# app/user/__init__.py
from flask import Blueprint

# Initialize the blueprint (import to user.py)
staff_blueprint = Blueprint('staff', __name__)