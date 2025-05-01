# Utopia API Handler

This Python project is designed to handle customer data integration between Utopia and PowerCode through an API. It processes orders from Utopia, searches for customers in PowerCode, and creates customer records in PowerCode if they do not exist. Additionally, it assigns service plans and sends notification emails.

## Features

1. **API Endpoint**: Handles incoming API callbacks from Utopia.
2. **Customer Management**: Searches for customers in PowerCode, creates new records if not found.
3. **Service Plan Assignment**: Adds appropriate service plans from Utopia and additional manual plans.
4. **Email Notifications**: Sends emails for success or failure, with attached contracts.
5. **Logging**: Logs actions and errors to `api_class.log`.

## Requirements

- Python 3.x
- Flask
- Flask-Mail
- Requests
- Utopia and PowerCode Python modules (custom imports)

## Setup

1. Install dependencies:
   pip install flask flask-mail requests
2. Configure the following constants in config.py:
PC_API_KEY: PowerCode API key.
PC_URL: PowerCode base URL.
3. Make sure to have the following email-related constants configured:
MAIL_SERVER = 'theglobal-net.mail.protection.outlook.com'
MAIL_PORT = 25
EMAIL_SENDER = 'no-reply@theglobal.net'
EMAIL_RECIPIENTS = ['email1@domain.com', 'email2@domain.com']

## How to Run
1. Clone the repository and navigate to the directory.
2. Run the script:
python utopia_api_handler.py
3.The application will start on http://localhost:5050.

## API Endpoints
/api-callback: Accepts POST requests from Utopia containing customer order data.

## Service Plan Management
The system allows for flexible service plan assignment:

Utopia Plans: These are mapped in the service_plan_mapping dictionary based on the plan description.
Additional Plans: You can manually assign extra service plans using the additional_service_plan_mapping.

## Example Callback
When Utopia sends a "Project New Order" event, the following happens:

The customer is searched in PowerCode.
If the customer doesn't exist, they are created.
A service plan is assigned based on the order details.
An email is sent to notify about the customer creation.

## Logging
All API events and errors are logged to api_class.log for audit and troubleshooting.

## Error Handling
If there are errors in customer creation or service plan assignment, an email will be sent to the recipients specified with details of the issue.

## Editing Ticket Description & Deploying Changes

This guide will walk you through the process of editing the ticket description and deploying changes to the system.

### Steps:

#### 1. **Edit the Ticket Description on GitHub**
1. Navigate to the `ticket_descriptions` folder.
2. Edit the `new_desc.txt` file as needed.
3. Commit and push the changes to the repository.

#### 2. **Deploy the Changes on the Server**

After editing the ticket description, you need to pull the changes to the server and restart the service.

##### Steps to deploy:

1. **SSH into the server:**
   ```bash
   ssh your-username@your-server-ip

2. **Simply run deploy_changes_UAC.sh:**
   ```bash
   ./deploy_changes_UAC.sh
The output should indicate that the service is running. If there are any issues, review the logs for troubleshooting.


## Editing Constants & Deploying Changes

This guide explains how to update constants like emails, server names, or log file paths, and how to deploy those changes to the system.

### Steps:

#### 1. **Edit the Constants on GitHub**
1. Navigate to the repository and open `api_callback.py`.
2. Find and edit the relevant constants (e.g., `EMAIL_RECIPIENT`, `LOG_FILENAME`, `SERVER_IP`, etc.).
3. Commit and push your changes to the repository.

#### 2. **Deploy the Changes on the Server**

Once your changes are pushed, deploy them to the server.

##### Steps to deploy:

##### Steps to deploy:

1. **SSH into the server:**
   ```bash
   ssh your-username@your-server-ip

2. **Simply run deploy_changes_UAC.sh:**
   ```bash
   ./deploy_changes_UAC.sh
