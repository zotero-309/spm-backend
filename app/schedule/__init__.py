# app/user/__init__.py
from flask import Blueprint

# Initialize the blueprint (import to schedule.py)
schedule_blueprint = Blueprint('schedule', __name__)