from datetime import datetime, timedelta
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text
from app import create_app, db
from app.models import Employee, WFHApplication, WFHSchedule, WFHWithdrawal


class TestWFHWithdrawal(unittest.TestCase):
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
        try:
            # Create employee instances
            employees = [
                Employee(staff_id=130002, staff_fname='Jack', staff_lname='Sim', dept='CEO', position='MD', country='Singapore', email='jack.sim@allinone.com.sg', reporting_manager=130002, role=1),
                Employee(staff_id=140001, staff_fname='Derek', staff_lname='Tan', dept='Sales', position='Director', country='Singapore', email='Derek.Tan@allinone.com.sg', reporting_manager=130002, role=1),
                Employee(staff_id=150008, staff_fname='Eric', staff_lname='Loh', dept='Solutioning', position='Director', country='Singapore', email='Eric.Loh@allinone.com.sg', reporting_manager=130002, role=1),
                Employee(staff_id=151408, staff_fname='Philip', staff_lname='Lee', dept='Engineering', position='Director', country='Singapore', email='Philip.Lee@allinone.com.sg', reporting_manager=130002, role=1),
                Employee(staff_id=140894, staff_fname='Rahim', staff_lname='Khalid', dept='Sales', position='Sales Manager', country='Singapore', email='Rahim.Khalid@allinone.com.sg', reporting_manager=140001, role=3)
            ]


            # Insert employees into the database
            db.session.add_all(employees)
            db.session.commit()  # Commit to get IDs for applications

            today = datetime.now().date()
            wfh_dates = [
                today + timedelta(days=1),   # Tomorrow
                today + timedelta(days=2),   # Day after tomorrow
                today - timedelta(days=30),  # 30 days ago
                today - timedelta(days=20),  # 20 days ago
                today - timedelta(days=19),  # 19 days ago
                today + timedelta(days=29),  # In 29 days
                today + timedelta(days=3),   # In 3 days
                today + timedelta(days=10),  # In 10 days
                today + timedelta(days=4),   # In 4 days
            ]

                        
            # Create WFH applications
            applications = [
                WFHApplication(staff_id=140894, time_slot='AM', staff_apply_reason='Working from home due to personal reasons', manager_reject_reason=None),
                WFHApplication(staff_id=140894, time_slot='FULL', staff_apply_reason='Health reasons', manager_reject_reason=None),
                WFHApplication(staff_id=140894, time_slot='PM', staff_apply_reason='Scheduled appointment', manager_reject_reason=None),
                WFHApplication(staff_id=140894, time_slot='AM', staff_apply_reason='Family matters', manager_reject_reason=None),
                WFHApplication(staff_id=140894, time_slot='AM', staff_apply_reason='Urgent family commitment', manager_reject_reason='Manager declined due to team meeting'),
                WFHApplication(staff_id=140894, time_slot='AM', staff_apply_reason='Childcare issues', manager_reject_reason=None),
                WFHApplication(staff_id=140894, time_slot='AM', staff_apply_reason='Issues', manager_reject_reason=None),
                WFHApplication(staff_id=151408, time_slot='AM', staff_apply_reason='Working from home due to personal reasons', manager_reject_reason=None),
                WFHApplication(staff_id=140894, time_slot='PM', staff_apply_reason='Working from home due to personal reasons', manager_reject_reason=None),
            ]

            db.session.add_all(applications)
            db.session.commit()  # Commit to generate application IDs


            schedules = [
                WFHSchedule(application_id=applications[0].application_id, wfh_date=wfh_dates[0], status='Pending_Approval', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[1].application_id, wfh_date=wfh_dates[1], status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[2].application_id, wfh_date=wfh_dates[2], status='Pending_Withdrawal', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[3].application_id, wfh_date=wfh_dates[3], status='Withdrawn', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[4].application_id, wfh_date=wfh_dates[4], status='Rejected', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[5].application_id, wfh_date=wfh_dates[5], status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[6].application_id, wfh_date=wfh_dates[6], status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[6].application_id, wfh_date=wfh_dates[7], status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[7].application_id, wfh_date=wfh_dates[0], status='Withdrawn', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[8].application_id, wfh_date=wfh_dates[8], status='Pending_Approval', manager_withdraw_reason=None),
            ]
            db.session.add_all(schedules)
            db.session.commit()  # Final commit to save schedules

            withdrawns =[
                WFHWithdrawal(wfh_id = schedules[2].wfh_id, staff_withdraw_reason='test'),
                WFHWithdrawal(wfh_id = schedules[3].wfh_id, staff_withdraw_reason='test')
            ]
            db.session.add_all(withdrawns)
            db.session.commit()  # Final commit to save schedules
        except Exception as e:
            db.session.rollback()
            raise e



    # Test Case 1: Withdrawal application status "Approved"
    def test_withdrawal_approved(self):
        
        date = (datetime.now().date() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/withdraw/140894', 
    json={
        "time_slot": "FULL",
        "staff_withdraw_reason": "having a meeting",
        "date": date,
        "status": "Approved"
    }, headers={"Content-Type": "application/json"})

        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Sending Manager for Approval'})

    # Test Case 2: Withdrawal application status "Pending_Approval"
    def test_withdrawal_pending_approval(self):
        date = (datetime.now().date() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/withdraw/140894',
            json={
                "time_slot": "AM",
                "staff_withdraw_reason": "having a meeting",
                "date": date,
                "status": "Pending_Approval"
            }, headers={"Content-Type": "application/json"})
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Application Success!'})

    # Test Case 3: Withdrawal application status "Pending_Withdrawal"
    def test_withdrawal_different_status(self):
        date = (datetime.now().date() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/withdraw/151408',
            json={
                "time_slot": "AM",
                "staff_withdraw_reason": "having a meeting",
                "date": date,
                "status": "Withdrawn"
            }, headers={"Content-Type": "application/json"})
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json,{"error": "JSON data passed from client side is insufficient or wrong"})

    # Test Case 4: Withdrawal application status "Withdrawn"
    @patch.object(db.session, 'query')
    def test_withdrawal_wfh_unexpected_error(self, mock_commit):
        # Simulate raising a generic exception
        mock_commit.side_effect = Exception('Something went wrong')

        # Prepare the request data
        mock_request_data = {
            "time_slot": "AM",
            "staff_withdraw_reason": "No longer needed",
            "date": "2024-10-16T08:00:00.000Z",
            "status": "Approved"
        }

        # Send the POST request to the withdrawal endpoint
        response = self.client.post(
            '/api/application/withdraw/140736',
            json=mock_request_data,
            content_type='application/json'
        )

        # Check that the response contains the correct status code and message
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'An unexpected error occurred.', response.data)



    # Test Case 5 :test_wrong_staff_id
    def test_wrong_staff_id(self):
        response = self.client.post('api/application/withdraw/1', json={
                "time_slot": "AM",
                "staff_withdraw_reason": "having a meeting",
                "date": "2024-10-18T00:00:00.000000Z",
                "status": "Pending_Approval"
            }, headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {"error": "JSON data passed from client side is insufficient or wrong"})

    # Test Case 6: Withdrawal of application that more than 2 week ago
    def test_withdrawal_more_than_two_weeks_ago(self):
        date = (datetime.now().date() + timedelta(days=29)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/withdraw/140894',
            json={
                "time_slot": "AM",
                "staff_withdraw_reason": "having a meeting",
                "date": date,
                "status": "Approved"
            }, headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'failed': 'cannot withdraw!'})

    # Test Case 7: Withdrawal application status "Approved"
    def test_withdrawal_approved_recurring(self):
        date = (datetime.now().date() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        response = self.client.post('api/application/withdraw/140894', 
    json={
        "time_slot": "AM",
        "staff_withdraw_reason": "having a meeting",
        "date": date,
        "status": "Approved"
    }, headers={"Content-Type": "application/json"})

        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Sending Manager for Approval'})
    

    # Test Case 8: test with invalid JSON
    def test_withdrawal_invalid_json(self):
        # Send invalid JSON (no data provided)
        response = self.client.post('api/application/withdraw/140736', json=False)

        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'JSON data passed from client side is insufficient', response.data)
    
    # Test Case 9: test for operational error
    @patch.object(db.session, 'query')
    def test_withdrawal_operational_error(self, mock_commit):
        # Simulate an OperationalError during the commit
        mock_commit.side_effect = OperationalError("DB Connection Error", None, None)

        # Mock request data
        mock_request_data = {
            "time_slot": "AM",
            "staff_withdraw_reason": "Some reason",
            "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
        response = self.client.post('api/application/withdraw/140736', json=mock_request_data)

        # Assertions
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Database connection issue.', response.data)
    
    # Test Case 10: test for sqlalchemy error
    @patch.object(db.session, 'query')
    def test_withdrawal_sqlalchemy_error(self, mock_commit):
        # Simulate a SQLAlchemyError during the commit
        mock_commit.side_effect = SQLAlchemyError("DB query failed")

        # Mock request data
        mock_request_data = {
            "time_slot": "AM",
            "staff_withdraw_reason": "Some reason",
            "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }

        response = self.client.post('api/application/withdraw/140736', json=mock_request_data)

        # Assertions
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Database query failed.', response.data)
    


if __name__ == '__main__':
    unittest.main()

