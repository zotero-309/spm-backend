# app/user/__init__.py
from flask import Blueprint

# Initialize the blueprint (import to schedule.py)
monitoring_blueprint = Blueprint('monitoring', __name__)