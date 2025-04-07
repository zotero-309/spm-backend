import unittest
from flask import Flask
# from BackEnd.app import create_app, db
# from BackEnd.config import Config
# from BackEnd.app.models import WFHApplication, WFHSchedule  # Import your models
from datetime import datetime

import sys
import os

# Add the BackEnd folder to the system path to import the modules needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../BackEnd')))

from app import create_app, db
from config import Config
from app.models import WFHApplication, WFHSchedule  # Import your models


class WFHApplicationIntegrationTestCase(unittest.TestCase):

    def create_app(self):
        # Create a Flask app instance for testing
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
        return app

    def setUp(self):
        # Set up the test client
        self.app = self.create_app()
        self.client = self.app.test_client()

        # Push an application context to use the database
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create test data
        self.create_test_data()

    def tearDown(self):
        # Remove test data
        self.delete_test_data()

        # Pop the application context
        self.app_context.pop()

    def create_test_data(self):
        # Insert WFH applications and schedules into the database
        try:

            # AM WFH on 30/09/2024 (Pending Approval)
            app1 = WFHApplication(staff_id=140004, time_slot='AM', staff_apply_reason='test', manager_reject_reason=None)
            # Full day WFH on 4/10/2024 (Accepted)
            app2 = WFHApplication(staff_id=140004, time_slot='FULL', staff_apply_reason='test', manager_reject_reason=None)
            # PM WFH on 3/10/2024 (Pending Withdrawal)
            app3 = WFHApplication(staff_id=140004, time_slot='PM', staff_apply_reason='test', manager_reject_reason=None)
            # AM WFH on 2/10/2024 (Withdrawn)
            app4 = WFHApplication(staff_id=140004, time_slot='AM', staff_apply_reason='test', manager_reject_reason=None)
            # AM WFH on 1/10/2024 (Rejected)
            app5 = WFHApplication(staff_id=140004, time_slot='AM', staff_apply_reason='test', manager_reject_reason='Manager declined')
            # AM WFH on 4/4/2024 (Accepted)
            app6 = WFHApplication(staff_id=140004, time_slot='AM', staff_apply_reason='test', manager_reject_reason=None)

            # Add applications to the session and commit to the database
            db.session.add_all([app1, app2, app3, app4, app5, app6])
            db.session.commit()  # Commit the changes to generate the IDs

            # Create schedules using the IDs of the applications after commit

            # AM WFH on 30/09/2024 (Pending Approval)
            schedule1 = WFHSchedule(application_id=app1.application_id, wfh_date=datetime(2024, 9, 30), status='Pending_Approval', staff_withdraw_reason=None, manager_withdraw_reason=None)
            # Full day WFH on 4/10/2024 (Accepted)
            schedule2 = WFHSchedule(application_id=app2.application_id, wfh_date=datetime(2024, 10, 4), status='Accepted', staff_withdraw_reason=None, manager_withdraw_reason=None)
            # PM WFH on 3/10/2024 (Pending Withdrawal)
            schedule3 = WFHSchedule(application_id=app3.application_id, wfh_date=datetime(2024, 10, 3), status='Pending_Withdrawal', staff_withdraw_reason='test', manager_withdraw_reason=None)

            # AM WFH on 2/10/2024 (Withdrawn)
            schedule4 = WFHSchedule(application_id=app4.application_id, wfh_date=datetime(2024, 10, 2), status='Withdrawn', staff_withdraw_reason='test', manager_withdraw_reason=None)
            # AM WFH on 1/10/2024 (Rejected)
            schedule5 = WFHSchedule(application_id=app5.application_id, wfh_date=datetime(2024, 10, 1), status='Rejected', staff_withdraw_reason=None, manager_withdraw_reason=None)
            # AM WFH on 4/4/2024 (Accepted)
            schedule6 = WFHSchedule(application_id=app6.application_id, wfh_date=datetime(2024, 4, 4), status='Accepted', staff_withdraw_reason=None, manager_withdraw_reason=None)

            # Add schedules to the session and commit
            db.session.add_all([schedule1, schedule2, schedule3, schedule4, schedule5, schedule6])
            db.session.commit()  # Commit schedules
        except Exception as e:
            db.session.rollback()
            raise e


    def delete_test_data(self):
        # Clean up the data after the test
        try:
            WFHApplication.query.filter_by(staff_id=140004).delete()
            db.session.commit()
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
                'class': 'Accepted',
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
                'class': 'Accepted',
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

if __name__ == '__main__':
    unittest.main()
