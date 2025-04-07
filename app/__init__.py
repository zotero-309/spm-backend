from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config, Testconfig
from flasgger import Swagger

# Initialize the database instance globally
db = SQLAlchemy()

# run.py run this function to initialise and run Flask app
def create_app(test_config=False):

    # Create the Flask app instance
    app = Flask(__name__)

    CORS(app, origins=["https://wfhscheduler.netlify.app"]) # CORS configuration --> allowing frontend vue to make request to flask backend

    # Initialize Flasgger
    swagger = Swagger(app)


    # If a custom configuration is passed, override the default config (for testing)
    if test_config:
        app.config.from_object(Testconfig)
    else:
        # Load app configuration
        app.config.from_object(Config)

    # Initialize extension with the app
    db.init_app(app)
    CORS(app) # CORS configuration --> allowing frontend vue to make request to flask backend

    # Import and register blueprints (modular routing)
    # when create a function e.g. schedule, create a folder and an empty init file to treat that folder as package

    # user login function
    from app.schedule.schedule import schedule_blueprint
    from app.application.application import application_blueprint
    from app.staff.staff import staff_blueprint
    app.register_blueprint(schedule_blueprint, url_prefix='/api/schedule') # how it routes to schedule_blueprint functions
    app.register_blueprint(application_blueprint, url_prefix='/api/application') # how it routes to application_blueprint functions
    app.register_blueprint(staff_blueprint, url_prefix='/api/staff') # how it routes to staff_blueprint functions
    return app
