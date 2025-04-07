from flask import jsonify, request
from app.staff import staff_blueprint  # Import the blueprint
from app import db
from app.models import Employee, WFHApplication, WFHSchedule, Login
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime


# Route to get staff related info
@staff_blueprint.route('/login', methods=['POST'])
def staff_login():
    try:
        json_data = request.get_json()
        if not json_data: # checks for first possible error
            return jsonify({"error": "JSON data passed from client side is insufficient"}), 400
        
        staff_rec = db.session.query(Login, Employee).join(Employee, Login.staff_id == Employee.staff_id).filter(
            Login.username == json_data["username"],
            Login.password == json_data["password"]
        ).first()

        if staff_rec:
            login_data, employee_data = staff_rec
            return_data = {
                "staff_id": login_data.staff_id,  # Assuming staff_id is in Employee
                "role": employee_data.role,          # Assuming role is in Employee
            }
            #situation where there is conflict for day request
            return jsonify({'data': return_data}), 200
        else: 
            #situation where some of scheduled wfh is already
            return jsonify({'error': 'No such staff credentials is found'}), 400
        
    except OperationalError as e:
        return jsonify({'error': 'Database connection issue.'}), 500

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    # Catch unexpected errors (everything else)
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred.'}), 500


