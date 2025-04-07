from datetime import date
import sys
import os
import unittest

from app import create_app, db
from app.models import Employee, WFHApplication, WFHSchedule, WFHWithdrawal

class TestWFHRejectRequests(unittest.TestCase):
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
                WFHApplication(staff_id=140025, time_slot='AM', staff_apply_reason='test application for emma', manager_reject_reason=None),

                WFHApplication(staff_id=140878, time_slot='AM', staff_apply_reason='test withdrawal for james', manager_reject_reason=None),
                WFHApplication(staff_id=140878, time_slot='PM', staff_apply_reason='test application for james', manager_reject_reason=None),
            ]

            db.session.add_all(applications)
            db.session.commit()  # Commit to generate application IDs

            schedules = [
                WFHSchedule(application_id=applications[0].application_id, wfh_date=date(2024, 10, 22), status='Pending_Approval', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[1].application_id, wfh_date=date(2024, 10, 23), status='Pending_Withdrawal', manager_withdraw_reason=None),

                WFHSchedule(application_id=applications[2].application_id, wfh_date=date(2024, 10, 23), status='Pending_Approval', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[3].application_id, wfh_date=date(2024, 10, 24), status='Pending_Withdrawal', manager_withdraw_reason=None),

                WFHSchedule(application_id=applications[4].application_id, wfh_date=date(2024, 10, 22), status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[5].application_id, wfh_date=date(2024, 10, 23), status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[6].application_id, wfh_date=date(2024, 10, 24), status='Approved', manager_withdraw_reason=None),

                WFHSchedule(application_id=applications[7].application_id, wfh_date=date(2024, 10, 24), status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[8].application_id, wfh_date=date(2024, 10, 25), status='Pending_Approval', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[8].application_id, wfh_date=date(2024, 11, 1), status='Pending_Approval', manager_withdraw_reason=None),

                WFHSchedule(application_id=applications[9].application_id, wfh_date=date(2024, 10, 23), status='Pending_Withdrawal', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[10].application_id, wfh_date=date(2024, 10, 22), status='Pending_Approval', manager_withdraw_reason=None),
            ]

            db.session.add_all(schedules)
            db.session.commit()  # Final commit to save schedules

            withdrawn =[
                WFHWithdrawal(wfh_id = schedules[1].wfh_id, staff_withdraw_reason='test withdrawal for james', manager_reject_withdrawal_reason=None),
                WFHWithdrawal(wfh_id = schedules[3].wfh_id, staff_withdraw_reason='test withdrawal for susan', manager_reject_withdrawal_reason=None),
                WFHWithdrawal(wfh_id = schedules[9].wfh_id, staff_withdraw_reason='test withdrawal for james', manager_reject_withdrawal_reason=None)
            ]
            db.session.add_all(withdrawn)
            db.session.commit()  # Final commit to save schedules
        except Exception as e:
            db.session.rollback()
            raise e
    
    # Test Case 1: Testing for withdrawal request
    # KAIEN
    def test_reject_application_for_withdrawal(self):

        response = self.client.post('api/application/approverejectapplication/140894', json={
                "application_id": 10,
                "wfh_id": 11,
                "status": "Reject",
                "staff_id": 140878,
                'manager_reject_reason' : None
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Approval or Rejection of withdrawal request not processed' })

    # Test Case 2: testing for pending approval application
    def test_reject_application_for_pending_approval(self):

        response = self.client.post('api/application/approverejectapplication/140894', json={
                "application_id": 11,
                "status": "Reject",
                "staff_id": 140878,
                'manager_reject_reason' : None
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Approval or Rejection of application request not processed' })

    # Test Case 3: Reject WFH Application Request [MRA04]
    def test_reject_application(self):
        response = self.client.post('api/application/approverejectapplication/140894', json={
                "application_id": 1,
                "status": "Reject",
                "staff_id": 140878,
                "manager_reject_reason": "testing for rejecting application",
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Application Rejected'})

        with self.app.app_context():
            db.session.flush()  # Force the ORM to flush pending changes to the DB
            db.session.commit()  # Ensure all pending transactions are committed

            # Fetch the updated schedule with the status 'Rejected'
            rejected_schedule = WFHSchedule.query.filter_by(application_id=1).first()

            # Assert that the pending approval has been successfully rejected
            self.assertIsNotNone(rejected_schedule)
            self.assertEqual(rejected_schedule.status, 'Rejected')

            # Fetch the related application and check the rejection reason
            rejected_application = WFHApplication.query.get(rejected_schedule.application_id)

            self.assertIsNotNone(rejected_application)
            self.assertEqual(rejected_application.manager_reject_reason, 'testing for rejecting application')


    # Test Case 4: Reject WFH Withdrawal Request [MRA06]
    # KAIEN
    def test_reject_withdrawal(self):
        response = self.client.post('api/application/approverejectapplication/140894', json={
                "application_id": 2,
                "wfh_id": 2,
                "status": "Reject",
                "staff_id": 140878,
                "manager_reject_reason": "testing for rejecting withdrawal",
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Withdrawal Rejected'})

        with self.app.app_context():
            db.session.flush()  # Force the ORM to flush pending changes to the DB
            db.session.commit()  # Ensure all pending transactions are committed

            approved_schedule = WFHSchedule.query.filter_by(application_id=2, wfh_id=2).first() # KAIEN

            self.assertIsNotNone(approved_schedule)
            self.assertEqual(approved_schedule.status, 'Approved')

            rejected_withdrawal = WFHWithdrawal.query.filter_by(wfh_id=2).first()

            self.assertIsNotNone(rejected_withdrawal)
            self.assertEqual(rejected_withdrawal.manager_reject_withdrawal_reason, 'testing for rejecting withdrawal')
        

    # Test Case 5: Reject Recurring WFH Application Request [MRA04]
    def test_reject_recurring_application(self):
        response = self.client.post('api/application/approverejectapplication/140894', json={
                "application_id": 9,
                "status": "Reject",
                "staff_id": 140025,
                "manager_reject_reason": "testing for rejecting recurring application",
            }
            , headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'success': 'Application Rejected'})

        with self.app.app_context():
            db.session.flush()  # Force the ORM to flush pending changes to the DB
            db.session.commit()  # Ensure all pending transactions are committed

            # Fetch the updated schedule with the status 'Rejected'
            rejected_schedules = WFHSchedule.query.filter_by(application_id=9).all()

            # Assert that the pending approval has been successfully rejected
            for rejected_schedule in rejected_schedules:
                self.assertIsNotNone(rejected_schedule)
                self.assertEqual(rejected_schedule.status, 'Rejected')

                # Fetch the related application and check the rejection reason
                rejected_application = WFHApplication.query.get(rejected_schedule.application_id)

                self.assertIsNotNone(rejected_application)
                self.assertEqual(rejected_application.manager_reject_reason, 'testing for rejecting recurring application')


if __name__ == '__main__':
    unittest.main()