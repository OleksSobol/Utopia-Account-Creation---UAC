// Utopia Admin Dashboard JavaScript
// Handles customer lookup, editing, and PowerCode integration

// Global state
let currentCustomerData = {};
let currentServicePlans = {};
let currentEditingOrderref = null;

// DOM Elements
const form = document.getElementById('lookupForm');
const orderrefInput = document.getElementById('orderref');
const submitBtn = document.getElementById('submitBtn');
const btnText = document.getElementById('btnText');
const btnIcon = document.getElementById('btnIcon');
const loadingSpinner = document.getElementById('loadingSpinner');
const clearBtn = document.getElementById('clearBtn');
const logWindow = document.getElementById('logWindow');
const logStatus = document.getElementById('logStatus');

// Utility Functions
function updateStatus(text, type = 'ready') {
    const colors = {
        ready: 'bg-gray-100 text-gray-600',
        loading: 'bg-blue-100 text-blue-600',
        success: 'bg-green-100 text-green-600',
        error: 'bg-red-100 text-red-600'
    };
    
    const icons = {
        ready: 'fa-circle',
        loading: 'fa-spinner fa-spin',
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle'
    };
    
    logStatus.className = `px-4 py-2 rounded-full ${colors[type]} text-sm font-semibold`;
    logStatus.innerHTML = `<i class="fas ${icons[type]} mr-2"></i>${text}`;
}

function addLogEntry(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const colors = {
        info: 'border-l-blue-500 bg-blue-50',
        success: 'border-l-green-500 bg-green-50',
        error: 'border-l-red-500 bg-red-50'
    };
    
    const entry = document.createElement('div');
    entry.className = `mb-6 pb-6 border-l-4 ${colors[type]} p-6 rounded-r-xl`;
    entry.innerHTML = `
        <div class="text-xs text-gray-500 mb-2 flex items-center">
            <i class="far fa-clock mr-2"></i>[${timestamp}]
        </div>
        <div class="text-gray-700">${message}</div>
    `;
    
    if (logWindow.querySelector('.text-center')) {
        logWindow.innerHTML = '';
    }
    
    logWindow.appendChild(entry);
    logWindow.scrollTop = logWindow.scrollHeight;
}

function getServicePlan(data) {
    if (data.orderitems && data.orderitems.length > 0) {
        return data.orderitems[0].description || "250 Mbps (default)";
    }
    return "250 Mbps (default)";
}

