# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# import pandas as pd

# app = Flask(__name__)

# # MySQL connection details
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://spmwfh:Password123_@spmwfh123.c1mimsiy0o6r.us-east-1.rds.amazonaws.com:3306/wfh'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # Initialize SQLAlchemy
# db = SQLAlchemy(app)

# # Define the Employee model
# class Employee(db.Model):
#     __tablename__ = 'employee'

#     staff_id = db.Column(db.Integer, primary_key=True)
#     staff_fname = db.Column(db.String(255), nullable=False)
#     staff_lname = db.Column(db.String(255), nullable=False)
#     dept = db.Column(db.String(255))
#     position = db.Column(db.String(255))
#     country = db.Column(db.String(255))
#     email = db.Column(db.String(255), unique=True)
#     reporting_manager = db.Column(db.Integer, db.ForeignKey('employee.staff_id'), nullable=True)  # Allow nulls
#     role = db.Column(db.Integer)

# # Load the CSV file into a pandas DataFrame
# df = pd.read_csv('employeenew.csv')

# # Clean column names by stripping whitespace (just in case)
# df.columns = df.columns.str.strip()

# with app.app_context():
#     # Step 1: Insert all employees without reporting_manager
#     for index, row in df.iterrows():
#         # Create a new Employee object for each row
#         new_employee = Employee(
#             staff_id=row['Staff_ID'],
#             staff_fname=row['Staff_FName'],
#             staff_lname=row['Staff_LName'],
#             dept=row['Dept'],
#             position=row['Position'],
#             country=row['Country'],
#             email=row['Email'],
#             reporting_manager=None,  # Initially set to None
#             role=row['Role']
#         )

#         # Add the new employee to the session
#         db.session.add(new_employee)

#     # Commit all the new employee records to the database
#     db.session.commit()

#     # Step 2: Update reporting_manager for each employee
#     for index, row in df.iterrows():
#         # Find the employee by staff_id
#         employee = Employee.query.get(row['Staff_ID'])
#         if employee:
#             # Check if the reporting manager ID is not null
#             reporting_manager_id = row['Reporting_Manager']
#             if pd.notna(reporting_manager_id):  # Ensure it's not NaN
#                 # Verify that the reporting manager exists
#                 reporting_manager = Employee.query.get(reporting_manager_id)
#                 if reporting_manager:  # If the manager exists, update it
#                     employee.reporting_manager = reporting_manager_id

#     # Commit the updates to the database
#     db.session.commit()

# print("Data inserted and reporting managers updated successfully!")
import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://udicfm3ei7jpyfx8:h2rq5GfSphPYr7x7gDUJ@bezufa1rhnyqaefkvkqo-mysql.services.clever-cloud.com:3306/bezufa1rhnyqaefkvkqo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Load the CSV file into a pandas DataFrame
df = pd.read_csv('employeenew.csv')

# Update the reporting_manager field for each employee
with app.app_context():  # Ensure operations are within the app context
    for index, row in df.iterrows():
        staff_id = row['Staff_ID']
        reporting_manager = row['Reporting_Manager']

        # Prepare the update statement
        update_statement = text(
            """
            UPDATE employee
            SET reporting_manager = :reporting_manager
            WHERE staff_id = :staff_id
            """
        )

        # Execute the update statement
        db.session.execute(update_statement, {'reporting_manager': reporting_manager, 'staff_id': staff_id})

        db.session.commit()  # Commit all updates


print("Reporting managers updated successfully!")
