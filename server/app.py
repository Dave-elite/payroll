from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

#Load enviroment variables
load_dotenv()

# initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, supports_credentials=True)

#configure database
database_url = os.environ.get('DATABASE_URL')
