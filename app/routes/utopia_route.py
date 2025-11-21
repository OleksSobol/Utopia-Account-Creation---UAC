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

@utopia_bp.route('/admin/utopia/get_customer_by_cid', methods=['POST'])
def get_customer_by_cid():
    cid = request.form.get('cid')
    result = utopia.getCustomerByCID(cid)
    try:
        formatted = json.dumps(result, indent=2)
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

@utopia_bp.route('/admin/utopia/get_siteid_by_mac', methods=['POST'])
def get_siteid_by_mac():
    mac = request.form.get('mac')
    result = utopia.getSiteIDByMAC(mac)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/check_access', methods=['POST'])
def check_access():
    siteid = request.form.get('siteid')
    result = utopia.checkAccess(siteid=siteid if siteid else None)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/get_orders', methods=['POST'])
def get_orders():
    siteid = request.form.get('siteid')
    result = utopia.getOrders(siteid=siteid if siteid else None)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/get_projects', methods=['POST'])
def get_projects():
    siteid = request.form.get('siteid')
    result = utopia.getProjects(siteid=siteid if siteid else None)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/get_project_details', methods=['POST'])
def get_project_details():
    projectid = request.form.get('projectid')
    result = utopia.getProjectDetails(projectid)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/get_isp_products', methods=['POST'])
def get_isp_products():
    result = utopia.getISPProducts()
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/suspend_service', methods=['POST'])
def suspend_service():
    cid = request.form.get('cid')
    siteid = request.form.get('siteid')
    result = utopia.suspendService(cid, siteid)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/unsuspend_service', methods=['POST'])
def unsuspend_service():
    cid = request.form.get('cid')
    siteid = request.form.get('siteid')
    result = utopia.unsuspendService(cid, siteid)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/change_speed', methods=['POST'])
def change_speed():
    cid = request.form.get('cid')
    siteid = request.form.get('siteid')
    uiaid = request.form.get('uiaid')
    product = request.form.get('product')
    issuedate = request.form.get('issuedate')
    result = utopia.changeSpeed(cid, siteid, uiaid, product, issuedate)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/cancel_service', methods=['POST'])
def cancel_service():
    cid = request.form.get('cid')
    siteid = request.form.get('siteid')
    issuedate = request.form.get('issuedate')
    result = utopia.cancelService(cid, siteid, issuedate)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/search_outage_tickets', methods=['POST'])
def search_outage_tickets():
    siteid = request.form.get('siteid')
    result = utopia.searchOutageTickets(siteid=siteid if siteid else None)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))

@utopia_bp.route('/admin/utopia/get_outage_ticket', methods=['POST'])
def get_outage_ticket():
    ticketid = request.form.get('ticketid')
    result = utopia.getOutageTicket(ticketid)
    try:
        formatted = json.dumps(result, indent=2)
        flash(formatted)
    except:
        flash(str(result))
    return redirect(url_for('utopia.utopia_panel'))