function formatCustomerData(data, orderref) {
    const selectedPlan = currentServicePlans[orderref] || getServicePlan(data);
    return `
        <div class="space-y-6">
            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border-2 border-blue-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold text-blue-700 flex items-center">
                        <i class="fas fa-clipboard-list mr-2"></i>Utopia Order Data
                    </h3>
                    <div class="flex space-x-2">
                        <button 
                            onclick="editPowerCodeData('${orderref}')"
                            class="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg flex items-center shadow-md hover:shadow-lg"
                        >
                            <i class="fas fa-edit mr-2"></i>Edit
                        </button>
                        <button 
                            onclick="sendToPowerCode('${orderref}')"
                            class="bg-green-600 hover:bg-green-700 text-white text-sm font-semibold px-4 py-2 rounded-lg flex items-center shadow-md hover:shadow-lg"
                        >
                            <i class="fas fa-paper-plane mr-2"></i>Send to PowerCode
                        </button>
                        <button 
                            onclick="toggleRawJson('${orderref}')"
                            id="rawJsonBtn-${orderref}"
                            class="bg-gray-600 hover:bg-gray-700 text-white text-sm font-semibold px-4 py-2 rounded-lg flex items-center shadow-md hover:shadow-lg"
                        >
                            <i class="fas fa-code mr-2"></i>View JSON
                        </button>
                    </div>
                </div>
                
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-white p-4 rounded-lg">
                            <span class="font-bold text-blue-600 block mb-1">Status</span>
                            <span class="text-gray-800">${data.status || 'N/A'}</span>
                        </div>
                        <div class="bg-white p-4 rounded-lg">
                            <span class="font-bold text-blue-600 block mb-1">Order Source</span>
                            <span class="text-gray-800">${data.ordersource || 'N/A'}</span>
                        </div>
                    </div>

                    ${data.customer ? `
                    <div class="bg-white p-4 rounded-lg">
                        <div class="font-bold text-blue-600 mb-3 flex items-center">
                            <i class="fas fa-user mr-2"></i>Customer Information
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                            <div><span class="font-semibold">Name:</span> ${data.customer.firstname} ${data.customer.lastname}</div>
                            <div><span class="font-semibold">Email:</span> ${data.customer.email}</div>
                            <div><span class="font-semibold">Phone:</span> ${data.customer.phone}</div>
                        </div>
                    </div>
                    ` : ''}

                    ${data.address ? `
                    <div class="bg-white p-4 rounded-lg">
                        <div class="font-bold text-blue-600 mb-3 flex items-center">
                            <i class="fas fa-map-marker-alt mr-2"></i>Service Address
                        </div>
                        <div class="space-y-2">
                            <div><span class="font-semibold">Site ID:</span> ${data.address.siteid || 'N/A'}</div>
                            <div><span class="font-semibold">Address:</span> ${data.address.address}</div>
                            ${data.address.apt ? `<div><span class="font-semibold">Apt:</span> ${data.address.apt}</div>` : ''}
                            <div><span class="font-semibold">City:</span> ${data.address.city}, ${data.address.state} ${data.address.zip}</div>
                        </div>
                    </div>
                    ` : ''}

                    ${data.orderitems && data.orderitems.length > 0 ? `
                    <div class="bg-white p-4 rounded-lg">
                        <div class="font-bold text-blue-600 mb-3 flex items-center">
                            <i class="fas fa-shopping-cart mr-2"></i>Order Items
                        </div>
                        <div class="space-y-3">
                            ${data.orderitems.map(item => `
                                <div class="bg-gray-50 p-3 rounded-lg border border-gray-200">
                                    <div><span class="font-semibold">Description:</span> ${item.description}</div>
                                    <div class="text-sm text-gray-600 mt-1">
                                        <span class="font-semibold">Quantity:</span> ${item.qty} | 
                                        <span class="font-semibold">Cost:</span> ${item.totalcost}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>

            <div id="rawJsonSection-${orderref}" class="bg-gray-900 p-6 rounded-xl border-2 border-gray-700 hidden">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-bold text-green-400 flex items-center">
                        <i class="fas fa-code mr-2"></i>Raw JSON Data
                    </h3>
                </div>
                <div id="pcData-${orderref}" class="bg-gray-800 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto custom-scrollbar">
                    <pre class="whitespace-pre-wrap"></pre>
                </div>
            </div>
        </div>
    `;
}

function toggleRawJson(orderref) {
    const section = document.getElementById(`rawJsonSection-${orderref}`);
    const button = document.getElementById(`rawJsonBtn-${orderref}`);
    
    if (!section || !button) return;
    
    const isHidden = section.classList.contains('hidden');
    
    if (isHidden) {
        section.classList.remove('hidden');
        button.innerHTML = '<i class="fas fa-times mr-2"></i>Hide JSON';
        button.classList.replace('bg-gray-600', 'bg-red-600');
        button.classList.replace('hover:bg-gray-700', 'hover:bg-red-700');
    } else {
        section.classList.add('hidden');
        button.innerHTML = '<i class="fas fa-code mr-2"></i>View JSON';
        button.classList.replace('bg-red-600', 'bg-gray-600');
        button.classList.replace('hover:bg-red-700', 'hover:bg-gray-700');
    }
}

// Form submission handler
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const orderref = orderrefInput.value.trim();
    
    if (!orderref) {
        addLogEntry('[ERROR] Please enter an order reference', 'error');
        return;
    }

    submitBtn.disabled = true;
    btnText.textContent = 'Searching...';
    btnIcon.classList.add('hidden');
    loadingSpinner.classList.remove('hidden');
    updateStatus('Querying...', 'loading');

    addLogEntry(`Querying orderref: <strong>${orderref}</strong>`, 'info');

    try {
        const response = await fetch('/api/lookup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ orderref })
        });

        const result = await response.json();

        if (result.success) {
            console.log('Customer Data:', result.data);
            
            result.data.orderref = orderref;
            currentCustomerData[orderref] = result.data;
            currentServicePlans[orderref] = getServicePlan(result.data);
            
            addLogEntry(formatCustomerData(result.data, orderref), 'success');
            
            setTimeout(() => {
                const pcDataElement = document.getElementById(`pcData-${orderref}`);
                if (pcDataElement) {
                    const preElement = pcDataElement.querySelector('pre');
                    if (preElement) {
                        preElement.textContent = JSON.stringify(result.data, null, 2);
                    }
                }
            }, 10);
            
            updateStatus('Success', 'success');
        } else {
            addLogEntry(`[ERROR] ${result.error}`, 'error');
            updateStatus('Error', 'error');
        }
    } catch (error) {
        addLogEntry(`[ERROR] Failed to connect to server: ${error.message}`, 'error');
        updateStatus('Connection Error', 'error');
        console.error('Fetch error:', error);
    } finally {
        submitBtn.disabled = false;
        btnText.textContent = 'Search';
        btnIcon.classList.remove('hidden');
        loadingSpinner.classList.add('hidden');
        
        setTimeout(() => updateStatus('Ready', 'ready'), 3000);
    }
});

