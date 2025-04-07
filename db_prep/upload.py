from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)

# MySQL connection details
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:8889/wfh'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://spmwfh:Password123_@spmwfh123.c1mimsiy0o6r.us-east-1.rds.amazonaws.com:3306/wfh'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define the Employee model
class Employee(db.Model):

    __tablename__ = 'employee'

    staff_id = db.Column(db.Integer, primary_key=True)
    staff_fname = db.Column(db.String(255), nullable=False)
    staff_lname = db.Column(db.String(255), nullable=False)
    dept = db.Column(db.String(255))
    position = db.Column(db.String(255))
    country = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    reporting_manager = db.Column(db.Integer, db.ForeignKey('employee.staff_id'))
    role = db.Column(db.Integer)


# Load the Excel file into a pandas DataFrame
df = pd.read_csv('employeenew.csv')

with app.app_context():

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():

        reporting_manager_id = row.get('Reporting_Manager')

        # Check if the employee is reporting to themselves, if so, set reporting_manager to None
        if row['Staff_ID'] == reporting_manager_id:
            reporting_manager_id = None  # Employees cannot report to themselves

        # Create a new Employee object for each row
        new_employee = Employee(
            staff_id = row['Staff_ID'],
            staff_fname=row['Staff_FName'],
            staff_lname=row['Staff_LName'],
            dept=row['Dept'],
            position=row['Position'],
            country=row['Country'],
            email=row['Email'],
            reporting_manager=None,
            role= row['Role']
        )

        # Add the new employee to the session
        db.session.add(new_employee)

    # Commit all the new employee records to the database
    db.session.commit()

# Step 2: Create a new DataFrame with staff_id and reporting_manager
df_reporting_managers = df[['Staff_ID', 'Reporting_Manager']]


# Step 3: Update reporting_manager field for each employee
with app.app_context():
    for index, row in df_reporting_managers.iterrows():
        # Find the employee by staff_id
        employee = Employee.query.get(row['Staff_ID'])
        employee.reporting_manager = row['Reporting_Manager']
        db.session.commit()


print("Data inserted successfully!")