""" Working With Powercode"""
import json
import time

import requests, random
import static_vars
import config
import os


def create_powercode_account(url, api_key, customer_info, customer_portal_password="WelcomeToGlobalNet", max_retries=3,
                             retry_delay=5):
    if customer_info['state'] == "Montana":
        customer_info['state'] = "MT"

    account_data = {
        'apiKey': api_key,
        'action': 'createCustomer',
        'firstName': customer_info['firstname'],
        'lastName': customer_info['lastname'],
        'emailAddress': customer_info['email'],
        "physicalStreet": customer_info['address'],
        "physicalCity": customer_info['city'],
        "physicalState": customer_info['state'],
        "physicalZip": customer_info['zip'],
        "physicalAutomaticallyGeocode": 1,
        "billingSameAsPhysical": 1,
        "taxZoneId": 1,
        "invoicePreference": "Email",
        "billDay": "Activation Date",
        "dueByDays": 0,
        "gracePeriodDays": 10,
        "customerNotes": 'Order# ' + customer_info['orderref'] +
                         "\nUtopia SiteID: " + customer_info['siteid'],
        "customerPortalUsername": customer_info['email'],
        "customerPortalPassword": customer_portal_password,
        "phone": json.dumps([
            {
                "Type": "Home",
                "Number": customer_info["phone"]
            }
        ]),
        "extAccountID": customer_info['siteid'],
    }

    for attempt in range(max_retries):
        print(f"Attempt #{attempt + 1} to create Powercode account.")

        try:
            PC_response = requests.post(url + ":444/api/1/index.php", data=account_data, verify=False)
            print(PC_response.json())

            if 'customerID' in PC_response.json():
                # Account created successfully
                PC_customer_id = PC_response.json()['customerID']
                print(f"Powercode account created successfully. Customer ID: {PC_customer_id}")
                return PC_customer_id
            elif PC_response.json().get('statusCode') == 23:
                # Geocoding failed, retry with physicalAutomaticallyGeocode set to 0
                print("Geocoding failed. Retrying with physicalAutomaticallyGeocode set to 0.")
                account_data["physicalAutomaticallyGeocode"] = 0
                time.sleep(retry_delay)
            else:
                # Other error, stop retrying
                print(f"Failed to create Powercode account. Response: {PC_response.json()}")
                error_message = PC_response.json().get('message', 'Unknown error in Powercode')
                #utopia_handler.send_email("Failed to create Powercode account", f"Error message: {error_message}")
                break

        except Exception as e:
            print(f"Exception during Powercode account creation: {e}")
            time.sleep(retry_delay)

    print(f"Failed to create Powercode account after {max_retries} attempts.")
    return -1


def read_powercode_account(customerID):
    account_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'readCustomer',
        'customerID': customerID,
    }

    PC_response = requests.post(static_vars.PC_URL + ":444/api/1/index.php", data=account_data, verify=False)
    print(PC_response.json())

# Read account
def get_customer_by_external_id(external_id):
    account_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'readCustomer',
        'extAccountID': external_id,
    }

    PC_response = requests.post(static_vars.PC_URL + ":444/api/1/index.php", data=account_data, verify=False)
    print(PC_response.json())


# Search customer
def search_powercode_customers(searchString):
    account_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'searchCustomers',
        'searchString': searchString,
    }

    PC_response = requests.post(static_vars.PC_URL + ":444/api/1/index.php", data=account_data, verify=False)
    return PC_response.json()


### Tickets ###
def create_powercode_ticket(customer_id, customer_name=""):
    # Path to the folder and the description file
    folder_path = 'ticket_descriptions'
    description_file = os.path.join(folder_path, 'new_desc.txt')

    # Create the folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)

    # Read the description from the text file
    with open(description_file, 'r') as file:
        new_desc = file.read()

    # Replace placeholders with dynamic values
    new_desc = new_desc.replace("{customer_name}", customer_name)

    # print(customer_id)
    ticket_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'createTicket',
        "type": "Individual",
        "summary": "BZN - Customer has requested Global Net Fiber Service",
        "category": 54,
        "ticketType": 21,
        "description": new_desc,
        "status": 1,
        "responsibleUser": "Sales",
        "responsibleGroupID": 4,
        "customerViewable": 1,
        "customerID": customer_id,

    }

    PC_response = requests.post(static_vars.PC_URL_Ticket, data=ticket_data, verify=False)

    # after ticket created, response will contain ticketID that will be need for reply ticket
    # {'message': 'Ticket created', 'statusCode': 0, 'ticketID': '15'}

    print(PC_response.json())

    ticket_id = PC_response.json().get('ticketID', None)

    return ticket_id

def read_powercode_ticket(ticket_id):
    ticket_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'readTicket',
        "ticketID": ticket_id
    }

    PC_response = requests.post(static_vars.PC_URL_Ticket, data=ticket_data, verify=False)

    # after ticket created, response will contain ticketID that will be need for reply ticket
    # {'message': 'Ticket created', 'statusCode': 0, 'ticketID': '15'}

    print(PC_response.json())


    return PC_response


# Service plans methods
def add_customer_service_plan(customer_id, service_plan_id):
    """
    Add a customer service plan to PowerCode.
    """
    service_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'addCustomerService',
        'customerID': customer_id,
        'serviceID': service_plan_id,
        'quantity': 5,
        'prorateService': 0
    }

    pc_response = requests.post(static_vars.PC_URL + ":444/api/1/index.php", data=service_data, verify=False)

    return pc_response.json()


    
def read_custom_action(action):
    fields = {
        "apiKey": config.PC_API_KEY,
        "action": action,
    }

    response = requests.post(static_vars.PC_URL + ":444/api/1/index.php", data=fields, verify=False)
    return response.json()
    

