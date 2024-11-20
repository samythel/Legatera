from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from legatera import create_app

app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5002)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )
