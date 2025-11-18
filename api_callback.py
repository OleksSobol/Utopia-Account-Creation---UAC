import os
import re
import json
import logging
import urllib3
import requests
import subprocess

import powercode as PowerCode
import utopia as Utopia
import config
from failure_tracker import FailureTracker

from config import *
from dotenv import dotenv_values
from flask_mail import Mail, Message
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from functools import wraps
from datetime import timedelta, datetime


# Only disable specific warnings, not all
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
# Application logs go to app_main.log only
# uWSGI system logs go to api_callback.log (configured in .ini file)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE)
        # Removed StreamHandler() to prevent logs going to uWSGI
    ]
)
logger = logging.getLogger(__name__)

# Disable Flask/Werkzeug HTTP request logging to keep logs clean
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('werkzeug').disabled = True


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
        
        # Flask configuration
        self.app.config['MAIL_SERVER'] = MAIL_SERVER
        self.app.config['MAIL_PORT'] = MAIL_PORT
        self.app.config['SECRET_KEY'] = SECRET_KEY
        self.app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

        # Admin credentials
        self.admin_username = ADMIN_USER
        
        # Initialize Flask-Mail
        self.mail = Mail(self.app)
        
        # Initialize failure tracker
        self.failure_tracker = FailureTracker()
        
        # Setup all routes
        self.setup_routes()

    def _reload_config(self):
        """Update instance variables after config reload"""
        self.admin_username = config.ADMIN_USER

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
        # Root and catch-all routes
        self.app.route('/')(self.index)
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

        # Ticket template editor routes (protected)
        self.app.route('/admin/ticket-editor', methods=['GET'])(self.login_required(self.ticket_editor))
        self.app.route('/api/ticket-template/save', methods=['POST'])(self.login_required(self.save_ticket_template))
        self.app.route('/api/ticket-template/load/<template_id>', methods=['GET'])(self.login_required(self.load_ticket_template))
        self.app.route('/api/ticket-template/list', methods=['GET'])(self.login_required(self.list_ticket_templates))
        self.app.route('/api/ticket-template/delete/<template_id>', methods=['DELETE'])(self.login_required(self.delete_ticket_template))

        # Configuration management routes (protected)
        self.app.route('/admin/config', methods=['GET'])(self.login_required(self.admin_config))
        self.app.route('/api/config/update', methods=['POST'])(self.login_required(self.update_config))
        self.app.route('/api/config/restart', methods=['POST'])(self.login_required(self.restart_application))

        # Log viewer routes (protected)
        self.app.route('/admin/logs', methods=['GET'])(self.login_required(self.admin_logs))
        self.app.route('/api/logs/read', methods=['GET'])(self.login_required(self.read_logs))
        self.app.route('/api/logs/download', methods=['GET'])(self.login_required(self.download_logs))

        # API callback route (no auth required - for webhook)
        self.app.route('/api-callback', methods=['GET', 'POST'])(self.api_callback)
        
        # Error handlers
        self.app.errorhandler(404)(self.not_found)
        self.app.errorhandler(500)(self.server_error)

    def index(self):
        """Root route - redirect based on auth status"""
        if 'logged_in' in session:
            return redirect(url_for('admin_panel'))
        return redirect(url_for('login'))

    def catch_all(self, path):
        """Default route for unmatched paths"""
        if 'logged_in' in session:
            return redirect(url_for('admin_panel'))
        return redirect(url_for('login'))

    def not_found(self, e):
        """Handle 404 errors"""
        if 'logged_in' in session:
            return render_template('404.html'), 404
        return redirect(url_for('login'))

    def server_error(self, e):
        """Handle 500 errors"""
        logger.error(f"Server error: {str(e)}", exc_info=True)
        return render_template('500.html'), 500

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
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate credentials
        if username == self.admin_username and config.check_admin_password(password):
            session.permanent = True
            session['logged_in'] = True
            session['username'] = username
            logger.info(f"User '{username}' logged in successfully from IP: {request.remote_addr}")
            return jsonify({'success': True}), 200
        else:
            logger.warning(f"Failed login attempt for username: {username} from IP: {request.remote_addr}")
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

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
        return render_template('admin.html', session=session)
    
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
            
            logger.info(f"Admin lookup for orderref: {orderref} by user: {session.get('username')}")
            
            # Call the Utopia API function
            result = Utopia.getCustomerFromUtopia(orderref)
            
            # Check for error responses from Utopia API
            if isinstance(result, dict) and "error" in result:
                utopia_error_msg = result.get("error", "Unknown error")
                logger.error(f"Admin lookup failed for orderref: {orderref} - Utopia error: {utopia_error_msg}")
                return jsonify({
                    'success': False,
                    'error': f'Utopia API error: {utopia_error_msg}'
                }), 404
            
            # Legacy check for old "Error" string response
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
            
            logger.info(f"Admin creating customer for orderref: {orderref} by user: {session.get('username')}")
            logger.info(pretty_log_json(customer_data, "Customer data to create"))
            
            # Extract customer info for processing
            customer_to_powercode = {
                "firstname": customer_data.get("customer", {}).get("firstname", ""),
                "lastname": customer_data.get("customer", {}).get("lastname", ""),
                "email": customer_data.get("customer", {}).get("email", ""),
                "phone": customer_data.get("customer", {}).get("phone", ""),
                "address": customer_data.get("address", {}).get("address", ""),
                "city": customer_data.get("address", {}).get("city", ""),
                "apt": customer_data.get("address", {}).get("apt", ""),
                "state": customer_data.get("address", {}).get("state", ""),
                "zip": customer_data.get("address", {}).get("zip", ""),
                "siteid": customer_data.get("address", {}).get("siteid", ""),
                "orderref": orderref,
                "sp_terms_agree_date": customer_data.get('termsagreement', {}).get('sp_terms_agree_date', "")
            }
            
            # Use shared customer creation logic
            success, customer_id, error_message, ticket_id = self.process_customer_creation(
                customer_to_powercode, orderref, service_plan
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
                        customer_data=customer_to_powercode
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
        return render_template('failures.html', session=session)
    
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
            
            logger.info(f"Failures retrieved by {session.get('username')}: {len(failures)} total")
            
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
                logger.info(f"Admin {session.get('username')} marked failure as resolved: {orderref}")
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
                logger.info(f"Admin {session.get('username')} deleted failure record: {orderref}")
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
        

    def ticket_editor(self):
        """
        Renders the ticket template editor interface
        GET /admin/ticket-editor - Returns the HTML template for editing ticket templates
        """
        # Load the default new customer template
        template_path = os.path.join(TICKET_TEMPLATE_DIR, TICKET_TEMPLATE_FILE)
        template_content = ''

        try:
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            else:
                # Default content if file doesn't exist
                template_content = '''<p>Hello {customer_name},</p>
        <p>Thank you for your recent request for Internet Service with Global Net via Yellowstone Fiber.</p>
        <p>We have received notification of your request through the Yellowstone Fiber portal.</p>'''
        except Exception as e:
            logger.error(f"Error loading template: {str(e)}")
            template_content = '<p>Error loading template. Please try again.</p>'

        return render_template('ticket_editor.html', 
                            session=session, 
                            template_content=template_content)
    
    def save_ticket_template(self):
        """
        Save ticket template to file
        POST /api/ticket-template/save - Expects JSON with template data
        """
        try:
            data = request.get_json()
            template_id = data.get('template_id', 'new_customer')
            filename = data.get('filename', '')
            name = data.get('name', '')
            subject = data.get('subject', '')
            content = data.get('content', '')
            
            if not content:
                return jsonify({
                    'success': False,
                    'error': 'Template content is required'
                }), 400
            
            if not name:
                return jsonify({
                    'success': False,
                    'error': 'Template name is required'
                }), 400
            
            # Create ticket template directory if it doesn't exist
            templates_dir = TICKET_TEMPLATE_DIR
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
            
            # If no filename provided, generate from name
            if not filename:
                filename = name.lower().replace(' ', '_').replace('-', '_')
                # Remove special characters
                filename = ''.join(c for c in filename if c.isalnum() or c == '_')
                filename = f"{filename}.txt"
            
            file_path = os.path.join(templates_dir, filename)
            
            # Save the template
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Save metadata
            meta_path = os.path.join(templates_dir, f"{filename}.meta.json")
            metadata = {
                'name': name,
                'subject': subject,
                'last_modified': datetime.now().isoformat()
            }
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Ticket template saved: {filename} by {session.get('username')}")
            
            return jsonify({
                'success': True,
                'message': f'Template saved to {filename}',
                'filename': filename,
                'file_path': file_path
            }), 200
            
        except Exception as e:
            logger.error(f"Error saving ticket template: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500

    def load_ticket_template(self, template_id):
        """
        Load a ticket template from file
        GET /api/ticket-template/load/<template_id> - Returns template content
        """
        try:
            templates_dir = TICKET_TEMPLATE_DIR
            
            # Map template IDs to file names
            template_files = {
                'new_customer': TICKET_TEMPLATE_FILE,
                'welcome': 'welcome_email.txt',
                'installation': 'installation_info.txt',
                'billing': 'billing_info.txt'
            }
            
            filename = template_files.get(template_id, f"{template_id}.txt")
            file_path = os.path.join(templates_dir, filename)
            
            if not os.path.exists(file_path):
                return jsonify({
                    'success': False,
                    'error': 'Template not found'
                }), 404
            
            # Load template content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to load metadata
            meta_path = os.path.join(templates_dir, f"{filename}.meta.json")
            metadata = {}
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            return jsonify({
                'success': True,
                'template_id': template_id,
                'content': content,
                'name': metadata.get('name', ''),
                'subject': metadata.get('subject', ''),
                'last_modified': metadata.get('last_modified', '')
            }), 200
            
        except Exception as e:
            logger.error(f"Error loading ticket template: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500

    def list_ticket_templates(self):
        """
        List all available ticket templates
        GET /api/ticket-template/list - Returns list of templates
        """
        try:
            templates_dir = TICKET_TEMPLATE_DIR
            
            if not os.path.exists(templates_dir):
                return jsonify({
                    'success': True,
                    'templates': []
                }), 200
            
            templates = []
            
            # Get all .txt files in the directory
            for filename in os.listdir(templates_dir):
                if filename.endswith('.txt') and not filename.endswith('.meta.json'):
                    file_path = os.path.join(templates_dir, filename)
                    meta_path = file_path + '.meta.json'
                    
                    # Load metadata if exists
                    metadata = {}
                    if os.path.exists(meta_path):
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    
                    # Get file stats
                    file_stat = os.stat(file_path)
                    
                    templates.append({
                        'id': filename.replace('.txt', ''),
                        'name': metadata.get('name', filename),
                        'subject': metadata.get('subject', ''),
                        'filename': filename,
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })
            
            return jsonify({
                'success': True,
                'templates': templates
            }), 200
            
        except Exception as e:
            logger.error(f"Error listing ticket templates: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500
    
    def delete_ticket_template(self, template_id):
        """
        Delete a ticket template file
        DELETE /api/ticket-template/delete/<template_id> - Delete template and metadata
        """
        try:
            data = request.get_json() or {}
            filename = data.get('filename', '')
            
            if not filename:
                return jsonify({
                    'success': False,
                    'error': 'Filename is required'
                }), 400
            
            templates_dir = TICKET_TEMPLATE_DIR
            file_path = os.path.join(templates_dir, filename)
            meta_path = os.path.join(templates_dir, f"{filename}.meta.json")
            
            # Check if file exists
            if not os.path.exists(file_path):
                return jsonify({
                    'success': False,
                    'error': 'Template file not found'
                }), 404
            
            # Prevent deletion of active template - read directly from .env to ensure we have the latest value
            env_values = dotenv_values('.env')
            active_template = env_values.get('TICKET_TEMPLATE_FILE', TICKET_TEMPLATE_FILE)
            
            if filename == active_template:
                return jsonify({
                    'success': False,
                    'error': f'Cannot delete the active template "{filename}". Please change the active template in Configuration first.'
                }), 400
            
            # Delete template file
            os.remove(file_path)
            
            # Delete metadata file if exists
            if os.path.exists(meta_path):
                os.remove(meta_path)
            
            logger.info(f"Ticket template deleted: {filename} by {session.get('username')}")
            
            return jsonify({
                'success': True,
                'message': f'Template {filename} deleted successfully'
            }), 200
            
        except Exception as e:
            logger.error(f"Error deleting ticket template: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500
    
    def admin_config(self):
        """
        Renders the configuration management interface
        GET /admin/config - Returns the HTML template for viewing/editing config settings
        """
        config_data = config.get_config_dict()
        return render_template('config.html', config_data=config_data, session=session)
    
    def update_config(self):
        """
        Update configuration values and persist to .env file
        POST /api/config/update - Expects JSON with config updates
        """
        try:
            data = request.get_json()
            updates = data.get('updates', {})
            
            if not updates:
                return jsonify({'success': False, 'error': 'No updates provided'}), 400
            
            logger.info(f"Config update requested by {session.get('username')}: {list(updates.keys())}")
            
            # Update configuration file
            updated_count, changes = config.update_config_file(updates)
            
            # Check if admin password was actually changed (look for it in the changes list)
            password_changed = any('ADMIN_PASS' in change for change in changes)
            
            # Log individual changes
            for change in changes:
                logger.info(f"Updated {change}")
            
            # Reload configuration if changes were made
            if updated_count > 0:
                config.reload_config()
                self._reload_config()
                
                logger.info(f"Configuration updated successfully: {updated_count} values changed")
                logger.info("Configuration reloaded in memory")
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully updated {updated_count} configuration value(s)',
                    'updated_count': updated_count,
                    'changes': changes,
                    'restart_required': False,
                    'logout_required': password_changed  # Force logout if password changed
                }), 200
            else:
                logger.info("No configuration changes detected - all values are the same")
                return jsonify({
                    'success': True,
                    'message': 'No changes detected - all values are already up to date',
                    'updated_count': 0,
                    'restart_required': False
                }), 200
            
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def restart_application(self):
        """
        Restart the application service
        POST /api/config/restart - Triggers application restart via systemd
        """
        try:
            logger.info(f"Application restart requested by {session.get('username')}")
            
            # Try to restart via systemd service
            restart_command = "sudo systemctl restart api_callback.service"
            
            # Execute restart command in background
            result = subprocess.Popen(
                restart_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logger.info("Restart command executed")
            
            return jsonify({
                'success': True,
                'message': 'Application restart initiated. Page will reload automatically.'
            }), 200
            
        except Exception as e:
            logger.error(f"Error restarting application: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Failed to restart application: {str(e)}'
            }), 500
    
    def admin_logs(self):
        """
        Renders the log viewer interface
        GET /admin/logs - Returns the HTML template for viewing application logs
        """
        return render_template('logs.html', session=session, log_file=LOG_FILE)
    
    def read_logs(self):
        """
        Read log file and return content
        GET /api/logs/read?lines=100&search=error - Returns log content with optional filters
        """
        try:
            lines = int(request.args.get('lines', 100))
            search = request.args.get('search', '').lower()
            
            if not os.path.exists(LOG_FILE):
                return jsonify({
                    'success': True,
                    'content': 'Log file does not exist yet.',
                    'total_lines': 0
                }), 200
            
            # Read the file
            with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
            
            # Apply search filter if provided
            if search:
                filtered_lines = [line for line in all_lines if search in line.lower()]
            else:
                filtered_lines = all_lines
            
            # Get the last N lines
            tail_lines = filtered_lines[-lines:] if len(filtered_lines) > lines else filtered_lines
            
            content = ''.join(tail_lines)
            
            return jsonify({
                'success': True,
                'content': content,
                'total_lines': len(all_lines),
                'filtered_lines': len(filtered_lines),
                'displayed_lines': len(tail_lines)
            }), 200
            
        except Exception as e:
            logger.error(f"Error reading logs: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Failed to read logs: {str(e)}'
            }), 500
    
    def download_logs(self):
        """
        Download the entire log file
        GET /api/logs/download - Returns log file as download
        """
        try:
            if not os.path.exists(LOG_FILE):
                return jsonify({
                    'success': False,
                    'error': 'Log file does not exist'
                }), 404
            
            from flask import send_file
            return send_file(
                LOG_FILE,
                as_attachment=True,
                download_name=f"app_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                mimetype='text/plain'
            )
            
        except Exception as e:
            logger.error(f"Error downloading logs: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Failed to download logs: {str(e)}'
            }), 500
        
    def api_callback(self):
        """
        Handle incoming API callbacks from Utopia
        POST /api-callback - Expects JSON with event, orderref, and msg fields
        """
        # Check if request has JSON data
        if not request.is_json:
            logger.error("No JSON payload provided to API callback")
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        request_data = request.get_json()
        logger.info(f"Received API callback: {pretty_log_json(request_data)}")

        try:
            # Safely extract fields with .get()
            event = request_data.get('event')
            orderref = request_data.get('orderref')
            msg = request_data.get('msg')

            # Check if any required fields are missing or empty
            if not event or not orderref or not msg:
                logger.error(f"Missing required fields - event: {event}, orderref: {orderref}, msg: {msg}")
                raise ValueError("Missing required fields in JSON payload")

            logger.info(f"Processing webhook - event: {event}, orderref: {orderref}, msg: {msg}")
            
            self.handle_information_from_post(event, orderref, msg)
            response = {"data": "Information received"}
        except KeyError as e:
            logger.error(f"Missing key in JSON payload: {str(e)}")
            response = {"error": f"Missing required field: {str(e)}"}
            return jsonify(response), 400
        except Exception as e:
            error = f"Error processing API callback: {str(e)}"
            logger.error(error, exc_info=True)

            self.failure_tracker.record_failure(
                orderref=orderref,
                error_message=error,
                failure_type="powercode_api_error"
            )
            
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
                f"Test Received",
                f'Test webhook received for orderref: {orderref}\nEvent: {event}'
            )
        else:
            logger.warning(f"Unhandled event: {msg} for orderref: {orderref}")

    def handle_new_order(self, orderref):
        """
        Process a new order from Utopia:
        1. Fetch customer data from Utopia
        2. Search for existing customer in PowerCode
        3. Create new customer or send notification if exists
        """
        logger.info(f"Processing new order from webhook - orderref: {orderref}")

        customer_from_utopia = Utopia.getCustomerFromUtopia(orderref)
        
        logger.info(pretty_log_json(customer_from_utopia, "Response from Utopia"))

        # Check for error responses from Utopia API
        if isinstance(customer_from_utopia, dict) and "error" in customer_from_utopia:
            utopia_error_msg = customer_from_utopia.get("error", "Unknown error")
            error_msg = f"Utopia API error for order {orderref}: {utopia_error_msg}"
            logger.error(error_msg)
            
            # Record failure in tracking system with specific Utopia error
            self.failure_tracker.record_failure(
                orderref=orderref,
                error_message=f"Utopia API error: {utopia_error_msg}",
                failure_type="utopia_api_error"
            )
            
            # Only send email if it's not the "No valid records found for this ISP" error
            if "No valid records found for this ISP" not in utopia_error_msg:
                # Send email with specific Utopia error message
                self.send_email(
                    f"Utopia API Error - Order {orderref}",
                    f"Failed to fetch customer data from Utopia API\n\n"
                    f"Order Reference: {orderref}\n"
                    f"Error Message: {utopia_error_msg}\n\n",
                    orderref
                )
            else:
                logger.info(f"Skipping email notification for 'No valid records' error - orderref: {orderref}")
            
            return
        
        # Legacy check for old "Error" string response
        # if customer_from_utopia == "Error":
        #     error_msg = f"Failed to fetch customer from Utopia for order {orderref}"
        #     logger.error(error_msg)
            
        #     # Record failure in tracking system
        #     self.failure_tracker.record_failure(
        #         orderref=orderref,
        #         error_message="Utopia API returned error - invalid orderref or API issue",
        #         failure_type="utopia_api_error"
        #     )
            
        #     self.send_email(
        #         f"Failed to fetch customer data from Utopia - Order {orderref}",
        #         f"Utopia API returned error for orderref: {orderref}\n\nPlease verify the order reference is correct.",
        #         orderref
        #     )
        #     return

        # Transform Utopia data to PowerCode format
        customer_to_powercode = self.customer_to_pc(customer_from_utopia, orderref)
        
        # Extract customer info for duplicate check
        firstname = customer_from_utopia.get("customer", {}).get("firstname", "")
        lastname = customer_from_utopia.get("customer", {}).get("lastname", "")
        utopia_city = customer_from_utopia.get("address", {}).get("city", "")
        
        # Use shared duplicate checking logic
        logger.info("Checking for existing customer in PowerCode...")
        exists, matching_customer = self.check_customer_exists(firstname, lastname, utopia_city)

        if exists:
            # Customer exists - send notification
            pc_customer_id = matching_customer.get('CustomerID')
            logger.info(f"Customer already exists in PowerCode - Customer ID: {pc_customer_id}")
            formatted_customer_info = self.format_contact_info(customer_to_powercode)
            self.send_email(
                f"Duplicate Customer Detected - Order {orderref}",
                f'Customer already exists in PowerCode with ID: {pc_customer_id}\n\n'
                f'PowerCode URL: {PC_URL}:444/index.php?q&page=/customers/_view.php&customerid={pc_customer_id}\n\n'
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
        
        logger.info(f"Creating customer in PowerCode with data:\n{formatted_customer_to_powercode}")

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
                    f"Failed to create customer: Customer exists - Order {orderref}",
                    f'Customer already exists in PowerCode with ID: {customer_id}\n\n{formatted_customer_info}',
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
                    f"Failed to create customer in PowerCode - Order {orderref}",
                    f'Error: {error_message}\n\nCheck PowerCode logs for details.\n\n{formatted_customer_to_powercode}',
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
                error_msg = 'Failed to create customer in PowerCode. Check server logs for details.'
                logger.error(f"PowerCode returned -1 for customer creation. Orderref: {orderref}")
                return False, -1, error_msg, None
            
            # Add service plans
            plans_success, plan_responses = self.add_service_plans(customer_id, service_plan)
            if not plans_success:
                logger.warning(f"Some service plans failed to add for customer {customer_id}")
            
            # Create PowerCode Ticket
            ticket_description = self.get_ticket_description(customer_data)
            ticket_id = PowerCode.create_powercode_ticket(
                customer_id, 
                customer_data.get("firstname", ""),
                description=ticket_description 
            ) 

            # ticket_id = PowerCode.create_powercode_ticket(customer_id, customer_data.get("firstname", ""))
            logger.info(f'Support ticket created: {ticket_id} for customer {customer_id}')
            
            # Send Success Email
            formatted_customer_info = self.format_contact_info(customer_data)
            self.send_email(
                f"Customer Created Successfully - {customer_full_name} (PC#{customer_id})",
                f'Customer created in PowerCode!\n\n'
                f'PowerCode ID: {customer_id}\n'
                f'PowerCode URL: {PC_URL}:444/index.php?q&page=/customers/_view.php&customerid={customer_id}\n'
                f'Support Ticket: {ticket_id}\n'
                f'Service Plan: {service_plan}\n\n'
                f'{formatted_customer_info}',
                orderref
            )
            
            logger.info(f"Customer created successfully - PowerCode ID: {customer_id}, Utopia Site ID: {customer_data.get('siteid', 'N/A')}")
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
        
        logger.info(f"Searching for existing customer: {utopia_full_name} in {city}")
        customers_list = PowerCode.search_powercode_customers(utopia_full_name)["customers"]
        
        # Try to find a match by name and city
        for customer in customers_list:
            pc_full_name = customer.get("CompanyName", "")
            pc_city = customer.get("City", "")
            
            # Match by full name and city
            # TODO: if name is same but address are different go ahead and create account

            if pc_full_name == utopia_full_name and pc_city == city:
                logger.info(f"Found existing customer: {pc_full_name} (ID: {customer.get('CustomerID')})")
                return True, customer
        
        logger.info(f"No existing customer found for: {utopia_full_name}")
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
            logger.info(f"Service plan '{primary_plan}' (ID: {service_id_primary}) added to customer {customer_id}: {service_plan_respond_primary}")
            
            # Add Bond fee
            service_id_bond = additional_service_plan_mapping.get("Bond fee")
            if service_id_bond:
                service_plan_respond_bond = PowerCode.add_customer_service_plan(customer_id, service_id_bond)
                responses['bond'] = service_plan_respond_bond
                logger.info(f"Bond fee service (ID: {service_id_bond}) added to customer {customer_id}: {service_plan_respond_bond}")
            
            return True, responses
            
        except Exception as e:
            logger.error(f"Error adding service plans to customer {customer_id}: {str(e)}", exc_info=True)
            return False, responses
        

    def get_ticket_description(self, customer_data):
        """
        Load ticket description template and replace variables with customer data
        Returns formatted ticket description ready to send
        """
        try:
            # Load the template from file
            template_path = os.path.join(TICKET_TEMPLATE_DIR, TICKET_TEMPLATE_FILE)
            
            if not os.path.exists(template_path):
                logger.warning(f"Ticket template not found at {template_path}, using default")
                return "New customer setup required. Please contact customer."
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Replace variables with actual customer data
            description = template.replace('{customer_name}', 
                                        f"{customer_data.get('firstname', '')} {customer_data.get('lastname', '')}".strip())
            description = description.replace('{order_ref}', customer_data.get('orderref', 'N/A'))
            description = description.replace('{site_id}', customer_data.get('siteid', 'N/A'))
            description = description.replace('{email}', customer_data.get('email', 'N/A'))
            description = description.replace('{phone}', customer_data.get('phone', 'N/A'))
            description = description.replace('{address}', customer_data.get('address', 'N/A'))
            description = description.replace('{city}', customer_data.get('city', 'N/A'))
            description = description.replace('{state}', customer_data.get('state', 'N/A'))
            description = description.replace('{zip}', customer_data.get('zip', 'N/A'))
        
            return description
        
        except Exception as e:
            logger.error(f"Error loading ticket description: {str(e)}", exc_info=True)
            return "Error loading ticket template. Please contact support."

    
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
            logger.info(f"Email sent successfully - Subject: {msg_subject}")

            return "Email sent!"
        except Exception as e:
            logger.error(f"Error sending email '{msg_subject}': {str(e)}", exc_info=True)
            return f"Error sending email: {msg_subject}"
    

    def customer_to_pc(self, customer_from_utopia, orderref):
        """
        Transform Utopia customer data to PowerCode format
        """
        return {
            "firstname": customer_from_utopia.get("customer", {}).get("firstname", ""),
            "lastname": customer_from_utopia.get("customer", {}).get("lastname", ""),
            "email": customer_from_utopia.get("customer", {}).get("email", ""),
            "phone": customer_from_utopia.get("customer", {}).get("phone", ""),
            "address": customer_from_utopia.get("address", {}).get("address", ""),
            "city": customer_from_utopia.get("address", {}).get("city", ""),
            "apt": customer_from_utopia.get("address", {}).get("apt", ""),
            "state": customer_from_utopia.get("address", {}).get("state", ""),
            "zip": customer_from_utopia.get("address", {}).get("zip", ""),
            "siteid": customer_from_utopia.get("address", {}).get("siteid", ""),
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
            f"Apartment/Unit: {safe(contact_info.get('apt'))}\n"
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
        logger.info(f"Starting Utopia API Handler on {config.FLASK_HOST}:{config.FLASK_PORT}")
        self.app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=True)


if __name__ == "__main__":
    utopia_handler = UtopiaAPIHandler()
    utopia_handler.run()