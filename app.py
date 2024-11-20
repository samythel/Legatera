from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from legatera import create_app

app = create_app()
