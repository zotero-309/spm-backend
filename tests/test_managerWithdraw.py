import unittest
from unittest.mock import patch
from app import create_app, db
from app.models import WFHApplication, WFHSchedule, Employee
from sqlalchemy import text
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.exc import SQLAlchemyError, OperationalError

class WFHManagerWithdraw(unittest.TestCase):

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
        # Add an employee with staff_id 140736
        new_employee = Employee(
            staff_id=140736,
            staff_fname='William',
            staff_lname='Fu',
            dept='Sales',
            position='Account Manager',
            country='Singapore',
            email='William.Fu@allinone.com.sg',
            reporting_manager=None, 
            role=2 
        )
        db.session.add(new_employee)
        db.session.commit()

        # Define today’s date
        today_date = datetime.now()

        # 1. Create a WFH application and schedule within 3 months forward and 1 month backward from today
        wfh_within_date_range_application = WFHApplication(
            staff_id=140736,
            time_slot="AM",
            staff_apply_reason="Medical emergency"
        )
        db.session.add(wfh_within_date_range_application)
        db.session.flush()  # Flush to get the application_id

        # Approved WFH date within 3 months forward (use today - 2 months)
        within_forward_date = today_date - relativedelta(months=2)
        test_schedule_within_forward = WFHSchedule(
            application_id=wfh_within_date_range_application.application_id,
            wfh_date=within_forward_date.date(),  # Format as date
            status="Approved",  # Approved status
            manager_withdraw_reason=None
        )
        db.session.add(test_schedule_within_forward)

        # Approved WFH date within 1 month backward (use today + 2 weeks)
        within_backward_date = today_date + relativedelta(weeks=2)
        test_schedule_within_backward = WFHSchedule(
            application_id=wfh_within_date_range_application.application_id,
            wfh_date=within_backward_date.date(),  # Format as date
            status="Approved",  # Approved status
            manager_withdraw_reason=None
        )
        db.session.add(test_schedule_within_backward)

        # 2. Create a WFH application and schedule for a date outside the 3-month forward range (today + 4 months)
        wfh_outside_forward_application = WFHApplication(
            staff_id=140736,
            time_slot="AM",
            staff_apply_reason="Outside 3 months forward WFH",
            manager_reject_reason=None
        )
        db.session.add(wfh_outside_forward_application)
        db.session.flush()

        outside_forward_date = today_date - relativedelta(months=4)  # Beyond 3 months forward
        test_schedule_outside_forward = WFHSchedule(
            application_id=wfh_outside_forward_application.application_id,
            wfh_date=outside_forward_date.date(),
            status="Approved",
            manager_withdraw_reason=None
        )
        db.session.add(test_schedule_outside_forward)

        # 3. Create a WFH application and schedule for a date outside the 1-month backward range (today - 2 months)
        wfh_outside_backward_application = WFHApplication(
            staff_id=140736,
            time_slot="AM",
            staff_apply_reason="Outside 1 month backward WFH"
        )
        db.session.add(wfh_outside_backward_application)
        db.session.flush()

        outside_backward_date = today_date + relativedelta(months=2)  # Beyond 1 month backward
        test_schedule_outside_backward = WFHSchedule(
            application_id=wfh_outside_backward_application.application_id,
            wfh_date=outside_backward_date.date(),
            status="Approved",
            manager_withdraw_reason=None
        )
        db.session.add(test_schedule_outside_backward)

        # 4. Create a WFH application and schedule for a date within the required date range but contains FULL in its status
        wfh_status_full_application = WFHApplication(
            staff_id=140736,
            time_slot="FULL",
            staff_apply_reason="Testing FULL status"
        )
        db.session.add(wfh_status_full_application)
        db.session.flush()

        wfh_status_full_date = today_date + relativedelta(weeks=3)  # Beyond 1 month backward
        test_schedule_status_full = WFHSchedule(
            application_id=wfh_status_full_application.application_id,
            wfh_date=wfh_status_full_date.date(),
            status="Approved",
            manager_withdraw_reason=None
        )
        db.session.add(test_schedule_status_full)

        # Final commit to the database
        db.session.commit()


    def test_wfh_arrangement_does_not_exist(self):
        # Get the current date and add one week (not inside the setup test db recs)
        wfh_no_exist = datetime.now() + relativedelta(weeks=1)
        formatted_test_date = wfh_no_exist.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        response = self.client.post('api/application/manager_withdraw/140736', json={
            "time_slot": "AM",
            "manager_withdraw_reason": "Urgent Product Release Meeting",
            "date": formatted_test_date  # Use the dynamically generated date
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['failed'] , 'No approved arrangement found!')

    def test_manager_withdraw_within_1_months_backward(self):
        # Get the current date and subtracts 2 weeks back (inside the setup test db recs)
        wfh_within_date_range = datetime.now() + relativedelta(weeks=2)
        formatted_test_date = wfh_within_date_range.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        response = self.client.post('api/application/manager_withdraw/140736', json={
            "time_slot": "AM",
            "manager_withdraw_reason": "Urgent Product Release Meeting",
            "date": formatted_test_date  # Use the dynamically generated date
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['success'] , 'Successful Withdrawal!')

    def test_manager_withdraw_within_3_months_forward(self):
        # Get the current date and add 2 months forward (inside the setup test db recs)
        wfh_within_date_range = datetime.now() - relativedelta(months=2)
        formatted_test_date = wfh_within_date_range.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        response = self.client.post('api/application/manager_withdraw/140736', json={
            "time_slot": "AM",
            "manager_withdraw_reason": "Urgent Product Release Meeting",
            "date": formatted_test_date  # Use the dynamically generated date
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['success'] , 'Successful Withdrawal!')


    def test_manager_withdraw_outside_3_months_after(self):
        # Get the current date and add 4 months forward (inside the setup test db recs)
        wfh_outside_date_range = datetime.now() - relativedelta(months=4)
        formatted_test_date = wfh_outside_date_range.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/manager_withdraw/140736', json={
            "time_slot": "AM",
            "manager_withdraw_reason": "Urgent Product Release Meeting",
            "date": formatted_test_date
        })
        print(response.json)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['failed'] , 'Approved arrangement is more than 3 months forward or 1 month backward!')

    def test_manager_withdraw_outside_1_month_before(self):
        # Get the current date and subtract 2 months backward (inside the setup test db recs)
        wfh_outside_date_range = datetime.now() + relativedelta(months=2)
        formatted_test_date = wfh_outside_date_range.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/manager_withdraw/140736', json={
            "time_slot": "AM",
            "manager_withdraw_reason": "Urgent Product Release Meeting",
            "date": formatted_test_date
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['failed'] , 'Approved arrangement is more than 3 months forward or 1 month backward!')

    def test_manager_withdraw_full_status(self):
        # Get the current date and subtract 2 months backward (inside the setup test db recs)
        wfh_within_date_range = datetime.now() + relativedelta(weeks=3)
        formatted_test_date = wfh_within_date_range.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/manager_withdraw/140736', json={
            "time_slot": "AM",
            "manager_withdraw_reason": "Urgent Product Release Meeting",
            "date": formatted_test_date
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['success'] , 'Successful Withdrawal!')

    # Test case: Unexpected error handling test
    @patch.object(db.session, 'query')
    def test_approve_or_reject_unexpected_error(self, mock_commit):
        # Simulate an unexpected error (e.g., KeyError) during the process
        mock_commit.side_effect = KeyError("Unexpected error occurred")
        
        wfh_within_date_range = datetime.now() + relativedelta(weeks=3)
        formatted_test_date = wfh_within_date_range.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/manager_withdraw/140736', json={
            "time_slot": "AM",
            "manager_withdraw_reason": "Urgent Product Release Meeting",
            "date": formatted_test_date
        })
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'An unexpected error occurred', response.data)
    

    # Test case: Database connection issue simulation (OperationalError)
    @patch.object(db.session, 'query')
    def test_approve_or_reject_db_connection_error(self, mock_query):
        # Mocking an OperationalError during the commit
        mock_query.side_effect = OperationalError("DB Connection Error", None, None)

        wfh_within_date_range = datetime.now() + relativedelta(weeks=3)
        formatted_test_date = wfh_within_date_range.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/manager_withdraw/140736', json={
            "time_slot": "AM",
            "manager_withdraw_reason": "Urgent Product Release Meeting",
            "date": formatted_test_date
        })
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Database connection issue.')

    # Test case : SQLAlchemy error handling test
    @patch.object(db.session, 'query')
    def test_display_approve_or_reject_sqlalchemy_error(self, mock_query):
        # Simulate an SQLAlchemyError
        mock_query.side_effect = SQLAlchemyError("Database query error")

        wfh_within_date_range = datetime.now() + relativedelta(weeks=3)
        formatted_test_date = wfh_within_date_range.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/manager_withdraw/140736', json={
            "time_slot": "AM",
            "manager_withdraw_reason": "Urgent Product Release Meeting",
            "date": formatted_test_date
        })

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {'error': 'Database query failed.'})
    
    # Test case : Error for missing JSON data in request
    def test_apply_wfh_no_json_data(self):
        response = self.client.post('/api/application/manager_withdraw/140736', json=False, content_type='application/json')
        
        # Check for a 400 Bad Request response due to missing JSON
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'JSON data passed from client side is insufficient', response.data)


if __name__ == '__main__':
    unittest.main()