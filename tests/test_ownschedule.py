import unittest
from flask import Flask, jsonify
from unittest.mock import patch
from app import create_app, db
from app.models import WFHApplication, WFHSchedule, WFHWithdrawal, Employee  # Import your models
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text
from datetime import datetime

class TestOwnSchedule(unittest.TestCase):


    @classmethod
    def setUpClass(self):
            # Set up the test client
        self.app = create_app(True)
        self.client = self.app.test_client()

        # Push the application context
        self.app_context = self.app.app_context()
        self.app_context.push()  # Push the context to use throughout the test

        # Initialize the database schema
        db.create_all()  # Create all tables in the test database
        # self.run_sql_script('../BackEnd/db_prep/schemaTest.sql')  # Run SQL script

        # Create test data
        self.create_test_data(self)
    @classmethod
    def tearDownClass(self):
        # Clean up after each test
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

        # Pop the application context
        self.app_context.pop()

    def create_test_data(self):
        # Insert WFH applications and schedules into the database
        try:
            # Create new user
            # Add an employee with staff_id 140736, remove reporting manager
            new_employee = Employee(
                staff_id=140004,
                staff_fname='Mary',
                staff_lname='Teo',
                dept='Sales',
                position='Account Manager',
                country='Singapore',
                email='Mary.Teo@allinone.com.sg',
                reporting_manager=None, 
                role=2 
            )
            db.session.add(new_employee)
            db.session.commit()

            # AM WFH on 30/09/2024 (Pending Approval)
            app1 = WFHApplication(staff_id=140004, time_slot='AM', staff_apply_reason='test', manager_reject_reason=None)
            # Full day WFH on 4/10/2024 (Approved)
            app2 = WFHApplication(staff_id=140004, time_slot='FULL', staff_apply_reason='test', manager_reject_reason=None)
            # PM WFH on 3/10/2024 (Pending Withdrawal)
            app3 = WFHApplication(staff_id=140004, time_slot='PM', staff_apply_reason='test', manager_reject_reason=None)
            # AM WFH on 2/10/2024 (Withdrawn)
            app4 = WFHApplication(staff_id=140004, time_slot='AM', staff_apply_reason='test', manager_reject_reason=None)
            # AM WFH on 1/10/2024 (Rejected)
            app5 = WFHApplication(staff_id=140004, time_slot='AM', staff_apply_reason='test', manager_reject_reason='Manager declined')
            # AM WFH on 4/4/2024 (Approved)
            app6 = WFHApplication(staff_id=140004, time_slot='AM', staff_apply_reason='test', manager_reject_reason=None)

            # Add applications to the session and commit to the database
            db.session.add_all([app1, app2, app3, app4, app5, app6])
            db.session.commit()  # Commit the changes to generate the IDs

            # Create schedules using the IDs of the applications after commit

            # AM WFH on 30/09/2024 (Pending Approval)
            schedule1 = WFHSchedule(application_id=app1.application_id, wfh_date=datetime(2024, 9, 30), status='Pending_Approval', manager_withdraw_reason=None)
            # Full day WFH on 4/10/2024 (Approved)
            schedule2 = WFHSchedule(application_id=app2.application_id, wfh_date=datetime(2024, 10, 4), status='Approved',  manager_withdraw_reason=None)
            # PM WFH on 3/10/2024 (Pending Withdrawal)
            schedule3 = WFHSchedule(application_id=app3.application_id, wfh_date=datetime(2024, 10, 3), status='Pending_Withdrawal', manager_withdraw_reason=None)

            # AM WFH on 2/10/2024 (Withdrawn)
            schedule4 = WFHSchedule(application_id=app4.application_id, wfh_date=datetime(2024, 10, 2), status='Withdrawn', manager_withdraw_reason=None)
            

            # AM WFH on 1/10/2024 (Rejected)
            schedule5 = WFHSchedule(application_id=app5.application_id, wfh_date=datetime(2024, 10, 1), status='Rejected', manager_withdraw_reason=None)
            # AM WFH on 4/4/2024 (Approved)
            schedule6 = WFHSchedule(application_id=app6.application_id, wfh_date=datetime(2024, 4, 4), status='Approved', manager_withdraw_reason=None)

            # Add schedules to the session and commit
            db.session.add_all([schedule1, schedule2, schedule3, schedule4, schedule5, schedule6])
            db.session.flush()
            withdrawn1 = WFHWithdrawal(wfh_id = schedule3.wfh_id, staff_withdraw_reason='test')
            withdrawn2 = WFHWithdrawal(wfh_id = schedule4.wfh_id, staff_withdraw_reason='test')
            db.session.add_all([withdrawn1, withdrawn2])
            db.session.commit()  # Commit schedules
        except Exception as e:
            db.session.rollback()
            raise e

    def test_frontend_can_extract_staff_id(self):
        # Simulate API call with the test client
        response = self.client.get('/api/schedule/own/140004')

        # Print the actual JSON response for debugging
        print("API Response:", response.json)

        # Assert the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Expected data
        expected_data = [
            {
                'class': 'Pending_Approval',
                'dateEnd': '2024-09-30T13:00:00',
                'dateStart': '2024-09-30T09:00:00',
                'description': 'test',
                'label': 'AM'
            },
            {
                'class': 'Approved',
                'dateEnd': '2024-10-04T18:00:00',
                'dateStart': '2024-10-04T09:00:00',
                'description': 'test',
                'label': 'FULL'
            },
            {
                'class': 'Pending_Withdrawal',
                'dateEnd': '2024-10-03T18:00:00',
                'dateStart': '2024-10-03T14:00:00',
                'description': 'test',
                'label': 'PM'
            },
            {
                'class': 'Approved',
                'dateEnd': '2024-04-04T13:00:00',
                'dateStart': '2024-04-04T09:00:00',
                'description': 'test',
                'label': 'AM'
            }
        ]

        # Extract the actual data from the response
        actual_data = response.json

        # Sort both lists based on a unique key, like 'dateStart' or a combination of fields
        actual_data_sorted = sorted(actual_data, key=lambda x: (x['dateStart'], x['class']))
        expected_data_sorted = sorted(expected_data, key=lambda x: (x['dateStart'], x['class']))
        print("Actual Data:", actual_data_sorted)
        print("Expected Data:", expected_data_sorted)

        # Assert that the actual data matches the expected data
        self.assertEqual(actual_data_sorted, expected_data_sorted)

    @patch.object(db.session, 'query')
    def test_connection_error(self, mock_query):
        # Simulate an OperationalError in the database connection
        mock_query.side_effect = OperationalError("DB Connection Error", None, None)

        response = self.client.get('/api/schedule/own/140004')
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Database connection issue.')

    @patch.object(db.session, 'query')
    def test_generic_exception(self, mock_query):
        # Simulate a generic exception
        mock_query.side_effect = Exception("Unexpected error")

        response = self.client.get('/api/schedule/own/140004')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'An unexpected error occurred.')

    @patch.object(db.session, 'query')
    def test_sqlalchemy_error(self, mock_query):
        # Simulate a SQLAlchemyError to test database query error handling
        mock_query.side_effect = SQLAlchemyError("Simulated Database Query Error")

        # Patch rollback to ensure that it is called during SQLAlchemyError
        response = self.client.get('/api/schedule/own/140004')

        # Validate response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Database query failed.')

if __name__ == '__main__':
    unittest.main()