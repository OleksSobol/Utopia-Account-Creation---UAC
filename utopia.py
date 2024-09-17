""" Working With Utopia"""
import requests
import json
import static_vars

# setting up params for API URL
params = {
    'apikey': static_vars.UTOPIA_API_KEY,
}


# get customer - Contract Lookup
# When authenticated, this endpoint returns additional order status information
def getCustomerFromUtopia(orderref):
    params["orderref"] = orderref

    response = requests.post(
        static_vars.URL_ENDPOINT + static_vars.UTOPIA_Contract_Lookup, data=json.dumps(params))

    if "error" not in response.text and response.status_code == 200:
        data = response.json()
        # print(printCustomerInfo(data))
    else:
        # print(response.json())
        data = "Error"
    return data


# get MAC address of router from UTOPIA
def getUtopiaCustomerMAC(siteid):
    JSON_REQUEST = {
        "apikey": static_vars.UTOPIA_API_KEY,
        "siteid": siteid,
    }

    response = requests.post(static_vars.URL_ENDPOINT + static_vars.UTOPIA_APView, data=json.dumps(JSON_REQUEST))
    try:
        APView = response.json()["result"][0]['eth']['eth1']["macs"][0][:17]
        APView_full = response.json()
        # print(f"If you see this than something is working right\n {APView_full}")
    except:
        APView = response.json()
        # APView = "No Mac Found"
    return APView


# This endpoint allows the service provider to query service details, optionally limited by various filters
def getCustomerService(siteid):
    JSON_REQUEST = {
        "apikey": static_vars.UTOPIA_API_KEY,
        "siteid": siteid,
    }

    response = requests.post(static_vars.URL_ENDPOINT + static_vars.UTOPIA_Service_Lookup,
                             data=json.dumps(JSON_REQUEST))
    try:
        APView_full = response.json()
        # print(f"If you see this than something is not fucked up\n {APView_full}")
    except:
        APView_full = response.json()
    return APView_full


# Download contract PDF document. If the document is ready for download, the PDF data is sent. If it is not ready,
# a json response is sent.
def getContractDownload(orderref):
    JSON_REQUEST = {
        "apikey": static_vars.UTOPIA_API_KEY,
        "orderref": orderref,
    }

    response = requests.post(static_vars.URL_ENDPOINT + static_vars.UTOPIA_Contract_Download,
                             data=json.dumps(JSON_REQUEST))
    APView_full = response.json()

    return APView_full

def download_contract_pdf(orderref):
    """
    Download contract PDF document.
    If the document is ready for download, the PDF data is sent.
    If it is not ready,a json response is sent.

    """
    json_request = {
        "apikey": static_vars.UTOPIA_API_KEY,
        "orderref": orderref,
    }

    # API endpoint URL
    url = "https://api.utopiafiber.dev/spquery/contractdownload"

    try:
        response = requests.post(static_vars.URL_ENDPOINT + static_vars.UTOPIA_Contract_Download,
                             data=json.dumps(json_request))
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Check the content type of the response
            content_type = response.headers.get('content-type')
            if content_type == 'application/pdf; charset=UTF-8':
                # PDF file is ready for download, return the content
                return response.content
            else:
                # Unexpected response content type
                print("Unexpected response content type:", content_type)
                return None
        elif response.status_code == 404:
            # Order not found or no valid records found for the ISP
            error_message = response.json().get("error", "Unknown error")
            print("Error:", error_message)
            return None

        else:
            # Unexpected status code
            print("Unexpected status code:", response.status_code)
            return None

    except requests.RequestException as e:
        # Handle HTTP request exceptions
        print("HTTP request failed:", e)
        return None

#Custom function
def printCustomerInfo(data):
    customer = {
                   'firstname': data['customer']['firstname'],
                   'lastname': data['customer']['lastname'],
                   'email': data['customer']['email'],
                   'phone': data['customer']['phone'],
               },
    address = {
        'address': data["address"]['address'],
        'apt': data["address"]['apt'],
        'city': data["address"]['city'],
        'zip': data["address"]['zip'],
        'state': data["address"]['state'],
    }
    return customer, address