// Clear button handler
clearBtn.addEventListener('click', () => {
    logWindow.innerHTML = `
        <div class="text-center text-gray-400 py-20">
            <i class="fas fa-inbox text-6xl mb-4 opacity-50"></i>
            <p class="text-lg">Waiting for search query...</p>
        </div>
    `;
    updateStatus('Ready', 'ready');
});

// Modal functions
function editPowerCodeData(orderref) {
    const rawData = currentCustomerData[orderref];
    if (!rawData) {
        alert('No customer data found. Please search again.');
        return;
    }

    const customer = rawData.customer || {};
    const address = rawData.address || {};
    
    currentEditingOrderref = orderref;
    
    document.getElementById('edit-firstname').value = customer.firstname || '';
    document.getElementById('edit-lastname').value = customer.lastname || '';
    document.getElementById('edit-email').value = customer.email || '';
    document.getElementById('edit-phone').value = customer.phone || '';
    document.getElementById('edit-address').value = address.address || '';
    document.getElementById('edit-city').value = address.city || '';
    document.getElementById('edit-state').value = address.state || '';
    document.getElementById('edit-zip').value = address.zip || '';
    document.getElementById('edit-apt').value = address.apt || '';
    document.getElementById('edit-siteid').value = address.siteid || '';
    
    document.getElementById('editModal').classList.remove('hidden');
    document.getElementById('edit-firstname').focus();
}

function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
    currentEditingOrderref = null;
}

