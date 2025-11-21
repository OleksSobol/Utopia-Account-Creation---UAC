from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import powercode  # Import your API methods
import json

powercode_bp = Blueprint('powercode', __name__, template_folder='templates')

@powercode_bp.route('/admin/powercode')
def powercode_panel():
    return render_template('powercode.html')

@powercode_bp.route('/admin/powercode/create_account', methods=['POST'])
def create_account():
    customer_info = request.form.to_dict()
    customer_id, error = powercode.create_powercode_account(customer_info)
    if error:
        flash(f"Error: {error}")
    else:
        flash(f"Account created successfully!\nCustomer ID: {customer_id}")
    return redirect(url_for('powercode.powercode_panel'))

@powercode_bp.route('/admin/powercode/read_account', methods=['POST'])
def read_account():
    customer_id = request.form.get('customerID')
    result = powercode.read_powercode_account(customer_id)
    try:
        # Try to parse and format JSON
        json_data = result.json()
        formatted = json.dumps(json_data, indent=2)
        flash(formatted)
    except:
        flash(result.text)
    return redirect(url_for('powercode.powercode_panel'))

@powercode_bp.route('/admin/powercode/get_customer_by_external_id', methods=['POST'])
def get_customer_by_external_id():
    external_id = request.form.get('external_id')
    result = powercode.get_customer_by_external_id(external_id)
    try:
        json_data = result.json()
        formatted = json.dumps(json_data, indent=2)
        flash(formatted)
    except:
        flash(result.text)
    return redirect(url_for('powercode.powercode_panel'))

@powercode_bp.route('/admin/powercode/search_customers', methods=['POST'])
def search_customers():
    search_string = request.form.get('searchString')
    result = powercode.search_powercode_customers(search_string)
    try:
        # If result is already a dict
        if isinstance(result, dict):
            formatted = json.dumps(result, indent=2)
        else:
            formatted = json.dumps(result.json(), indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('powercode.powercode_panel'))

# search customer with new UAPI
@powercode_bp.route('/admin/powercode/search_customers_by_uapi', methods=['POST'])
def search_customers_by_uapi():
    search_string = request.form.get('searchString_by_uapi')
    result = powercode.search_customers_with_uapi(search_string)
    try:
        # If result is already a dict
        if isinstance(result, dict):
            formatted = json.dumps(result, indent=2)
        else:
            formatted = json.dumps(result.json(), indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('powercode.powercode_panel'))

@powercode_bp.route('/admin/powercode/create_ticket', methods=['POST'])
def create_ticket():
    customer_id = request.form.get('customer_id')
    description = request.form.get('description')
    ticket_id = powercode.create_powercode_ticket(customer_id, description)
    flash(f"Ticket created successfully!\nTicket ID: {ticket_id}")
    return redirect(url_for('powercode.powercode_panel'))

@powercode_bp.route('/admin/powercode/read_ticket', methods=['POST'])
def read_ticket():
    ticket_id = request.form.get('ticket_id')
    result = powercode.read_powercode_ticket(ticket_id)
    try:
        json_data = result.json()
        formatted = json.dumps(json_data, indent=2)
        flash(formatted)
    except:
        flash(result.text)
    return redirect(url_for('powercode.powercode_panel'))

@powercode_bp.route('/admin/powercode/add_service_plan', methods=['POST'])
def add_service_plan():
    customer_id = request.form.get('customer_id')
    service_plan_id = request.form.get('service_plan_id')
    result = powercode.add_customer_service_plan(customer_id, service_plan_id)
    try:
        if isinstance(result, dict):
            formatted = json.dumps(result, indent=2)
        else:
            formatted = json.dumps(result.json(), indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('powercode.powercode_panel'))

@powercode_bp.route('/admin/powercode/get_customer_tags', methods=['POST'])
def get_customer_tags():
    customer_id = request.form.get('customer_id')
    result = powercode.get_customer_tags(customer_id)
    try:
        if isinstance(result, dict):
            formatted = json.dumps(result, indent=2)
        else:
            formatted = json.dumps(result.json(), indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('powercode.powercode_panel'))

@powercode_bp.route('/admin/powercode/add_customer_tag', methods=['POST'])
def add_customer_tag():
    customer_id = request.form.get('customer_id')
    tags_id_list = request.form.get('tags_id_list').split(',')
    result = powercode.add_customer_tag(customer_id, tags_id_list)
    try:
        if isinstance(result, dict):
            formatted = json.dumps(result, indent=2)
        else:
            formatted = json.dumps(result.json(), indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('powercode.powercode_panel'))

@powercode_bp.route('/admin/powercode/delete_customer_tag', methods=['POST'])
def delete_customer_tag():
    customer_id = request.form.get('customer_id')
    tags_id = request.form.get('tags_id')
    result = powercode.delete_customer_tag(customer_id, tags_id)
    try:
        if isinstance(result, dict):
            formatted = json.dumps(result, indent=2)
        else:
            formatted = json.dumps(result.json(), indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('powercode.powercode_panel'))

@powercode_bp.route('/admin/powercode/read_custom_action', methods=['POST'])
def read_custom_action():
    action = request.form.get('action')
    result = powercode.read_custom_action(action)
    try:
        if isinstance(result, dict):
            formatted = json.dumps(result, indent=2)
        else:
            formatted = json.dumps(result.json(), indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('powercode.powercode_panel'))