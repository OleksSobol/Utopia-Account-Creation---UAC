""" Working With Utopia"""
import requests
import json
import static_vars
import config

# setting up params for API URL
params = {
    'apikey': config.UTOPIA_API_KEY,
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
        "apikey": config.UTOPIA_API_KEY,
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
        "apikey": config.UTOPIA_API_KEY,
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
