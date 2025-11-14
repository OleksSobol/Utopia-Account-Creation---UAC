"""
Configuration module for UAC-Utopia Account Creation
Loads all configuration from environment variables (.env file)
"""
import os
import warnings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# Flask App Settings
# ============================================================================
# Host/port for running the Flask app; can be overridden via environment.
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5050'))

# ============================================================================
# API Keys
# ============================================================================
PC_API_KEY = os.getenv("PC_API_KEY")
UTOPIA_API_KEY = os.getenv("UTOPIA_API_KEY")

# ============================================================================
# PowerCode Configuration
# ============================================================================
PC_URL = os.getenv('PC_URL')
PC_URL_API = os.getenv('PC_URL_API')
PC_addressRangev4 = int(os.getenv('PC_ADDRESS_RANGE_V4', '10228'))

# Service Plan IDs (PowerCode)
SERVICE_PLAN_1GBPS_ID = int(os.getenv('SERVICE_PLAN_1GBPS_ID', '164'))
SERVICE_PLAN_250MBPS_ID = int(os.getenv('SERVICE_PLAN_250MBPS_ID', '163'))
SERVICE_PLAN_BOND_FEE_ID = int(os.getenv('SERVICE_PLAN_BOND_FEE_ID', '172'))

# ============================================================================
# Utopia Configuration
# ============================================================================
URL_ENDPOINT = os.getenv('UTOPIA_URL_ENDPOINT')

# Utopia API Endpoints (URL paths)
UTOPIA_Service_Lookup = '/spquery/service'
UTOPIA_Order_Lookup = '/spquery/orders'
UTOPIA_Customer_Lookup = '/spquery/customer'
UTOPIA_Contract_Lookup = '/spquery/contractlookup'
UTOPIA_Contract_Download = '/spquery/contractdownload'
UTOPIA_APView = "/spquery/apview"

# ============================================================================
# SSL Verification Settings
# ============================================================================
PC_VERIFY_SSL = os.getenv('PC_VERIFY_SSL', 'true').lower() == 'true'

# ============================================================================
# Email Configuration
# ============================================================================
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT', 25))
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',')

# ============================================================================
# Customer Portal Configuration
# ============================================================================
CUSTOMER_PORTAL_PASSWORD = os.getenv('CUSTOMER_PORTAL_PASSWORD')

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_FILE = 'app_main.log'

# ============================================================================
# Configuration Validation
# ============================================================================
def validate_config():
    """Validate that all required environment variables are present."""
    required_vars = [
        'PC_API_KEY',
        'UTOPIA_API_KEY',
        'PC_URL',
        'PC_URL_API',
        'UTOPIA_URL_ENDPOINT',
        'MAIL_SERVER',
        'EMAIL_SENDER',
        'EMAIL_RECIPIENTS',
        'CUSTOMER_PORTAL_PASSWORD'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        raise EnvironmentError(
            f'Missing required environment variables: {", ".join(missing)}\n'
            f'Please check your .env file. See .env.example for reference.'
        )
    
    # Log warnings for SSL configuration
    if not PC_VERIFY_SSL:
        warnings.warn(
            "PowerCode SSL verification is DISABLED. This is a security risk!",
            RuntimeWarning
        )
    
    print('✓ All required environment variables loaded successfully')
    return True

# Validate configuration on module import
validate_config()
