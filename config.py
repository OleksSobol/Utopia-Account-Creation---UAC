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
