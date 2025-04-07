import unittest
from flask import Flask, jsonify
from unittest.mock import patch
from app import create_app, db
from app.models import Employee, Login
from sqlalchemy.exc import SQLAlchemyError, OperationalError

class TestStaffLogin(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Set up the test client and in-memory database
        self.app = create_app(test_config=True)
        self.client = self.app.test_client()

        # Push the application context and initialize the database
        with self.app.app_context():
            db.create_all()  # Create tables for the test
            # self.run_sql_script('../BackEnd/db_prep/schemaTest.sql')  # Run SQL script //13/10 added ../
            self.populate_test_data(self)  # Populate some initial test data if needed


    @classmethod
    def tearDownClass(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def populate_test_data(self):
        # Clear existing data
        db.session.query(Login).delete()
        db.session.query(Employee).delete()
        db.session.commit()

        # Create one sample employee
        employee = Employee(
            staff_id=140736,
            staff_fname='William',
            staff_lname='Fu',
            dept='Sales',
            position='',
            country='Singapore',
            email='Williamfu@gamil.com',
            reporting_manager=None,
            role=2
        )

        # Add the employee to the session
        db.session.add(employee)

        # Create corresponding login record for the employee
        login = Login(
            username='salesstaff',
            password='salesstaff',
            staff_id=140736
        )

        # Add login record to the session
        db.session.add(login)

        # Commit changes to the database
        db.session.commit()

    def test_successful_login(self):
        # Test successful login with valid credentials
        response = self.client.post('api/staff/login', json={
            'username': 'salesstaff',
            'password': 'salesstaff'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['data']['staff_id'], 140736)
        self.assertEqual(response.json['data']['role'], 2)

    def test_missing_json_data(self):
        # Send request without JSON data
        response = self.client.post('api/staff/login', json=False)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], "JSON data passed from client side is insufficient")

    def test_invalid_credentials(self):
        # Test login attempt with invalid credentials
        response = self.client.post('api/staff/login', json={
            'username': 'salesstaff',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'No such staff credentials is found')

    @patch.object(db.session, 'query')
    def test_connection_error(self, mock_query):
        # Simulate an OperationalError in the database connection
        mock_query.side_effect = OperationalError("DB Connection Error", None, None)

        response = self.client.post('/api/staff/login', json={
            'username': 'salesstaff',
            'password': 'salesstaff'
        })
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Database connection issue.')

    @patch.object(db.session, 'query')
    def test_generic_exception(self, mock_query):
        # Simulate a generic exception
        mock_query.side_effect = Exception("Unexpected error")

        response = self.client.post('/api/staff/login', json={
            'username': 'salesstaff',
            'password': 'salesstaff'
        })

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'An unexpected error occurred.')

    @patch.object(db.session, 'query')
    def test_sqlalchemy_error(self, mock_query):
        # Simulate a SQLAlchemyError to test database query error handling
        mock_query.side_effect = SQLAlchemyError("Simulated Database Query Error")

        # Patch rollback to ensure that it is called during SQLAlchemyError
        response = self.client.post('/api/staff/login', json={
                'username': 'salesstaff',
                'password': 'salesstaff'
        })

        # Validate response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Database query failed.')
    
# Run the tests
if __name__ == '__main__':
    unittest.main()
