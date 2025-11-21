from flask import Blueprint, render_template, request, redirect, url_for, flash
import utopia  # Import your Utopia API methods

utopia_bp = Blueprint('utopia', __name__, template_folder='templates')

@utopia_bp.route('/admin/utopia')
def utopia_panel():
    return render_template('utopia.html')

@utopia_bp.route('/admin/utopia/get_customer', methods=['POST'])
def get_customer():
    orderref = request.form.get('orderref')
    result = utopia.getCustomerFromUtopia(orderref)
    flash(f"Customer info: {result}")
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/get_mac', methods=['POST'])
def get_mac():
    siteid = request.form.get('siteid')
    result = utopia.getUtopiaCustomerMAC(siteid)
    flash(f"MAC address: {result}")
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/get_service', methods=['POST'])
def get_service():
    siteid = request.form.get('siteid')
    result = utopia.getCustomerService(siteid)
    flash(f"Service info: {result}")
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/print_customer_info', methods=['POST'])
def print_customer_info():
    # For demo, you can pass a JSON string in the form
    import json
    data = request.form.get('customer_json')
    try:
        data_dict = json.loads(data)
        customer, address = utopia.printCustomerInfo(data_dict)
        flash(f"Customer: {customer}, Address: {address}")
    except Exception as e:
        flash(f"Error: {e}")
    return redirect(url_for('utopia.utopia_panel'))