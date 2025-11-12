import json
import logging
import os
import requests
import urllib3
from flask import Flask, request, jsonify
from flask_mail import Mail, Message

import powercode as PowerCode
import utopia as Utopia
import config

from static_vars import *

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

# Only disable specific warnings, not all
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UtopiaAPIHandler:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['MAIL_SERVER'] = MAIL_SERVER
        self.app.config['MAIL_PORT'] = MAIL_PORT
        self.mail = Mail(self.app)
        self.setup_routes()

    def setup_routes(self):
        self.app.route('/', defaults={'path': ''})(self.catch_all)
        self.app.route('/<path:path>')(self.catch_all)
        self.app.route('/api-callback', methods=['GET', 'POST'])(self.api_callback)

    def catch_all(self, path):
        return 'This is only for Utopia API'

    def api_callback(self):
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
        # search cust in Utopia/Powercode and create customer in Powercode
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
        logger.info(f"Searching for customer - {orderref}")

        customer_from_utopia = Utopia.getCustomerFromUtopia(orderref)
        
        logger.info(f"Response from Utopia: {customer_from_utopia}")

        # Check for error FIRST before trying to access dict methods
        if customer_from_utopia == "Error":
            logger.error(f"Failed to fetch customer from Utopia for order {orderref}")
            self.send_email(
                f"Failed to fetch customer data from Utopia - Order {orderref}",
                f"Utopia API returned error for orderref: {orderref}",
                orderref
            )
            return

        # NOW it's safe to extract Utopia customer info
        utopia_name = customer_from_utopia.get('billingaddress', {}).get('name', '')
        utopia_city = customer_from_utopia.get('billingaddress', {}).get('city', '')

        logger.info("Searching in PC...")

        firstname = customer_from_utopia.get("customer", {}).get("firstname", "")
        lastname = customer_from_utopia.get("customer", {}).get("lastname", "")
        customer_first_last_name = f"{firstname} {lastname}".strip()

        customers_list = PowerCode.search_powercode_customers(customer_first_last_name)["customers"]
        logger.info(customers_list)

        # Try to find a match by comparing names
        matching_customer = None

        for customer in customers_list:
            pc_name = customer.get("CompanyName", "")
            pc_city = customer.get("City", "")
            if pc_name == utopia_name and pc_city == utopia_city:
                matching_customer = customer
                break

        # check by name if customer exist in Powercode.
        if matching_customer:
            logger.info(f"Customer exist, doing nothing... {customers_list}")
            customer_to_powercode = self.customer_to_pc(customer_from_utopia, orderref)
            formatted_customer_to_powercode = self.format_contact_info(customer_to_powercode)

            self.send_email(
                f"Failed to create customer: Customer exist, Powercode ID {customers_list[0]['CustomerID']}",
                f'{formatted_customer_to_powercode}',
                orderref,
            )
        else:
            self.create_new_customer(customer_from_utopia, orderref)

    def create_new_customer(self, customer_from_utopia, orderref):
        customer_to_powercode = self.customer_to_pc(customer_from_utopia, orderref)
        formatted_customer_to_powercode = self.format_contact_info(customer_to_powercode)
        
        logger.warning(f"Creating customer in PC with data: \n{formatted_customer_to_powercode}")

        logger.info("Utopia:", customer_from_utopia)
        customer_first_last_name = (
                    customer_from_utopia["customer"]["firstname"] + " " + customer_from_utopia["customer"]["lastname"])

        logger.info(f"Creating Powercode account for orderref={orderref}")
        customer_id = PowerCode.create_powercode_account(
            PC_URL,
            config.PC_API_KEY,
            customer_to_powercode,
            customer_portal_password=CUSTOMER_PORTAL_PASSWORD
        )
        logger.info(customer_id)

        if customer_id == -1:
            self.send_email(
                f"Failed to create customer: {customer_from_utopia}",
                f'Check Powercode Logs, because API returns -1 when something wrong. \n{formatted_customer_to_powercode}',
                orderref
            )
        else:
            # ADD SERVICE PLAN
            # Determine the service ID before the function call
            utopia_customers_service_plan = customer_from_utopia["orderitems"][0]["description"]

            # Create a mapping for flexibility, easily add more plans in the future
            # Service plan mapping for Utopia plans
            service_plan_mapping = {
                "1 Gbps": 164,
                "250 Mbps": 163,
            }

            # Additional plans (manually added or other criteria-based)
            additional_service_plan_mapping = {
                "Bond fee": 172,
            }

            # Get Utopia service plan
            utopia_customes_service_plan = customer_from_utopia["orderitems"][0][
                "description"] if "orderitems" in customer_from_utopia else None

            # Get the service ID for the Utopia plan (with a default if not found)
            service_id_utopia = service_plan_mapping.get(utopia_customes_service_plan,
                                                         163)  # Default to 163 if not found

            # Add Utopia service plan
            service_plan_respond_utopia = PowerCode.add_customer_service_plan(
                customer_id,
                service_id_utopia
            )

            logger.info(f"Utopia service added: {service_plan_respond_utopia}")

            # Step 3: Add an additional plan manually
            additional_plan = "Bond fee" 
            service_id_additional = additional_service_plan_mapping.get(additional_plan, None)

            if service_id_additional:
                service_plan_respond_additional = PowerCode.add_customer_service_plan(
                    customer_id,
                    service_id_additional
                )
                logger.info(f"Additional service added: {service_plan_respond_additional}")

            # Create PowerCode Ticket & log response to a variable
            ticket_creation_response_pc = PowerCode.create_powercode_ticket(customer_id, customer_to_powercode["firstname"])
            
            # Log entry for PowerCode ticket creation
            logger.info(f'Ticket: {ticket_creation_response_pc}, created in PowerCode')
            

            # Send Email
            self.send_email(
                f"Customer created - {customer_first_last_name} PC#{customer_id}",
                f'Powercode id: https://management.theglobal.net:444/index.php?q&page=/customers/_view.php&customerid={customer_id} \n{formatted_customer_to_powercode}',
                orderref
            )

            logger.info(
                f"Customer created - Powercode: {customer_id}, Utopia siteID: {customer_from_utopia['address']['siteid']}")


    def send_email(self, msg_subject, msg_body, order_ref=None):
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
        self.app.run(host='0.0.0.0', port=5050)


if __name__ == "__main__":
    utopia_handler = UtopiaAPIHandler()
    utopia_handler.run()
