from datetime import date
import sys
import os
import unittest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from app import create_app, db
from app.models import Employee, WFHApplication, WFHSchedule, WFHWithdrawal

class TestWFHApproveRequests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Set up the test client and in-memory database
        self.app = create_app(test_config=True)
        self.client = self.app.test_client()

        # Push the application context and initialize the database
        with self.app.app_context():
            db.create_all()  # Create tables for the test
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
                Employee(staff_id=140894, staff_fname='Rahim', staff_lname='Khalid', dept='Sales', position='Sales Manager', country='Singapore', email='Rahim.Khalid@allinone.com.sg', reporting_manager=140001, role=3),

                Employee(staff_id=140878, staff_fname='James', staff_lname='Tong', dept='Sales', position='Account Manager', country='Singapore', email='James.Tong@allinone.com.sg', reporting_manager=140894, role=2),
                Employee(staff_id=140002, staff_fname='Susan', staff_lname='Goh', dept='Sales', position='Account Manager', country='Singapore', email='Susan.Goh@allinone.com.sg', reporting_manager=140894, role=2),
                Employee(staff_id=140015, staff_fname='Oliva', staff_lname='Lim', dept='Sales', position='Account Manager', country='Singapore', email='Oliva.Lim@allinone.com.sg', reporting_manager=140894, role=2),
                Employee(staff_id=140025, staff_fname='Emma', staff_lname='Heng', dept='Sales', position='Account Manager', country='Singapore', email='Emma.Heng@allinone.com.sg', reporting_manager=140894, role=2),

                # Employee(staff_id=150008, staff_fname='Eric', staff_lname='Loh', dept='Solutioning', position='Director', country='Singapore', email='Eric.Loh@allinone.com.sg', reporting_manager=130002, role=1),
                # Employee(staff_id=151408, staff_fname='Philip', staff_lname='Lee', dept='Engineering', position='Director', country='Singapore', email='Philip.Lee@allinone.com.sg', reporting_manager=130002, role=1),
                # Employee(staff_id=140003, staff_fname='Janice', staff_lname='Chan', dept='Sales', position='Account Manager', country='Singapore', email='Janice.Chan@allinone.com.sg', reporting_manager=140894, role=2),
                # Employee(staff_id=140004, staff_fname='Mary', staff_lname='Teo', dept='Sales', position='Account Manager', country='Singapore', email='Mary.Teo@allinone.com.sg', reporting_manager=140894, role=2),
                # Employee(staff_id=140036, staff_fname='Charlotte', staff_lname='Wong', dept='Sales', position='Account Manager', country='Singapore', email='Charlotte.Wong@allinone.com.sg', reporting_manager=140894, role=2),
                # Employee(staff_id=140078, staff_fname='Amelia', staff_lname='Ong', dept='Sales', position='Account Manager', country='Singapore', email='Amelia.Ong@allinone.com.sg', reporting_manager=140894, role=2),
                # Employee(staff_id=140102, staff_fname='Eva', staff_lname='Yong', dept='Sales', position='Account Manager', country='Singapore', email='Eva.Yong@allinone.com.sg', reporting_manager=140894, role=2),
                # Employee(staff_id=140108, staff_fname='Liam', staff_lname='The', dept='Sales', position='Account Manager', country='Singapore', email='Liam.The@allinone.com.sg', reporting_manager=140894, role=2),
                # Employee(staff_id=140115, staff_fname='Noah', staff_lname='Ng', dept='Sales', position='Account Manager', country='Singapore', email='Noah.Ng@allinone.com.sg', reporting_manager=140894, role=2),
                # Employee(staff_id=140525, staff_fname='Oliver', staff_lname='Tan', dept='Sales', position='Account Manager', country='Singapore', email='Oliver.Tan@allinone.com.sg', reporting_manager=140894, role=2),
                # Employee(staff_id=140736, staff_fname='William', staff_lname='Fu', dept='Sales', position='Account Manager', country='Singapore', email='William.Fu@allinone.com.sg', reporting_manager=140894, role=2),
                
            ]

            # Insert employees into the database
            db.session.add_all(employees)
            db.session.commit()  # Commit to get IDs for applications

                        
            # Create WFH applications
            applications = [
                WFHApplication(staff_id=140878, time_slot='AM', staff_apply_reason='test application for james', manager_reject_reason=None),
                WFHApplication(staff_id=140878, time_slot='PM', staff_apply_reason='test withdrawal for james', manager_reject_reason=None),

                WFHApplication(staff_id=140002, time_slot='FULL', staff_apply_reason='test application for susan', manager_reject_reason=None),
                WFHApplication(staff_id=140002, time_slot='AM', staff_apply_reason='test withdrawal for susan', manager_reject_reason=None),

                WFHApplication(staff_id=140015, time_slot='AM', staff_apply_reason='Urgent family commitment', manager_reject_reason=None),
                WFHApplication(staff_id=140015, time_slot='PM', staff_apply_reason='Urgent family commitment', manager_reject_reason=None),
                WFHApplication(staff_id=140015, time_slot='AM', staff_apply_reason='Urgent family commitment', manager_reject_reason=None),

                WFHApplication(staff_id=140025, time_slot='AM', staff_apply_reason='Urgent family commitment', manager_reject_reason=None),
                WFHApplication(staff_id=140025, time_slot='AM', staff_apply_reason='test application for emma', manager_reject_reason=None),  # KAIEN 
                WFHApplication(staff_id=140025, time_slot='AM', staff_apply_reason='test application for emma', manager_reject_reason=None),  # KAIEN 
            ]

            db.session.add_all(applications)
            db.session.commit()  # Commit to generate application IDs

            schedules = [
                WFHSchedule(application_id=applications[0].application_id, wfh_date=date(2024, 10, 22), status='Pending_Approval', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[1].application_id, wfh_date=date(2024, 10, 28), status='Pending_Withdrawal', manager_withdraw_reason=None),

                WFHSchedule(application_id=applications[2].application_id, wfh_date=date(2024, 10, 23), status='Pending_Approval', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[3].application_id, wfh_date=date(2024, 10, 24), status='Pending_Withdrawal', manager_withdraw_reason=None),

                WFHSchedule(application_id=applications[4].application_id, wfh_date=date(2024, 10, 22), status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[5].application_id, wfh_date=date(2024, 10, 23), status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[6].application_id, wfh_date=date(2024, 10, 24), status='Approved', manager_withdraw_reason=None),

                WFHSchedule(application_id=applications[7].application_id, wfh_date=date(2024, 10, 24), status='Approved', manager_withdraw_reason=None),

                WFHSchedule(application_id=applications[8].application_id, wfh_date=date(2024, 10, 25), status='Pending_Approval', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[8].application_id, wfh_date=date(2024, 11, 1), status='Pending_Approval', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[9].application_id, wfh_date=date(2024, 10, 21), status='Pending_Withdrawal', manager_withdraw_reason=None),  # KAIEN 
                WFHSchedule(application_id=applications[9].application_id, wfh_date=date(2024, 11, 28), status='Pending_Withdrawal', manager_withdraw_reason=None),  # KAIEN 
            ]

            db.session.add_all(schedules)
            db.session.commit()  # Final commit to save schedules

            withdrawn =[
                WFHWithdrawal(wfh_id = schedules[1].wfh_id, staff_withdraw_reason='test withdrawal for james', manager_reject_withdrawal_reason=None),
                WFHWithdrawal(wfh_id = schedules[3].wfh_id, staff_withdraw_reason='test withdrawal for susan', manager_reject_withdrawal_reason=None),
                WFHWithdrawal(wfh_id = schedules[10].wfh_id, staff_withdraw_reason='test withdrawal for susan', manager_reject_withdrawal_reason=None),  # KAIEN 
                WFHWithdrawal(wfh_id = schedules[11].wfh_id, staff_withdraw_reason='test withdrawal for susan', manager_reject_withdrawal_reason=None)  # KAIEN 
            ]
            db.session.add_all(withdrawn)
            db.session.commit()  # Final commit to save schedules
        except Exception as e:
            db.session.rollback()
            raise e

    # Test Case 2: Approve WFH Application Request [MAA04]
    def test_approve_application(self):
        print("test case 2")
        response = self.client.post('api/application/approverejectapplication/140894', json={
                "application_id": 1,
                "status": "Approve",
                "staff_id": 140878,
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Application Approved'})

        with self.app.app_context():
            db.session.flush()  # Force the ORM to flush pending changes to the DB
            db.session.commit()  # Ensure all pending transactions are committed

            approved_schedule = WFHSchedule.query.filter_by(application_id=1).first()

            self.assertIsNotNone(approved_schedule)
            self.assertEqual(approved_schedule.status, 'Approved')
        
        print("Finish")

    # Test Case 3: Approve WFH Withdrawal Request [MAA06]
    # KAIEN 
    def test_approve_withdrawal(self):
        print("test case 3")
        response = self.client.post('api/application/approverejectapplication/140894', json={
                "application_id": 2,
                "wfh_id": 2,
                "status": "Approve",
                "staff_id": 140878,
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Withdrawal Approved'})

        with self.app.app_context():
            db.session.flush()  # Force the ORM to flush pending changes to the DB
            db.session.commit()  # Ensure all pending transactions are committed

            approved_schedule = WFHSchedule.query.filter_by(wfh_id=2, application_id=2).first() # KAIEN

            self.assertIsNotNone(approved_schedule)
            self.assertEqual(approved_schedule.status, 'Withdrawn')
        
        print("Finish")
    
    # Test Case 4: Approve Recurring WFH Application Request [MAA04]
    def test_approve_recurring_application(self):
        print("test case 4")
        response = self.client.post('api/application/approverejectapplication/140894', json={
                "application_id": 9,
                "status": "Approve",
                "staff_id": 140025,
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Application Approved'})

        with self.app.app_context():
            db.session.flush()  # Force the ORM to flush pending changes to the DB
            db.session.commit()  # Ensure all pending transactions are committed

            approved_schedules = WFHSchedule.query.filter_by(application_id=9).all()
            print("THIS",approved_schedules)

            for approved_schedule in approved_schedules:
                self.assertIsNotNone(approved_schedule)
                self.assertEqual(approved_schedule.status, 'Approved')
        
        print("Finish")

    # Test case 5: Error for missing JSON data in request
    def test_approve_or_reject(self):
        response = self.client.post('api/application/approverejectapplication/140894', json=False, content_type='application/json')
        
        # Check for a 400 Bad Request response due to missing JSON
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'JSON data passed from client side is insufficient', response.data)

    # Test case 5: Unexpected error handling test
    @patch.object(db.session, 'query')
    def test_approve_or_reject_unexpected_error(self, mock_commit):
        # Simulate an unexpected error (e.g., KeyError) during the process
        mock_commit.side_effect = KeyError("Unexpected error occurred")
        

        
        response = self.client.post('api/application/approverejectapplication/140894',json={
                "application_id": 9,
                "status": "Approve",
                "staff_id": 140025,
            }
            , headers={"Content-Type": "application/json"})
        
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'An unexpected error occurred', response.data)
    

    # Test case 6: Database connection issue simulation (OperationalError)
    @patch.object(db.session, 'query')
    def test_approve_or_reject_db_connection_error(self, mock_query):
        # Mocking an OperationalError during the commit
        mock_query.side_effect = OperationalError("DB Connection Error", None, None)

        
        response = self.client.post('api/application/approverejectapplication/140894',json={
                "application_id": 9,
                "status": "Approve",
                "staff_id": 140025,
            }
            , headers={"Content-Type": "application/json"})
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Database connection issue.')

    # Test case 7: SQLAlchemy error handling test
    @patch.object(db.session, 'query')
    def test_display_approve_or_reject_sqlalchemy_error(self, mock_query):
        # Simulate an SQLAlchemyError
        mock_query.side_effect = SQLAlchemyError("Database query error")

        response = self.client.post('api/application/approverejectapplication/140894',json={
                "application_id": 9,
                "status": "Approve",
                "staff_id": 140025,
            }
            , headers={"Content-Type": "application/json"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {'error': 'Database query failed.'})

    # Test Case 8 : Wrong Reporting Manager
    def test_wrong_reporting_manager(self):
        response = self.client.post('api/application/approverejectapplication/140001', json={
                "application_id": 2,
                "status": "Approve",
                "staff_id": 140025,
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'failed': 'wrong reporting manager'})

    
    # Test Case 9 : No Schedule Found
    def test_no_schedule_found(self):

        response = self.client.post('api/application/approverejectapplication/140001', json={
                "application_id": 2,
                "status": "Approve",
                "staff_id": 140894,
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'failed': 'No pending requests found'})

    # NEWLY ADDED
    # Test Case 10: Approve WFH Withdrawal Request Recurring 
    # KAIEN 
    def test_approve_withdrawal_recurring(self):

        response = self.client.post('api/application/approverejectapplication/140894', json={
                "application_id": 10,
                "wfh_id": 11,
                "status": "Approve",
                "staff_id": 140025,
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Withdrawal Approved'})

        with self.app.app_context():
            db.session.flush()  # Force the ORM to flush pending changes to the DB
            db.session.commit()  # Ensure all pending transactions are committed

            approved_schedule = WFHSchedule.query.filter_by(application_id=2).first()

            self.assertIsNotNone(approved_schedule)
            self.assertEqual(approved_schedule.status, 'Withdrawn')    



if __name__ == '__main__':
    unittest.main()