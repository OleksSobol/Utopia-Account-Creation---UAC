import json
import logging
import os
import requests
import urllib3
from flask import Flask, request
from flask_mail import Mail, Message

import powercode as PowerCode
import utopia as Utopia
import static_vars
import config

# Disable warnings
urllib3.disable_warnings()

# Constants
MAIL_SERVER = 'theglobal-net.mail.protection.outlook.com'
MAIL_PORT = 25
EMAIL_SENDER = 'no-reply@theglobal.net'
EMAIL_RECIPIENTS = ['osobol@theglobal.net', 'amolenda@theglobal.net', 'mbuonocore@theglobal.net']
LOG_FILE = 'api_class.log'


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
        request_data = request.get_json()
        logging.basicConfig(filename=LOG_FILE, format='%(asctime)s - %(message)s', level=logging.INFO)
        logging.info(request_data)

        try:
            event = request_data['event']
            orderref = request_data['orderref']
            msg = request_data["msg"]
            self.handle_information_from_post(event, orderref, msg)
            response = {"data": "Information received"}
        except Exception as e:
            logging.error(f"Error processing API callback: {str(e)}")
            response = {"error": "Error processing API callback"}

        return response

    def handle_information_from_post(self, event, orderref, msg):
        # search cust in Utopia/Powercode and create customer in Powercode
        if msg == "Project New Order":
            self.handle_new_order(orderref)
        else:
            logging.warning("No methods to handle that yet!")

    def handle_new_order(self, orderref):
        logging.info(f"Searching for customer - {orderref}")
        customer_from_utopia = Utopia.getCustomerFromUtopia(orderref)
        logging.info(f"Response from Utopia: {customer_from_utopia}")

        if customer_from_utopia != "Error":
            logging.info("Search in PC")
            customer_first_last_name = (customer_from_utopia["customer"]["firstname"] + " " + customer_from_utopia["customer"]["lastname"])
            customers_list = PowerCode.search_powercode_customers(customer_first_last_name)["customers"]
            logging.info(customers_list)

            if customers_list:
                logging.info(f"Customer exist, doing nothing... {customers_list}")

                customer_to_powercode = self.format_contact_info(self.customer_to_pc(customer_from_utopia, orderref))
                self.send_email(
                    f"Failed to create customer: Customer exist, Powercode ID {customers_list[0]['CustomerID']}",
                    f'{customer_to_powercode}',
                    orderref,
                )
            else:
                self.create_new_customer(customer_from_utopia, orderref)
        else:
            logging.info("No customer found")

    def create_new_customer(self, customer_from_utopia, orderref):
        logging.warning(f"Creating customer in PC: {customer_from_utopia}")
        customer_to_powercode = self.customer_to_pc(customer_from_utopia, orderref)
        formatted_customer_to_powercode = self.format_contact_info(self.customer_to_pc(customer_from_utopia, orderref))
        logging.info("Utopia:", customer_from_utopia)

        customer_id = PowerCode.create_powercode_account(
            static_vars.PC_URL,
            config.PC_API_KEY,
            customer_to_powercode,
            customer_portal_password="WelcomeToGlobalNet"
        )
        logging.info(customer_id)

        if customer_id == -1:
            self.send_email(
                f"Failed to create customer: {customer_from_utopia}",
                f'Check Powercode Logs. \n{formatted_customer_to_powercode}',
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

            logging.info(f"Utopia service added: {service_plan_respond_utopia}")

            # Step 3: Add an additional plan manually (if needed)
            additional_plan = "Bond fee"  # Example, this can be dynamic based on the customer or logic
            service_id_additional = additional_service_plan_mapping.get(additional_plan, None)

            if service_id_additional:
                service_plan_respond_additional = PowerCode.add_customer_service_plan(
                    customer_id,
                    service_id_additional
                )
                logging.info(f"Additional service added: {service_plan_respond_additional}")

            # Create ticket
            PowerCode.create_powercode_ticket(customer_id, customer_to_powercode["firstname"])

            # Send Email
            self.send_email(
                f"Customer created - Powercode#{customer_id}",
                f'Powercode id: https://management.theglobal.net:444/index.php?q&page=/customers/_view.php&customerid={customer_id} \n{formatted_customer_to_powercode}',
                orderref
            )

            logging.info(
                f"Customer created - Powercode: {customer_id}, Utopia siteID: {customer_from_utopia['address']['siteid']}")


    def send_email(self, msg_subject, msg_body, order_ref=None):
        try:
            msg = Message(
                subject=msg_subject,
                sender=EMAIL_SENDER,
                recipients=EMAIL_RECIPIENTS,
                body=msg_body
            )

            attachment_path = None
            if order_ref:
                attachment_path = self.attach_contract_to_email(order_ref)
                if attachment_path:
                    with self.app.open_resource(attachment_path) as attachment:
                        msg.attach(
                            f"{order_ref}.pdf",
                            "application/pdf",
                            attachment.read())
                        logging.info(f"Attached PDF contract for: {order_ref}")
            self.mail.send(msg)
            logging.info(f"Email sent successfully: {msg_subject}")

            # Delete PDF contract after email sent
            if attachment_path:
                os.remove(attachment_path)
                logging.info(f"Delete PDF contract: {attachment_path}")

            return "Email sent!"
        except Exception as e:
            logging.error(f"Error sending email: {msg_subject}. Error: {str(e)}")
            return f"Error sending email: {msg_subject}"


    def attach_contract_to_email(self, order_ref):
        pdf_content = Utopia.download_contract_pdf(order_ref)
        if pdf_content:
            os.makedirs("contracts", exist_ok=True)
            file_path = f"contracts/{order_ref}.pdf"
            with open(file_path, "wb") as f:
                f.write(pdf_content)
                logging.info(f"PDF file downloaded successfully for: {order_ref}")
                return file_path
        else:
            logging.error("Failed to download PDF file.")
            return None


    def format_contact_info(self, contact_info):
        formatted_info = f"Name: {contact_info['firstname']} {contact_info['lastname']}\n"
        formatted_info += f"Email: {contact_info['email']}\n"
        formatted_info += f"Phone: {contact_info['phone']}\n"
        formatted_info += f"Address: {contact_info['address']}\n"
        formatted_info += f"City: {contact_info['city']}\n"
        formatted_info += f"State: {contact_info['state']}\n"
        formatted_info += f"ZIP: {contact_info['zip']}\n"
        formatted_info += f"Site ID: {contact_info['siteid']}\n"
        formatted_info += f"Order Ref: {contact_info['orderref']}"
        return formatted_info

    def customer_to_pc(self, customer_from_utopia, orderref):
        return {
            "firstname": customer_from_utopia["customer"]["firstname"],
            "lastname": customer_from_utopia["customer"]["lastname"],
            "email": customer_from_utopia["customer"]["email"],
            "phone": customer_from_utopia["customer"]["phone"],
            "address": customer_from_utopia["address"]["address"],
            "city": customer_from_utopia["address"]["city"],
            "apt": customer_from_utopia["address"]["city"],
            "state": customer_from_utopia["address"]["state"],
            "zip": customer_from_utopia["address"]["zip"],
            "siteid": customer_from_utopia["address"]["siteid"],
            "orderref": orderref,
        }

    def run(self):
        self.app.run(host='0.0.0.0', port=5050)


if __name__ == "__main__":
    utopia_handler = UtopiaAPIHandler()
    utopia_handler.run()
