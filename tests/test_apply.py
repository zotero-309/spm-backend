import json
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import unittest
from unittest.mock import patch
from app import create_app, db
from app.models import WFHApplication, WFHSchedule, Employee
from sqlalchemy import text


class TestWFHApply(unittest.TestCase):

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

        # Add an employee with staff_id 140736, remove reporting manager
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

        new_employee = Employee(
            staff_id=130002,
            staff_fname='Jack',
            staff_lname='Sim',
            dept='CEO',
            position='MD',
            country='Singapore',
            email='jack.sim@allinone.com.sg',
            reporting_manager=None, 
            role=1
        )
        db.session.add(new_employee)
        db.session.commit()

        # Add an existing WFH application and schedule with 'Pending Approval' for AM slot on 4/10/2024
        test_application = WFHApplication(
            staff_id=140736,  # Same staff ID
            time_slot="AM",  # Same time slot to trigger conflict
            staff_apply_reason="Existing WFH"
        )
        db.session.add(test_application)
        db.session.flush()  # Flush to get the application_id for the next step

        # Add a schedule entry for 4/10/2024
        test_schedule = WFHSchedule(
            application_id=test_application.application_id,
            wfh_date="2024-10-04",
            status="Pending_Approval",  # The status that causes the conflict
            manager_withdraw_reason=None
        )
        db.session.add(test_schedule)
        db.session.commit()

    def test_apply_wfh1(self):
        # Send a request to the endpoint
        
        response = self.client.post('/api/application/apply/140736', json={
            "time_slot": "PM",
            "apply_reason": "Work from home",
            "start_date": "2024-10-10T00:00:00.000Z",
            "end_date": "2024-10-10T00:00:00.000Z"
        })
        print(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Application Success!', response.data)

    def test_apply_wfh(self):
        # Send a request to the endpoint
        
        response = self.client.post('/api/application/apply/140736', json={
            "time_slot": "AM",
            "apply_reason": "Work from home",
            "start_date": "2024-10-09T00:00:00.000Z",
            "end_date": "2024-10-09T00:00:00.000Z"
        })
        print(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Application Success!', response.data)

    def test_apply_wfhfull(self):
        # Send a request to the endpoint
        
        response = self.client.post('/api/application/apply/140736', json={
            "time_slot": "FULL",
            "apply_reason": "Work from home",
            "start_date": "2024-10-06T00:00:00.000Z",
            "end_date": "2024-10-06T00:00:00.000Z"
        })
        print(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Application Success!', response.data)

    def test_apply_wfhceo(self):
        # Send a request to the endpoint
        response = self.client.post('/api/application/apply/130002', json={
            "time_slot": "AM",
            "apply_reason": "Work from home",
            "start_date": "2024-10-11T00:00:00.000Z",
            "end_date": "2024-10-11T00:00:00.000Z"
        })
        print(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Application Success!', response.data)

    def test_apply_wfh_exist(self):
        # Send a request to the endpoint for the same staff ID and date as the existing application
        response = self.client.post('/api/application/apply/140736', json={
            "time_slot": "AM",  # Same time slot
            "apply_reason": "Work from home",
            "start_date": "2024-10-04T00:00:00.000Z",  # Conflicting date
            "end_date": "2024-10-04T00:00:00.000Z"
        })
        
        # Check that the response indicates a conflict (status code 400)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Application already exists!', response.data)

    # Test case 3: Error for missing JSON data in request
    def test_apply_wfh_no_json_data(self):
        response = self.client.post('/api/application/apply/140736', json=False, content_type='application/json')
        
        # Check for a 400 Bad Request response due to missing JSON
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'JSON data passed from client side is insufficient', response.data)

    # Test case 4: Database connection issue simulation (OperationalError)
    @patch.object(db.session, 'query')
    def test_apply_wfh_db_connection_error(self, mock_query):
        # Mocking an OperationalError during the commit
        mock_query.side_effect = OperationalError("DB Connection Error", None, None)

        mock_request_data = {
            "time_slot": "AM",
            "apply_reason": "Urgent matter",
            "start_date": "2024-10-14T08:00:00.000Z",
            "end_date": "2024-10-14T08:00:00.000Z"
        }
        
        response = self.client.post('/api/application/apply/140736', json=mock_request_data)
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Database connection issue.')

    # Test case 5: SQLAlchemy error handling test
    @patch.object(db.session, 'query')
    def test_display_wfh_request_sqlalchemy_error(self, mock_query):
        # Simulate an SQLAlchemyError
        mock_query.side_effect = SQLAlchemyError("Database query error")

        mock_request_data = {
            "time_slot": "AM",
            "apply_reason": "Urgent matter",
            "start_date": "2024-10-15T08:00:00.000Z",
            "end_date": "2024-10-15T08:00:00.000Z"
        }

        response = self.client.post('/api/application/apply/140736', json=mock_request_data)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {'error': 'Database query failed.'})


    # Test case 5: Unexpected error handling test
    @patch.object(db.session, 'query')
    def test_apply_wfh_unexpected_error(self, mock_commit):
        # Simulate an unexpected error (e.g., KeyError) during the process
        mock_commit.side_effect = KeyError("Unexpected error occurred")
        
        mock_request_data = {
            "time_slot": "AM",
            "apply_reason": "Family emergency",
            "start_date": "2024-10-15T08:00:00.000Z",
            "end_date": "2024-10-15T08:00:00.000Z"
        }
        
        response = self.client.post('/api/application/apply/140736', data=json.dumps(mock_request_data), content_type='application/json')
        
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'An unexpected error occurred', response.data)

    # Test case 6: Application with recurring dates (no conflicts)
    @patch.object(db.session, 'query')
    def test_apply_wfh_recurring_dates_success(self, mock_query):
        mock_request_data = {
            "time_slot": "AM",
            "apply_reason": "Regular WFH every week",
            "start_date": "2024-10-01T08:00:00.000Z",
            "end_date": "2024-10-31T08:00:00.000Z"
        }
        
        # Simulate no conflicting WFH applications for recurring dates
        mock_query().join().filter().count.return_value = 0
        
        response = self.client.post('/api/application/apply/140736', data=json.dumps(mock_request_data), content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Application Success!', response.data)

    # Test case 6: Application with recurring dates (no conflicts)
    def test_apply_wfh_recurring_dates_fail(self):

        mock_request_data = {
            "time_slot": "AM",
            "apply_reason": "Regular WFH every week",
            "start_date": "2024-10-16T08:00:00.000Z",
            "end_date": "2024-10-31T08:00:00.000Z"
        }
        
        # Simulate no conflicting WFH applications for recurring dates
        # mock_query().join().filter().count.return_value = 0
        
        response = self.client.post('/api/application/apply/140736', json=mock_request_data, content_type='application/json')

        mock_request_data_for_erorr = {
            "time_slot": "AM",
            "apply_reason": "Regular WFH every week",
            "start_date": "2024-10-16T08:00:00.000Z",
            "end_date": "2024-10-31T08:00:00.000Z"
        }
        response = self.client.post('/api/application/apply/140736', json=mock_request_data_for_erorr, content_type='application/json')
        


        
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Application already exists!', response.data)

    # Test case 7: Application with recurring dates (partial conflict)
    def test_apply_wfh_recurring_conflict(self):
        # Send a request to the endpoint for the same staff ID and date range as the existing application
        response = self.client.post('/api/application/apply/140736', json={
            "time_slot": "AM",  # Same time slot
            "apply_reason": "Recurring Work from home",
            "start_date": "2024-10-04T00:00:00.000Z",  # Conflicting date
            "end_date": "2024-10-18T00:00:00.000Z"  # Recurring every week (Fridays)
        })

        # Check that the response indicates a partial conflict (status code 400)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Application already exists on some recurring days!', response.data)
    
if __name__ == '__main__':
    unittest.main()