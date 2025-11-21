""" Working With Utopia"""
import requests
import json
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
        config.URL_ENDPOINT + config.UTOPIA_Contract_Lookup, data=json.dumps(params))

    if "error" not in response.text and response.status_code == 200:
        data = response.json()
        # print(printCustomerInfo(data))
    else:
        data = response.json()

    return data


# get MAC address of router from UTOPIA
def getUtopiaCustomerMAC(siteid):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "siteid": siteid,
    }

    response = requests.post(config.URL_ENDPOINT + config.UTOPIA_APView, data=json.dumps(JSON_REQUEST))
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

    response = requests.post(config.URL_ENDPOINT + config.UTOPIA_Service_Lookup,
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
# Check Access Rights to Site / Customer
def checkAccess(siteid=None, clientid=None):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
    }
    if siteid:
        JSON_REQUEST["siteid"] = siteid
    if clientid:
        JSON_REQUEST["clientid"] = clientid
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/checkaccess", data=json.dumps(JSON_REQUEST))
    return response.json()


# Edit Service Item
def editServiceItem(servid, spsubid1=None, spsubid2=None, spsubid3=None):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "servid": servid,
    }
    if spsubid1 is not None:
        JSON_REQUEST["spsubid1"] = spsubid1
    if spsubid2 is not None:
        JSON_REQUEST["spsubid2"] = spsubid2
    if spsubid3 is not None:
        JSON_REQUEST["spsubid3"] = spsubid3
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/editserviceitem", data=json.dumps(JSON_REQUEST))
    return response.json()


# Contract Download
def downloadContract(orderref):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "orderref": orderref,
    }
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/contractdownload", data=json.dumps(JSON_REQUEST))
    return response


# Order Lookup
def getOrders(status=None, siteid=None, orderref=None):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
    }
    if status:
        JSON_REQUEST["status"] = status
    if siteid:
        JSON_REQUEST["siteid"] = siteid
    if orderref:
        JSON_REQUEST["orderref"] = orderref
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/orders", data=json.dumps(JSON_REQUEST))
    return response.json()


# Edit Order Item
def editOrderItem(itemid, handoff=None, nnivlan=None, nnivlanservice=None, vlan=None, vlanservice=None, spsubid1=None, spsubid2=None, spsubid3=None):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "itemid": itemid,
    }
    if handoff is not None:
        JSON_REQUEST["handoff"] = handoff
    if nnivlan is not None:
        JSON_REQUEST["nnivlan"] = nnivlan
    if nnivlanservice is not None:
        JSON_REQUEST["nnivlanservice"] = nnivlanservice
    if vlan is not None:
        JSON_REQUEST["vlan"] = vlan
    if vlanservice is not None:
        JSON_REQUEST["vlanservice"] = vlanservice
    if spsubid1 is not None:
        JSON_REQUEST["spsubid1"] = spsubid1
    if spsubid2 is not None:
        JSON_REQUEST["spsubid2"] = spsubid2
    if spsubid3 is not None:
        JSON_REQUEST["spsubid3"] = spsubid3
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/editorderitem", data=json.dumps(JSON_REQUEST))
    return response.json()


# Customer Lookup
def getCustomerByCID(cid):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "cid": cid,
    }
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/customer", data=json.dumps(JSON_REQUEST))
    return response.json()


# Suspend Service
def suspendService(cid, siteid):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "cid": cid,
        "siteid": siteid,
    }
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/suspend", data=json.dumps(JSON_REQUEST))
    return response.json()


# Unsuspend Service
def unsuspendService(cid, siteid):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "cid": cid,
        "siteid": siteid,
    }
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/unsuspend", data=json.dumps(JSON_REQUEST))
    return response.json()


# Change Speed
def changeSpeed(cid, siteid, uiaid, product, issuedate):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "cid": cid,
        "siteid": siteid,
        "uiaid": uiaid,
        "product": product,
        "issuedate": issuedate,
    }
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/changespeed", data=json.dumps(JSON_REQUEST))
    return response.json()


# Cancel Service
def cancelService(cid, siteid, issuedate, singleservice=None):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "cid": cid,
        "siteid": siteid,
        "issuedate": issuedate,
    }
    if singleservice:
        JSON_REQUEST["singleservice"] = singleservice
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/cancelservice", data=json.dumps(JSON_REQUEST))
    return response.json()


# SiteID Lookup by MAC Address
def getSiteIDByMAC(mac, hourshistory=1):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "mac": mac,
        "hourshistory": hourshistory,
    }
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/macsearch", data=json.dumps(JSON_REQUEST))
    return response.json()


# ISP Products
def getISPProducts():
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
    }
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/products", data=json.dumps(JSON_REQUEST))
    return response.json()


# Project Lookup
def getProjects(statusid=None, siteid=None, orderref=None):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
    }
    if statusid:
        JSON_REQUEST["statusid"] = statusid
    if siteid:
        JSON_REQUEST["siteid"] = siteid
    if orderref:
        JSON_REQUEST["orderref"] = orderref
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/projects", data=json.dumps(JSON_REQUEST))
    return response.json()


# Project Details
def getProjectDetails(projectid):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "projectid": projectid,
    }
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/projectdetail", data=json.dumps(JSON_REQUEST))
    return response.json()


# Outage Ticket Search
def searchOutageTickets(siteid=None, clientid=None, eventdate=None, status=None, sla=None, devicequery=None, utc=False):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
    }
    if siteid:
        JSON_REQUEST["siteid"] = siteid
    if clientid:
        JSON_REQUEST["clientid"] = clientid
    if eventdate:
        JSON_REQUEST["eventdate"] = eventdate
    if status:
        JSON_REQUEST["status"] = status
    if sla is not None:
        JSON_REQUEST["sla"] = sla
    if devicequery:
        JSON_REQUEST["devicequery"] = devicequery
    if utc:
        JSON_REQUEST["utc"] = utc
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/outagetickets", data=json.dumps(JSON_REQUEST))
    return response.json()


# Outage Ticket Lookup
def getOutageTicket(ticketid, utc=False):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "ticketid": ticketid,
    }
    if utc:
        JSON_REQUEST["utc"] = utc
    
    response = requests.post(config.URL_ENDPOINT + "/spquery/outageticket", data=json.dumps(JSON_REQUEST))
    return response.json()


# Bulk Address Export
def bulkAddressExport(network):
    JSON_REQUEST = {
        "apikey": config.UTOPIA_API_KEY,
        "network": network,
    }
    
    response = requests.post(config.URL_ENDPOINT + "/address/bulkexport", data=json.dumps(JSON_REQUEST))
    return response.json()