import os
from dotenv import load_dotenv

# Load env veriables from .env file
load_dotenv()

PC_API_KEY = os.getenv("PC_API_KEY")
UTOPIA_API_KEY = os.getenv("UTOPIA_API_KEY")

if not PC_API_KEY:
    raise EnvironmentError("Powercode API Key not found in enviroment variables")
if not UTOPIA_API_KEY:
    raise EnvironmentError("Utopia API Key not found in enviroment variables")

def validate_config():
    """Validate that all required environment variables are present."""
    required_vars = [
        'PC_API_KEY',
        'UTOPIA_API_KEY',
        'PC_URL',
        'PC_URL_TICKET',
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
    
    print('✓ All required environment variables loaded successfully')
    return True

validate_config()