# Static variables for the Utopia Account Creation project
import os
import warnings
from dotenv import load_dotenv

# Load .env
load_dotenv()

#  Powercode
PC_URL = os.getenv('PC_URL')
PC_URL_Ticket = os.getenv('PC_URL_TICKET')
PC_addressRangev4 = 10228

# Utopia
# Utopia API main endpoint
URL_ENDPOINT = os.getenv('UTOPIA_URL_ENDPOINT')

# Utopia API Endpoints 
UTOPIA_Service_Lookup = '/spquery/service'
UTOPIA_Order_Lookup = '/spquery/orders'
UTOPIA_Customer_Lookup = '/spquery/customer'
UTOPIA_Contract_Lookup = '/spquery/contractlookup'
UTOPIA_Contract_Download = '/spquery/contractdownload'
UTOPIA_APView = "/spquery/apview"

# SSL Verification Settings
PC_VERIFY_SSL = os.getenv('PC_VERIFY_SSL', 'true').lower() == 'true'

# Email Configuration
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT', 25))
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',')

# Customer Portal Configuration
CUSTOMER_PORTAL_PASSWORD = os.getenv('CUSTOMER_PORTAL_PASSWORD')

# Logging conf
LOG_FILE = 'api_class.log'

# Validate critical configuration
if not all([PC_URL, PC_URL_Ticket, URL_ENDPOINT, MAIL_SERVER, EMAIL_SENDER, CUSTOMER_PORTAL_PASSWORD]):
    raise EnvironmentError('Missing required configuration in environment variables. Check your .env file.')

# Log warning if SSL verification is disabled
if not PC_VERIFY_SSL:
    warnings.warn("PowerCode SSL verification is DISABLED. This is a security risk!", RuntimeWarning)