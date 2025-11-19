""" Working With Powercode"""
import os
import json
import time
import base64
import config
import requests

from requests.auth import HTTPBasicAuth, AuthBase
from config import PC_VERIFY_SSL, CUSTOMER_PORTAL_PASSWORD



# Small implementation of API key only authentication
class PcApiKeyAuth(AuthBase):
    def __init__(self, key: str):
        self.encoded_key = base64.b64encode(key.encode()).decode()

    def __call__(self, r: requests.PreparedRequest):
        r.headers["Authorization"] = f"Basic {self.encoded_key}"
        return r


def create_powercode_account(customer_info, max_retries=3, retry_delay=5):
    if customer_info['state'] == "Montana":
        customer_info['state'] = "MT"

    notes = (
        f"Order# {customer_info.get('orderref', '')}\n"
        f"Utopia SiteID: {customer_info.get('siteid', '')}\n"
        f"Agreed to Service Provider Terms: {customer_info.get('sp_terms_agree_date', '')}"
    )

    account_data = {
        'apiKey': config.PC_API_KEY,
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
        "customerNotes": notes,
        "customerPortalUsername": customer_info['customerPortalUsername'],
        "customerPortalPassword": CUSTOMER_PORTAL_PASSWORD,
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
            response = requests.post(config.PC_URL_API, data=account_data, verify=PC_VERIFY_SSL)
            # print(PC_response.json())

            if 'customerID' in response.json():
                # Account created successfully
                PC_customer_id = response.json()['customerID']
                print(f"Powercode account created successfully: {response}")
                return PC_customer_id
            elif response.json().get('statusCode') == 23:
                # Geocoding failed, retry with physicalAutomaticallyGeocode set to 0
                # print("Geocoding failed. Retrying with physicalAutomaticallyGeocode set to 0.")
                account_data["physicalAutomaticallyGeocode"] = 0
                time.sleep(retry_delay)
            else:
                # Other error, stop retrying
                # print(f"Failed to create Powercode account. Response: {PC_response.json()}")
                error_message = response.json().get('message', 'Unknown error in Powercode')
                #utopia_handler.send_email("Failed to create Powercode account", f"Error message: {error_message}")
                break

        except Exception as e:
            print(f"Exception during Powercode account creation: {e}")
            time.sleep(retry_delay)

    print(f"Failed to create Powercode account after {max_retries} attempts.")
    
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)

    return -1, response.text


def read_powercode_account(customerID):
    account_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'readCustomer',
        'customerID': customerID,
    }

    PC_response = requests.post(config.PC_URL_API, data=account_data, verify=PC_VERIFY_SSL)
    return PC_response

# Read account
def get_customer_by_external_id(external_id):
    account_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'readCustomer',
        'extAccountID': external_id,
    }

    PC_response = requests.post(config.PC_URL_API, data=account_data, verify=PC_VERIFY_SSL)
    return PC_response


# Search customer
def search_powercode_customers(searchString):
    account_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'searchCustomers',
        'searchString': searchString,
    }

    PC_response = requests.post(config.PC_URL_API, data=account_data, verify=PC_VERIFY_SSL)
    return PC_response.json()


### Tickets ###
def create_powercode_ticket(customer_id, description):

    # print(customer_id)
    ticket_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'createTicket',
        "type": "Individual",
        "summary": "BZN - Customer has requested Global Net Fiber Service",
        "category": 54,
        "ticketType": 21,
        "description": description,
        "status": 1,
        "responsibleUser": "Sales",
        "responsibleGroupID": 4,
        "customerViewable": 1,
        "customerID": customer_id,

    }

    PC_response = requests.post(config.PC_URL_API, data=ticket_data, verify=PC_VERIFY_SSL)

    # after ticket created, response will contain ticketID that will be need for reply ticket
    # {'message': 'Ticket created', 'statusCode': 0, 'ticketID': '15'}

    # print(PC_response.json())

    ticket_id = PC_response.json().get('ticketID', None)

    return ticket_id

def read_powercode_ticket(ticket_id):
    ticket_data = {
        'apiKey': config.PC_API_KEY,
        'action': 'readTicket',
        "ticketID": ticket_id
    }

    PC_response = requests.post(config.PC_URL_API, data=ticket_data, verify=PC_VERIFY_SSL)

    # after ticket created, response will contain ticketID that will be need for reply ticket
    # {'message': 'Ticket created', 'statusCode': 0, 'ticketID': '15'}

    # print(PC_response.json())


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

    pc_response = requests.post(config.PC_URL_API, data=service_data, verify=PC_VERIFY_SSL)

    return pc_response.json()

#
# 
#

def get_customer_tags(customer_id):
    """
    Get tags for a specific customer
    """
    path = "uapi/customer/tags/customer"
    
    url = f"{config.PC_URL_UAPI}/{path}"

    params = {
        "customerID": customer_id
    }

    response = requests.get(
        url,
        params = params,
        auth = PcApiKeyAuth(config.PC_API_KEY),
        allow_redirects = True,
    )

    print("Status Code:", response.status_code)
    print("Response Body:", response.text)

    return response.text

# {"Success":true,"Response":[{"TagID":5,"TagName":"Bridged Handoff"},{"TagID":9,"TagName":"Yellowstone Fiber Customer"}]}
def add_customer_tag(customer_id, tags_id_list):
    """
    Add a tags to a customer
    """
    path = "uapi/customer/tags/customer"
    url = f"{config.PC_URL_UAPI}/{path}"

    params = {
        "customerID": customer_id,
        "tags[]": tags_id_list
    }

    response = requests.post(
        url,
        params = params,
        auth = PcApiKeyAuth(config.PC_API_KEY),
        allow_redirects = True,
    )

    print("Status Code:", response.status_code)
    print("Response Body:", response.text)

    return response.text

def delete_customer_tag(customer_id, tags_id):
    """
    Add a tags to a customer
    """
    path = "uapi/customer/tags/customer"
    url = f"{config.PC_URL_UAPI}/{path}"

    params = {
        "customerID": customer_id,
        "tags[]": tags_id
    }

    response = requests.delete(
        url,
        params = params,
        auth = PcApiKeyAuth(config.PC_API_KEY),
        allow_redirects = True,
    )

    print("Status Code:", response.status_code)
    print("Response Body:", response.text)

    return response.text

    
def read_custom_action(action):
    fields = {
        "apiKey": config.PC_API_KEY,
        "action": action,
    }

    response = requests.post(config.PC_URL_API, data=fields, verify=PC_VERIFY_SSL)
    return response.json()
    