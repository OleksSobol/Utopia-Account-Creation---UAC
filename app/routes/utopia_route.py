from flask import Blueprint, render_template, request, redirect, url_for, flash
import utopia  # Import your Utopia API methods
import json

utopia_bp = Blueprint('utopia', __name__, template_folder='templates')

@utopia_bp.route('/admin/utopia')
def utopia_panel():
    return render_template('utopia.html')

@utopia_bp.route('/admin/utopia/get_customer', methods=['POST'])
def get_customer():
    orderref = request.form.get('orderref')
    result = utopia.getCustomerFromUtopia(orderref)
    try:
        if isinstance(result, dict):
            formatted = json.dumps(result, indent=2)
        else:
            formatted = str(result)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/get_mac', methods=['POST'])
def get_mac():
    siteid = request.form.get('siteid')
    result = utopia.getUtopiaCustomerMAC(siteid)
    try:
        if isinstance(result, dict):
            formatted = json.dumps(result, indent=2)
        else:
            formatted = str(result)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/get_service', methods=['POST'])
def get_service():
    siteid = request.form.get('siteid')
    result = utopia.getCustomerService(siteid)
    try:
        if isinstance(result, dict):
            formatted = json.dumps(result, indent=2)
        else:
            formatted = str(result)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/print_customer_info', methods=['POST'])
def print_customer_info():
    data = request.form.get('customer_json')
    try:
        data_dict = json.loads(data)
        customer, address = utopia.printCustomerInfo(data_dict)
        result = {
            "customer": customer,
            "address": address
        }
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except Exception as e:
        flash(f"Error: {str(e)}")
    return redirect(url_for('utopia.utopia_panel'))