"""
Configuration module for UAC-Utopia Account Creation
Loads all configuration from environment variables (.env file)
"""
import os
import warnings
import bcrypt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# GUI App Settings
# ============================================================================
ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASS_HASH = os.getenv('ADMIN_PASS_HASH')
# Legacy support: if ADMIN_PASS_HASH doesn't exist, use ADMIN_PASS (plaintext)
ADMIN_PASS = os.getenv('ADMIN_PASS') if not ADMIN_PASS_HASH else None
SECRET_KEY = os.getenv("SECRET_KEY")


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
PC_URL_UAPI = os.getenv('PC_URL_UAPI')
PC_addressRangev4 = int(os.getenv('PC_ADDRESS_RANGE_V4', '10228'))
PC_UAPI_USERNAME = os.getenv("PC_UAPI_USERNAME")
PC_UAPI_PASSWORD = os.getenv("PC_UAPI_PASSWORD")
PC_CUST_TAGS = os.getenv("PC_CUST_TAGS")


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
# Ticket Template Configuration
# ============================================================================
TICKET_TEMPLATE_DIR = os.getenv('TICKET_TEMPLATE_DIR', 'ticket_descriptions')
TICKET_TEMPLATE_FILE = os.getenv('TICKET_TEMPLATE_FILE', 'new_desc.txt')
TICKET_TEMPLATE_META_FILE = os.getenv('TICKET_TEMPLATE_META_FILE', 'new_desc.txt.meta.json')

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
        'PC_URL_UAPI',
        'PC_UAPI_USERNAME',
        'PC_UAPI_PASSWORD',
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


# ============================================================================
# Password Hashing Utilities
# ============================================================================
def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, password_hash):
    """Verify a password against a bcrypt hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def get_admin_password():
    """Get admin password (for backward compatibility with plaintext)"""
    return ADMIN_PASS if ADMIN_PASS else None


def check_admin_password(password):
    """Check if provided password matches admin credentials"""
    if ADMIN_PASS_HASH:
        # Use hashed password
        return verify_password(password, ADMIN_PASS_HASH)
    elif ADMIN_PASS:
        # Legacy plaintext comparison
        return password == ADMIN_PASS
    return False


# ============================================================================
# Configuration Management Functions
# ============================================================================
def get_config_dict():
    """Get all configuration values as a structured dictionary"""
    return {
        'flask': {
            'FLASK_HOST': FLASK_HOST,
            'FLASK_PORT': FLASK_PORT,
        },
        'email': {
            'MAIL_SERVER': MAIL_SERVER,
            'MAIL_PORT': MAIL_PORT,
            'EMAIL_SENDER': EMAIL_SENDER,
            'EMAIL_RECIPIENTS': ', '.join([email.strip() for email in EMAIL_RECIPIENTS]) if isinstance(EMAIL_RECIPIENTS, list) else EMAIL_RECIPIENTS,
        },
        'powercode': {
            'PC_API_KEY': PC_API_KEY,
            'PC_URL': PC_URL,
            'PC_URL_API': PC_URL_API,
            'PC_ADDRESS_RANGE_V4': PC_addressRangev4,
            'PC_VERIFY_SSL': PC_VERIFY_SSL,
            'SERVICE_PLAN_1GBPS_ID': SERVICE_PLAN_1GBPS_ID,
            'SERVICE_PLAN_250MBPS_ID': SERVICE_PLAN_250MBPS_ID,
            'SERVICE_PLAN_BOND_FEE_ID': SERVICE_PLAN_BOND_FEE_ID,
            'CUSTOMER_PORTAL_PASSWORD': CUSTOMER_PORTAL_PASSWORD,
        },
        'utopia': {
            'UTOPIA_API_KEY': UTOPIA_API_KEY,
        },
        'ticket_templates': {
            'TICKET_TEMPLATE_DIR': TICKET_TEMPLATE_DIR,
            'TICKET_TEMPLATE_FILE': TICKET_TEMPLATE_FILE,
            'TICKET_TEMPLATE_META_FILE': TICKET_TEMPLATE_META_FILE,
        },
        'logging': {
            'LOG_FILE': LOG_FILE,
        },
        'admin': {
            'ADMIN_USER': ADMIN_USER,
            'ADMIN_PASS': get_admin_password() or '',  # Show plaintext only if exists (legacy)
        }
    }


def update_config_file(updates):
    """
    Update .env file with new configuration values
    
    Args:
        updates: Dictionary of key-value pairs to update
        
    Returns:
        tuple: (updated_count, changes_list)
    """
    env_path = '.env'
    if not os.path.exists(env_path):
        raise FileNotFoundError('.env file not found')
    
    # Read current .env contents
    with open(env_path, 'r', encoding='utf-8') as f:
        env_lines = f.readlines()
    
    # Create a dictionary of current values
    env_dict = {}
    for line in env_lines:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_dict[key.strip()] = value.strip()
    
    # Only update values that have actually changed
    updated_count = 0
    changes = []
    for key, new_value in updates.items():
        # Special handling for ADMIN_PASS - hash it and store as ADMIN_PASS_HASH
        if key == 'ADMIN_PASS' and new_value:
            new_hash = hash_password(new_value)
            
            # Remove old ADMIN_PASS if it exists (migrating to hashed version)
            if 'ADMIN_PASS' in env_dict:
                del env_dict['ADMIN_PASS']
            
            # Update or add ADMIN_PASS_HASH
            old_hash = env_dict.get('ADMIN_PASS_HASH', '')
            if old_hash != new_hash:
                env_dict['ADMIN_PASS_HASH'] = new_hash
                updated_count += 1
                changes.append(f"ADMIN_PASS_HASH: Password updated (hashed)")
        elif key in env_dict:
            old_value = env_dict[key]
            new_value_str = str(new_value)
            
            # Only update if value has changed
            if old_value != new_value_str:
                env_dict[key] = new_value_str
                updated_count += 1
                changes.append(f"{key}: '{old_value}' -> '{new_value_str}'")
    
    # Only write to file if there were actual changes
    if updated_count > 0:
        with open(env_path, 'w', encoding='utf-8') as f:
            for key, value in env_dict.items():
                f.write(f"{key}={value}\n")
    
    return updated_count, changes


def reload_config():
    """Reload configuration from .env file and update module variables"""
    import importlib
    import sys
    
    # Reload environment variables
    load_dotenv(override=True)
    
    # Get reference to this module
    current_module = sys.modules[__name__]
    
    # Reload this module
    importlib.reload(current_module)
    
    return True
