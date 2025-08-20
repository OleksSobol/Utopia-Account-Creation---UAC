import powercode as PowerCode
import utopia as Utopia

from api_callback import UtopiaAPIHandler

import utopia
import static_vars
import config
import urllib3

urllib3.disable_warnings()


def main():
    orderref = "UIA202411-001700"
    data = {'event': 'Project Update', 'orderref': 'UIA202411-001186', 'msg': 'Project New Order'}
    customer_from_utopia = Utopia.getCustomerFromUtopia(orderref)
    print(customer_from_utopia)
{'status': 'Signed', 'ordersource': 'webcustomer', 'promo': '', 'contractdownload': 'Ready', 'customer': {'firstname': 'Susie', 'lastname': 'Drukman', 'email': 'zannadruk@yahoo.com', 'phone': '4065818023'}, 'address': {'siteid': '714780', 'address': '411 N BROADWAY AVENUE', 'apt': '', 'city': 'Bozeman', 'zip': '59715', 'state': 'Montana'}, 'billingaddress': {'name': 'Susie Drukman', 'phone': '4065818023', 'address': '411 N BROADWAY AVENUE', 'apt': '', 'city': 'Bozeman', 'zip': '59715', 'state': 'Montana'}, 'orderitems': [{'pid': '259', 'chargetype': 'mrc', 'description': '250 Mbps', 'costper': '65', 'totalcost': '65', 'qty': '1'}], 'orderphoneport': []}


if __name__ == "__main__":
    main()
