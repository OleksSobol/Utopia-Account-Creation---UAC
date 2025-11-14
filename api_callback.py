import os
import re
import json
import logging
import urllib3
import requests

import powercode as PowerCode
import utopia as Utopia
import config
from failure_tracker import FailureTracker

from config import *
from flask_mail import Mail, Message
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from functools import wraps


# Only disable specific warnings, not all
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def pretty_log_json(data, title=""):
    """Pretty print JSON data for logging with proper indentation"""
    if isinstance(data, (dict, list)):
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        if title:
            return f"{title}:\n{formatted}"
        return formatted
    return str(data)


class UtopiaAPIHandler:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['MAIL_SERVER'] = MAIL_SERVER
        self.app.config['MAIL_PORT'] = MAIL_PORT
        self.app.config['SECRET_KEY'] = SECRET_KEY

        self.admin_username = ADMIN_USER
        self.admin_password = ADMIN_PASS
        
        self.mail = Mail(self.app)
        
        # Initialize failure tracker
        self.failure_tracker = FailureTracker()
        
        self.setup_routes()

    def login_required(self, f):
        """
        Decorator to protect routes that require authentication
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    
    def setup_routes(self):
        """
        Setup all Flask routes for the application
        """
        self.app.route('/', defaults={'path': ''})(self.catch_all)
        self.app.route('/<path:path>')(self.catch_all)
        
        # Authentication routes
        self.app.route('/login', methods=['GET', 'POST'])(self.login)
        self.app.route('/logout', methods=['POST'])(self.logout)
        
        # Admin panel routes (protected)
        self.app.route('/admin', methods=['GET'])(self.login_required(self.admin_panel))
        self.app.route('/api/lookup', methods=['POST'])(self.login_required(self.admin_lookup))
        self.app.route('/api/create-customer', methods=['POST'])(self.login_required(self.create_customer_from_admin))
        
        # Failure management routes (protected)
        self.app.route('/admin/failures', methods=['GET'])(self.login_required(self.admin_failures))
        self.app.route('/api/failures', methods=['GET'])(self.login_required(self.get_failures_api))
        self.app.route('/api/failures/<orderref>/resolve', methods=['POST'])(self.login_required(self.resolve_failure_api))
        self.app.route('/api/failures/<orderref>/delete', methods=['DELETE'])(self.login_required(self.delete_failure_api))
        self.app.route('/api/failures/stats', methods=['GET'])(self.login_required(self.get_failure_stats_api))

        # API callback route (no auth required)
        self.app.route('/api-callback', methods=['GET', 'POST'])(self.api_callback)

    def catch_all(self, path):
        """Default route for unmatched paths"""
        return 'This is only for Utopia API'

    def login(self):
        """
        Login page and authentication handler
        GET /login - Show login form
        POST /login - Authenticate user
        """
        if request.method == 'GET':
            # Check if already logged in
            if 'logged_in' in session:
                return redirect(url_for('admin_panel'))
            return render_template('login.html')
        
        # Handle POST request (login form submission)
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Validate credentials
        if username == self.admin_username and password == self.admin_password:
            session['logged_in'] = True
            session['username'] = username
            logger.info(f"User '{username}' logged in successfully")
            return jsonify({'success': True}), 200
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

    def logout(self):
        """
        Logout handler
        POST /logout - Clear session and logout user
        """
        username = session.get('username', 'Unknown')
        session.clear()
        logger.info(f"User '{username}' logged out")
        return jsonify({'success': True}), 200

    def admin_panel(self):
        """
        Renders the admin lookup interface
        GET /admin - Returns the HTML template
        """
        return render_template('admin.html')
    
    def admin_lookup(self):
        """
        Admin API endpoint for looking up customer data from Utopia
        POST /api/lookup - Expects JSON with 'orderref' field
        Returns customer data or error message
        """
        try:
            # Get orderref from request body
            data = request.get_json()
            orderref = data.get('orderref', '').strip()
            
            # Validate orderref is provided
            if not orderref:
                logger.warning("Admin lookup attempted without orderref")
                return jsonify({
                    'success': False,
                    'error': 'Order reference is required'
                }), 400
            
            logger.info(f"Admin lookup for orderref: {orderref}")
            
            # Call the Utopia API function
            result = Utopia.getCustomerFromUtopia(orderref)
            
            # Check if result is an error string
            if result == "Error" or isinstance(result, str):
                logger.error(f"Admin lookup failed for orderref: {orderref}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid orderref or not found: {orderref}'
                }), 404
            
            # Log successful lookup
            logger.info(f"Admin lookup successful for orderref: {orderref}")
            logger.debug(pretty_log_json(result, f"Admin lookup result for {orderref}"))
            
            # Return successful response with customer data
            return jsonify({
                'success': True,
                'data': result,
                'orderref': orderref
            }), 200
            
        except Exception as e:
            # Catch any unexpected errors and return detailed error message
            logger.error(f"Error in admin_lookup: {str(e)}", exc_info=True)
            
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500
        
    def create_customer_from_admin(self):
        """
        Create customer in PowerCode from admin panel
        POST /api/create-customer - Expects JSON with orderref and customer data
        """
        try:
            # Get data from request body
            data = request.get_json()
            orderref = data.get('orderref', '').strip()
            customer_data = data.get('customer_data', {})
            service_plan = data.get('service_plan', '250 Mbps')  # Get service plan from frontend
            
            # Validate inputs
            if not orderref or not customer_data:
                logger.warning("Admin create customer attempted without required data")
                return jsonify({
                    'success': False,
                    'error': 'Order reference and customer data are required'
                }), 400
            
            logger.info(f"Admin creating customer for orderref: {orderref}")
            logger.info(pretty_log_json(customer_data, "Customer data to create"))
            
            # Use shared customer creation logic
            success, customer_id, error_message, ticket_id = self.process_customer_creation(
                customer_data, orderref, service_plan
            )
            
            if not success:
                if customer_id != -1:  # Customer exists
                    return jsonify({
                        'success': False,
                        'error': error_message,
                        'customer_id': customer_id
                    }), 409
                else:  # Creation failed - record in failure tracker
                    self.failure_tracker.record_failure(
                        orderref=orderref,
                        error_message=error_message,
                        failure_type="admin_creation_failed",
                        customer_data=customer_data
                    )
                    
                    return jsonify({
                        'success': False,
                        'error': error_message
                    }), 500
            
            # Return success response
            return jsonify({
                'success': True,
                'customer_id': customer_id,
                'message': f'Customer created successfully in PowerCode with ID: {customer_id}',
                'ticket': ticket_id,
                'service_plan': service_plan
            }), 200
            
        except Exception as e:
            logger.error(f"Error in create_customer_from_admin: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500
        
    def admin_failures(self):
        """
        Renders the failure management interface
        GET /admin/failures - Returns the HTML template for managing failures
        """
        return render_template('failures.html')
    
    def get_failures_api(self):
        """
        API endpoint to get failure data
        GET /api/failures - Returns JSON with failure list and statistics
        """
        try:
            include_resolved = request.args.get('include_resolved', 'false').lower() == 'true'
            
            # Get failure list and statistics
            failures = self.failure_tracker.get_failure_list(include_resolved=include_resolved)
            stats = self.failure_tracker.get_failure_stats()
            
            return jsonify({
                'success': True,
                'failures': failures,
                'stats': stats,
                'total': len(failures)
            }), 200
            
        except Exception as e:
            logger.error(f"Error in get_failures_api: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500
    
    def resolve_failure_api(self, orderref):
        """
        API endpoint to mark a failure as resolved
        POST /api/failures/<orderref>/resolve - Mark failure as resolved
        """
        try:
            data = request.get_json() or {}
            resolution_note = data.get('note', '')
            
            success = self.failure_tracker.mark_resolved(orderref, resolution_note)
            
            if success:
                logger.info(f"Admin marked failure as resolved: {orderref}")
                return jsonify({
                    'success': True,
                    'message': f'Failure {orderref} marked as resolved'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Failure {orderref} not found'
                }), 404
                
        except Exception as e:
            logger.error(f"Error in resolve_failure_api: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500
    
    def delete_failure_api(self, orderref):
        """
        API endpoint to delete a failure record
        DELETE /api/failures/<orderref>/delete - Remove failure record
        """
        try:
            success = self.failure_tracker.remove_failure(orderref)
            
            if success:
                logger.info(f"Admin deleted failure record: {orderref}")
                return jsonify({
                    'success': True,
                    'message': f'Failure {orderref} deleted'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Failure {orderref} not found'
                }), 404
                
        except Exception as e:
            logger.error(f"Error in delete_failure_api: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500
    
    def get_failure_stats_api(self):
        """
        API endpoint to get failure statistics
        GET /api/failures/stats - Returns JSON with detailed failure statistics
        """
        try:
            stats = self.failure_tracker.get_failure_stats()
            
            # Get additional details
            unresolved_failures = self.failure_tracker.get_failure_list(include_resolved=False)
            recent_failures = unresolved_failures[:5]  # Last 5 unresolved
            
            return jsonify({
                'success': True,
                'stats': stats,
                'recent_unresolved': recent_failures
            }), 200
            
        except Exception as e:
            logger.error(f"Error in get_failure_stats_api: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500
        
    def api_callback(self):
        """
        Handle incoming API callbacks from Utopia
        POST /api-callback - Expects JSON with event, orderref, and msg fields
        """
    # Check if request has JSON data
        if not request.is_json:
            logger.error("No JSON payload provided")
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        request_data = request.get_json()
        logger.info(f"Received request data: {request_data}")  # Log the full payload

        try:
            # Safely extract fields with .get()
            event = request_data.get('event')
            orderref = request_data.get('orderref')
            msg = request_data.get('msg')

            # Check if any required fields are missing or empty
            if not event or not orderref or not msg:
                logger.error(f"Missing required fields - event: {event}, orderref: {orderref}, msg: {msg}")
                raise ValueError("Missing required fields in JSON payload")

            logger.info(f"Processing - event: {event}, orderref: {orderref}, msg: {msg}")
            
            self.handle_information_from_post(event, orderref, msg)
            response = {"data": "Information received"}
        except KeyError as e:
            logger.error(f"Missing key in JSON payload: {str(e)}")
            response = {"error": f"Missing required field: {str(e)}"}
            return jsonify(response), 400
        except Exception as e:
            logger.error(f"Error processing API callback: {str(e)}", exc_info=True)  # exc_info adds stack trace
            response = {"error": "Error processing API callback"}
            return jsonify(response), 400

        return jsonify(response), 200

    def handle_information_from_post(self, event, orderref, msg):
        """
        Route different message types to appropriate handlers
        """
        if msg == "Project New Order":
            self.handle_new_order(orderref)
        elif msg == "Test":
            self.send_email(
                f"This is just a test",
                f'Please ignore it!'
            )

        else:
            logger.warning("No methods to handle that yet!")

    def handle_new_order(self, orderref):
        """
        Process a new order from Utopia:
        1. Fetch customer data from Utopia
        2. Search for existing customer in PowerCode
        3. Create new customer or send notification if exists
        """
        logger.info(f"Searching for customer - {orderref}")

        customer_from_utopia = Utopia.getCustomerFromUtopia(orderref)
        
        logger.info(pretty_log_json(customer_from_utopia, "Response from Utopia"))

        # Check for error FIRST before trying to access dict methods
        if customer_from_utopia == "Error":
            error_msg = f"Failed to fetch customer from Utopia for order {orderref}"
            logger.error(error_msg)
            
            # Record failure in tracking system
            self.failure_tracker.record_failure(
                orderref=orderref,
                error_message="Utopia API returned error - invalid orderref or API issue",
                failure_type="utopia_api_error"
            )
            
            self.send_email(
                f"Failed to fetch customer data from Utopia - Order {orderref}",
                f"Utopia API returned error for orderref: {orderref}",
                orderref
            )
            return

        # Transform Utopia data to PowerCode format
        customer_to_powercode = self.customer_to_pc(customer_from_utopia, orderref)
        
        # Extract customer info for duplicate check (using billing address for webhook flow)
        # utopia_name = customer_from_utopia.get('billingaddress', {}).get('name', '')
        utopia_city = customer_from_utopia.get('billingaddress', {}).get('city', '')
        
        firstname = customer_from_utopia.get("customer", {}).get("firstname", "")
        lastname = customer_from_utopia.get("customer", {}).get("lastname", "")
        
        # Use shared duplicate checking logic
        logger.info("Searching customer in Powercode...")
        exists, matching_customer = self.check_customer_exists(firstname, lastname, utopia_city)

        if exists:
            # Customer exists - send notification
            logger.info(f"Customer exists, doing nothing... Customer ID: {matching_customer.get('CustomerID')}")
            formatted_customer_info = self.format_contact_info(customer_to_powercode)
            self.send_email(
                f"Failed to create customer: Customer exist, Powercode ID {matching_customer['CustomerID']}",
                f'{formatted_customer_info}',
                orderref,
            )
        else:
            # Create new customer using shared logic
            self.handle_webhook_customer_creation(customer_from_utopia, orderref)

    def handle_webhook_customer_creation(self, customer_from_utopia, orderref):
        """
        Handle customer creation from webhook (Utopia API data)
        Transforms Utopia data and processes customer creation workflow
        """
        # Transform Utopia data to PowerCode format
        customer_to_powercode = self.customer_to_pc(customer_from_utopia, orderref)
        formatted_customer_to_powercode = self.format_contact_info(customer_to_powercode)
        
        logger.info(f"Creating customer in Powercode with next data: \n{formatted_customer_to_powercode}")

        # Determine service plan from Utopia order items
        utopia_customers_service_plan = (
            customer_from_utopia.get("orderitems", [{}])[0].get("description", "250 Mbps")
            if customer_from_utopia.get("orderitems")
            else "250 Mbps"
        )

        # Use shared customer creation logic
        success, customer_id, error_message, ticket_id = self.process_customer_creation(
            customer_to_powercode, orderref, utopia_customers_service_plan
        )

        if not success:
            if customer_id != -1:
                # Customer exists (shouldn't happen here, but handle it)
                formatted_customer_info = self.format_contact_info(customer_to_powercode)
                self.send_email(
                    f"Failed to create customer: Customer exists, Powercode ID {customer_id}",
                    f'{formatted_customer_info}',
                    orderref,
                )
            else:
                # Creation failed - record in failure tracker
                self.failure_tracker.record_failure(
                    orderref=orderref,
                    error_message=error_message,
                    failure_type="powercode_creation_failed",
                    customer_data=customer_to_powercode
                )
                
                self.send_email(
                    f"Failed to create customer: {customer_from_utopia}",
                    f'Check Powercode Logs, because API returns -1 when something wrong. \n{formatted_customer_to_powercode}',
                    orderref
                )
        else:
            # Success is already logged and email sent by process_customer_creation
            logger.info(f"Webhook customer creation completed successfully for orderref: {orderref}")


    def process_customer_creation(self, customer_data, orderref, service_plan):
        """
        Core customer creation workflow
        Handles: duplicate check → create account → add plans → create ticket → send email
        Returns: (success, customer_id, error_message, ticket_id)
        """
        try:
            # Extract customer info for duplicate check
            firstname = customer_data.get("firstname", "")
            lastname = customer_data.get("lastname", "")
            city = customer_data.get("city", "")
            customer_full_name = f"{firstname} {lastname}".strip()
            
            # Check if customer already exists
            exists, matching_customer = self.check_customer_exists(firstname, lastname, city)
            if exists:
                error_msg = f'Customer already exists in PowerCode with ID: {matching_customer.get("CustomerID")}'
                logger.warning(error_msg)
                return False, matching_customer.get('CustomerID'), error_msg, None
            
            # Create customer in PowerCode
            logger.info(f"Creating PowerCode account for orderref={orderref}")
            customer_id = PowerCode.create_powercode_account(customer_data)
            
            if customer_id == -1:
                error_msg = 'Failed to create customer in PowerCode. Check server logs.'
                logger.error(f"Failed to create customer in PowerCode for orderref: {orderref}")
                return False, -1, error_msg, None
            
            # Add service plans
            plans_success, plan_responses = self.add_service_plans(customer_id, service_plan)
            if not plans_success:
                logger.warning(f"Some service plans failed to add for customer {customer_id}")
            
            # Create PowerCode Ticket
            ticket_id = PowerCode.create_powercode_ticket(customer_id, customer_data.get("firstname", ""))
            logger.info(f'Ticket: {ticket_id}, created in PowerCode')
            
            # Send Email
            formatted_customer_info = self.format_contact_info(customer_data)
            self.send_email(
                f"Customer created - {customer_full_name} PC#{customer_id}",
                f'Powercode id: {PC_URL}:444/index.php?q&page=/customers/_view.php&customerid={customer_id}\n\n{formatted_customer_info}',
                orderref
            )
            
            logger.info(f"Customer created successfully - Powercode: {customer_id}, Utopia siteID: {customer_data.get('siteid', 'N/A')}")
            return True, customer_id, None, ticket_id
            
        except Exception as e:
            error_msg = f'Error creating customer: {str(e)}'
            logger.error(f"Error in process_customer_creation: {str(e)}", exc_info=True)
            return False, -1, error_msg, None


    def check_customer_exists(self, firstname, lastname, city):
        """
        Check if customer already exists in PowerCode
        Returns: (exists, matching_customer_or_none)
        """
        utopia_full_name = f"{firstname} {lastname}".strip()
        
        logger.info("Checking if customer exists in PowerCode...")
        customers_list = PowerCode.search_powercode_customers(utopia_full_name)["customers"]
        
        # Try to find a match by name and city
        for customer in customers_list:
            pc_full_name = customer.get("CompanyName", "")
            pc_city = customer.get("City", "")
            # Match by full name and city
            if pc_full_name == utopia_full_name and pc_city == city:
                return True, customer
        
        return False, None

    def add_service_plans(self, customer_id, primary_plan):
        """
        Add service plans to customer (primary + bond fee)
        Returns: (success, responses)
        """
        # Service plan mapping
        service_plan_mapping = {
            "1 Gbps": SERVICE_PLAN_1GBPS_ID,
            "250 Mbps": SERVICE_PLAN_250MBPS_ID,
        }
        
        additional_service_plan_mapping = {
            "Bond fee": SERVICE_PLAN_BOND_FEE_ID,
        }
        
        responses = {}
        
        try:
            # Add primary service plan
            service_id_primary = service_plan_mapping.get(primary_plan, SERVICE_PLAN_250MBPS_ID)
            service_plan_respond_primary = PowerCode.add_customer_service_plan(customer_id, service_id_primary)
            responses['primary'] = service_plan_respond_primary
            logger.info(f"Service plan '{primary_plan}' added: {service_plan_respond_primary}")
            
            # Add Bond fee
            service_id_bond = additional_service_plan_mapping.get("Bond fee")
            if service_id_bond:
                service_plan_respond_bond = PowerCode.add_customer_service_plan(customer_id, service_id_bond)
                responses['bond'] = service_plan_respond_bond
                logger.info(f"Bond fee service added: {service_plan_respond_bond}")
            
            return True, responses
            
        except Exception as e:
            logger.error(f"Error adding service plans: {str(e)}")
            return False, responses

    
    def send_email(self, msg_subject, msg_body, order_ref=None):
        """
        Send email notification using Flask-Mail
        """
        try:
            msg = Message(
                subject=msg_subject,
                sender=EMAIL_SENDER,
                recipients=EMAIL_RECIPIENTS,
                body=msg_body
            )
            
            self.mail.send(msg)
            logger.info(f"Email sent successfully: {msg_subject}")

            return "Email sent!"
        except Exception as e:
            logger.error(f"Error sending email: {msg_subject}. Error: {str(e)}")
            return f"Error sending email: {msg_subject}"
    

    def customer_to_pc(self, customer_from_utopia, orderref):
        """
        Transform Utopia customer data to PowerCode format
        """
        return {
            "firstname": customer_from_utopia["customer"].get("firstname", ""),
            "lastname": customer_from_utopia["customer"].get("lastname", ""),
            "email": customer_from_utopia["customer"].get("email", ""),
            "phone": customer_from_utopia["customer"].get("phone", ""),
            "address": customer_from_utopia["address"].get("address", ""),
            "city": customer_from_utopia["address"].get("city", ""),
            "apt": customer_from_utopia["address"].get("city", ""),
            "state": customer_from_utopia["address"].get("state", ""),
            "zip": customer_from_utopia["address"].get("zip", ""),
            "siteid": customer_from_utopia["address"].get("siteid", ""),
            "orderref": orderref,
            "sp_terms_agree_date": customer_from_utopia.get('termsagreement', {}).get('sp_terms_agree_date', "")
        }
    
    def format_contact_info(self, contact_info):
        """
        Format customer contact information for email/logging
        """
        def safe(val):
            return val if val not in [None, "None", ""] else "N/A"

        formatted_info = (
            f"Name: {safe(contact_info.get('firstname'))} {safe(contact_info.get('lastname'))}\n"
            f"Email: {safe(contact_info.get('email'))}\n"
            f"Phone: {safe(contact_info.get('phone'))}\n"
            f"Address: {safe(contact_info.get('address'))}\n"
            f"City: {safe(contact_info.get('city'))}\n"
            f"State: {safe(contact_info.get('state'))}\n"
            f"ZIP: {safe(contact_info.get('zip'))}\n"
            f"Site ID: {safe(contact_info.get('siteid'))}\n"
            f"Order Ref: {safe(contact_info.get('orderref'))}\n"
            f"Agreed to Service Provider Terms: {safe(contact_info.get('sp_terms_agree_date'))}"
        )

        return formatted_info



    def run(self):
        """
        Start the Flask application
        Uses configured host/port from config.py
        """
        self.app.run(host=config.FLASK_HOST, port=config.FLASK_PORT)


if __name__ == "__main__":
    utopia_handler = UtopiaAPIHandler()
    utopia_handler.run()
