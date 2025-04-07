# app/user/__init__.py
from flask import Blueprint

# Initialize the blueprint (import to schedule.py)
application_blueprint = Blueprint('application', __name__)

from .application import auto_reject