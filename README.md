# Utopia API Handler

This Python project is designed to handle customer data integration between Utopia and PowerCode through an API. It processes orders from Utopia, searches for customers in PowerCode, and creates customer records in PowerCode if they do not exist. Additionally, it assigns service plans and sends notification emails.

## Features

1. **API Endpoint**: Handles incoming API callbacks from Utopia.
2. **Customer Management**: Searches for customers in PowerCode, creates new records if not found.
3. **Service Plan Assignment**: Adds appropriate service plans from Utopia and additional manual plans.
4. **Email Notifications**: Sends emails for success or failure.
5. **Logging**: Logs actions and errors to `api_class.log`.

## Requirements

- Python 3.x
- Flask
- Flask-Mail
- Requests
- python-dotenv
- Utopia and PowerCode Python modules (custom imports)

## Configuration Setup

### Environment Variables

This application uses environment variables for secure configuration management. **Never commit the `.env` file to version control!**

### Initial Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and fill in the actual values for your environment**

3. **Verify all required variables are set** (see table below)

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PC_API_KEY` | PowerCode API authentication key | `your_api_key_here` |
| `UTOPIA_API_KEY` | Utopia API authentication key | `your_api_key_here` |
| `PC_URL` | PowerCode base URL | `https://example.com` |
| `PC_URL_TICKET` | PowerCode ticket API endpoint | `https://example.com:444/api/1/index.php` |
| `UTOPIA_URL_ENDPOINT` | Utopia API base URL | `https://api.utopiafiber.com` |
| `MAIL_SERVER` | SMTP mail server | `MAIL SERVER` |
| `MAIL_PORT` | SMTP port | `25` |
| `EMAIL_SENDER` | From address for emails | `no-reply@theglobal.net` |
| `EMAIL_RECIPIENTS` | Comma-separated list of recipients | `email1@example.com,email2@example.com` |
| `CUSTOMER_PORTAL_PASSWORD` | Default customer portal password | `DEFAULT_PASSWORD` |
| `PC_VERIFY_SSL` | Enable SSL verification for PowerCode API | `false` (use `true` when certs are fixed) |

### Security Notes

- **Never commit `.env` to version control** - it contains sensitive credentials
- The `.env.example` file is safe to commit (it has no real secrets)
- Use strong passwords in production environments
- The `.gitignore` file is configured to prevent `.env` from being committed

### SSL Configuration

The application supports configurable SSL verification:
- Set `PC_VERIFY_SSL=true` to enable SSL verification (recommended when certificates are valid)
- Set `PC_VERIFY_SSL=false` to disable SSL verification (only if PowerCode has certificate issues)
- A warning will be logged when SSL verification is disabled

## Setup and Installation

1. **Clone the repository and navigate to the directory**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your actual credentials
   ```

4. **Verify configuration:**
   ```bash
   python -c "import config; print('Config loaded successfully')"
   ```
   You should see: `✓ All required environment variables loaded successfully`


## How to Run

### Development Mode

1. **Ensure `.env` file is configured** (see Configuration Setup above)

2. **Run the Flask application:**
   ```bash
   python api_callback.py
   ```

3. **The application will start on** `http://localhost:5050`

4. **You should see:**
   ```
   ✓ All required environment variables loaded successfully
   * Running on http://127.0.0.1:5050
   ```

**Note:** The "development server" warning is normal and expected for local testing.

### Production Deployment

For production deployment on Linux servers, use the deployment script:

```bash
./deploy_changes_UAC.sh
```

This will pull the latest changes and restart the service.

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


## Deployment Checklist

Before deploying to production:

- [ ] Copy `.env.example` to `.env`
- [ ] Fill in all required environment variables with actual values
- [ ] Test application startup locally (check for validation success message)
- [ ] Verify API endpoints work correctly
- [ ] Confirm email notifications are sent properly
- [ ] Check SSL certificate settings (`PC_VERIFY_SSL`)
- [ ] Review logs for any warnings or errors
- [ ] Ensure `.env` file is NOT committed to Git
- [ ] Update production server's `.env` file with production credentials

---

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

**IMPORTANT:** As of Phase 1 security improvements, constants are now managed via environment variables.

### Steps to Update Configuration:

#### 1. **Edit Environment Variables**

**For Development:**
1. Edit your local `.env` file
2. Update the relevant variable (e.g., `EMAIL_RECIPIENTS`, `MAIL_SERVER`, etc.)
3. Restart the application

**For Production:**
1. SSH into the server
2. Edit `/path/to/application/.env` file
3. Update the variable
4. Run the deployment script to restart the service

#### 2. **Deploy the Changes on the Server**

1. **SSH into the server:**
   ```bash
   ssh your-username@your-server-ip
   ```

2. **Run the deployment script:**
   ```bash
   ./deploy_changes_UAC.sh
   ```

**Note:** You no longer need to edit `config.py` or `static_vars.py` directly. All configuration is managed through the `.env` file for security and flexibility.

### Common Configuration Changes

| What to Change | Environment Variable | Example |
|----------------|---------------------|---------|
| Email recipients | `EMAIL_RECIPIENTS` | `user1@example.com,user2@example.com` |
| Email sender | `EMAIL_SENDER` | `noreply@yourdomain.com` |
| Mail server | `MAIL_SERVER` | `smtp.yourserver.com` |
| PowerCode API URL | `PC_URL` | `https://your-powercode-server.com` |
| Customer portal password | `CUSTOMER_PORTAL_PASSWORD` | `YourSecurePassword123` |

---

## Troubleshooting

### Application Won't Start

**Error: "Missing required environment variables"**
- Solution: Ensure all required variables are set in your `.env` file
- Check `.env.example` for the complete list
- Verify no typos in variable names

**Error: "No module named 'dotenv'"**
- Solution: Install python-dotenv: `pip install python-dotenv`

### SSL Certificate Errors

**Error: "SSL: CERTIFICATE_VERIFY_FAILED"**
- For PowerCode API: Set `PC_VERIFY_SSL=false` in `.env` (temporary workaround)
- Check that `PC_VERIFY_SSL` is set correctly

### Email Not Sending

- Verify `MAIL_SERVER` and `MAIL_PORT` are correct
- Check `EMAIL_SENDER` and `EMAIL_RECIPIENTS` format
- Ensure mail server allows connections from your IP
- Check application logs in `api_class.log`

### Configuration Not Loading

- Ensure `.env` file is in the same directory as `api_callback.py`
- Check file permissions on `.env`
- Verify `.env` file doesn't have a `.txt` extension
- Restart the application after changing `.env`

---
