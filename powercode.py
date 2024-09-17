""" Working With Powercode"""
import json
import time

import requests, random
import static_vars
import config


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
    new_desc = \
    f"""
    <p>Hello {customer_name},</p>
    <p>Thank you for your recent request for Internet Service with Global Net via Yellowstone Fiber.&nbsp; We have received notification of your request through the Yellowstone Fiber portal. Global Net will monitor the construction progress in partnership with them.&nbsp; If you have any questions regarding the construction they can be reached at 406-312-5777.</p>
    <p>In preparation for what is to come here are a few things to consider, plan for, and discuss with the technician when they arrive:</p>
    <ol>
        <li>
            <p>Where should the Fiber ONT (modem) be installed?</p>
            <ul>
                <li>Somewhere near a power outlet</li>
                <li>Somewhere accessible for troubleshooting purposes</li>
                <li>At your Smart Panel if you have one (see below for more information)</li>
            </ul>
        <p>Yellowstone Fiber will install the ONT and run a single Ethernet cable to your preferred, but reasonable, location for a router.&nbsp;<br>A link to the Top 10 Router Recommendations by Yellowstone Fiber can be found <a href="https://www.yellowstonefiber.com/top-10-router-recommendations/">HERE</a>.</p>
        </li>
        <li>
            <p>Where should your router be located?</p>
            <ul>
                <li>Centrally located in an open area of your home/office to ensure the best WiFi coverage</li><li>Somewhere easily accessible for troubleshooting</li>
                <li>As high up as possible to avoid obstruction by other items or devices</li>
                <li>At your Smart Panel if you have one (see below for more information)
                </li>
            </ul>
        </li>
        <li>
            <p>Where should you&nbsp;<strong><u>NOT</u></strong>&nbsp;place your router?</p>
            <ul>
                <li>In a closet</li>
                <li>In a drawer</li>
                <li>On the floor</li>
                <li>In a crawlspace</li>
                <li>In a pantry</li>
                <li>Under a sink</li>
                <li>In an attic</li>
                <li>On a bookshelf covered with books</li>
                <li>Outside, exposed to the elements</li>
            </ul>
        </li>
    </ol>
    <p>If you have a Smart Panel in your home/office and would like to utilize your existing home wiring or WiFi access points, it will be best to have your router located at the Smart Panel. Please refer to your Smart Home specialist or IT consultant with any questions as Global Net does not support, nor is responsible for, any internal networking configurations.</p>
    <p>Global Net and Yellowstone Fiber do not service or support the LAN side of your internet service. Customer-owned devices like your router, phones, computers, gaming consoles, IOT, and TV’s are not supported by either company. These will be the responsibility of the customer to troubleshoot and maintain.</p>
    <p>After the installation of the Yellowstone Fiber ONT is complete <strong>BILLING WILL START</strong>. If&nbsp;your router is available at the install, the installer will&nbsp;connect it&nbsp;to the ONT and&nbsp;will&nbsp;confirm you have internet access.</p>
    <br>
    <p><strong>BILLING INFORMATION</strong></p>
    <br>
    <p>Once your service is activated you will need to call Global Net Billing at 406-587-5095, Option 3.&nbsp; Our Customer Service Reps will set up auto billing on a credit or debit card. You can also use this link to the Global Net Customer portal to upload your billing information <a href="https://customer.theglobal.net/">HERE</a>.</p>
    <p>There is a 10 day grace period after activation.&nbsp; After 10 days without payment, service will be interrupted.</p>
    <p>Your payment to Yellowstone Fiber is $30 per month but will be billed and collected by Global Net with our bill for internet service.&nbsp;<br></p>
    <p>Please let us know if you have any questions and we look forward to bringing you online soon!</p>
    <br>
    <p>Sincerely,<br>Global Net Fiber Support</p>
    """

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

    ticketID = PC_response.json()['ticketID']

    return ticketID

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




### Service plans

def add_customer_service_plan(url, api, customer_id, utopia_service):
    """
    REAL  PC:
    ID  Name
    139	YF Residential 250
    140	YF Residential 1000
    161 - YF Gig 2024    

    """
    print("from add_customer_service_plan:", utopia_service)
    if utopia_service == "1 Gbps":
        service_id = 164
    elif utopia_service == "250 Mbps":
        service_id = 163
    else:
        service_id = 163

    service_data = {
        'apiKey': api,
        'action': 'addCustomerService',
        'customerID': customer_id,
        'serviceID': service_id,
        'quantity': 5,
        'prorateService': 0
    }

    pc_response = requests.post(url + ":444/api/1/index.php", data=service_data, verify=False)

    return pc_response.json()


    
def read_custom_action(action):
    fields = {
        "apiKey": config.PC_API_KEY,
        "action": action,
    }

    response = requests.post(static_vars.PC_URL + ":444/api/1/index.php", data=fields, verify=False)
    return response.json()
    