function saveEditedData() {
    if (!currentEditingOrderref) {
        alert('Error: No order reference found.');
        return;
    }

    const rawData = currentCustomerData[currentEditingOrderref] || {};
    rawData.customer = rawData.customer || {};
    rawData.address = rawData.address || {};
    
    rawData.customer.firstname = document.getElementById('edit-firstname').value.trim();
    rawData.customer.lastname = document.getElementById('edit-lastname').value.trim();
    rawData.customer.email = document.getElementById('edit-email').value.trim();
    rawData.customer.phone = document.getElementById('edit-phone').value.trim();
    rawData.address.address = document.getElementById('edit-address').value.trim();
    rawData.address.city = document.getElementById('edit-city').value.trim();
    rawData.address.state = document.getElementById('edit-state').value.trim();
    rawData.address.zip = document.getElementById('edit-zip').value.trim();
    rawData.address.apt = document.getElementById('edit-apt').value.trim();
    rawData.address.siteid = document.getElementById('edit-siteid').value.trim();
    
    currentCustomerData[currentEditingOrderref] = rawData;
    
    // Update display
    const logEntries = logWindow.querySelectorAll('.border-l-4');
    logEntries.forEach(entry => {
        const utopiaSection = entry.querySelector('.bg-gradient-to-r');
        if (utopiaSection) {
            const editButton = utopiaSection.querySelector(`button[onclick="editPowerCodeData('${currentEditingOrderref}')"]`);
            if (editButton) {
                entry.querySelector('.space-y-6').innerHTML = formatCustomerData(rawData, currentEditingOrderref);
                
                setTimeout(() => {
                    const pcDataElement = document.getElementById(`pcData-${currentEditingOrderref}`);
                    if (pcDataElement) {
                        const preElement = pcDataElement.querySelector('pre');
                        if (preElement) {
                            preElement.textContent = JSON.stringify(rawData, null, 2);
                        }
                    }
                }, 10);
            }
        }
    });
    
    closeEditModal();
    addLogEntry('✓ Customer data updated successfully', 'success');
}

async function sendToPowerCode(orderref) {
    const rawData = currentCustomerData[orderref];
    const servicePlan = currentServicePlans[orderref] || '250 Mbps';
    
    if (!rawData) {
        alert('No customer data found. Please search again.');
        return;
    }

    const c = rawData.customer || {};
    if (!confirm(`Create customer in PowerCode?\n\nName: ${c.firstname || ''} ${c.lastname || ''}\nEmail: ${c.email || ''}\nService Plan: ${servicePlan}\n\nThis will create the customer account and send notifications.`)) {
        return;
    }

    addLogEntry(`Sending customer data to PowerCode for orderref: <strong>${orderref}</strong>...`, 'info');
    updateStatus('Creating...', 'loading');

    try {
        const response = await fetch('/api/create-customer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                orderref,
                customer_data: rawData,
                service_plan: servicePlan
            })
        });

        const result = await response.json();

        if (result.success) {
            const successMsg = `
                <div class="space-y-3">
                    <div class="text-2xl font-bold text-green-600 flex items-center">
                        <i class="fas fa-check-circle mr-2"></i>Customer Created Successfully!
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-white p-3 rounded-lg">
                            <strong>PowerCode ID:</strong> ${result.customer_id}
                        </div>
                        <div class="bg-white p-3 rounded-lg">
                            <strong>Service Plan:</strong> ${result.service_plan || 'N/A'}
                        </div>
                        <div class="bg-white p-3 rounded-lg">
                            <strong>Ticket:</strong> ${result.ticket || 'Created'}
                        </div>
                    </div>
                    <div class="text-sm text-gray-600 mt-3">
                        <i class="fas fa-envelope mr-2"></i>Email notification sent to admin.
                    </div>
                </div>
            `;
            addLogEntry(successMsg, 'success');
            updateStatus('Success', 'success');
        } else {
            addLogEntry(`[ERROR] ${result.error}`, 'error');
            updateStatus('Error', 'error');
        }
    } catch (error) {
        addLogEntry(`[ERROR] Failed to create customer: ${error.message}`, 'error');
        updateStatus('Connection Error', 'error');
        console.error('Create customer error:', error);
    }
}

// Modal event listeners
document.getElementById('closeModalBtn').addEventListener('click', closeEditModal);
document.getElementById('cancelModalBtn').addEventListener('click', closeEditModal);
document.getElementById('saveChangesBtn').addEventListener('click', saveEditedData);

document.getElementById('editModal').addEventListener('click', (e) => {
    if (e.target.id === 'editModal') closeEditModal();
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && currentEditingOrderref) closeEditModal();
});

// Logout function
async function logout() {
    try {
        const response = await fetch('/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/login';
    }
}

// Focus on input on load
window.addEventListener('load', () => orderrefInput.focus());