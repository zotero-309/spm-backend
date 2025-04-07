from datetime import datetime, timedelta
import unittest
from unittest.mock import patch
from app import create_app, db
from app.models import Employee, WFHApplication, WFHSchedule, WFHWithdrawal
from app.application import auto_reject
from sqlalchemy.exc import SQLAlchemyError, OperationalError

class TestWFHAutoReject(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Set up the test client and in-memory database
        self.app = create_app(test_config=True)
        self.client = self.app.test_client()

        # Push the application context and initialize the database
        with self.app.app_context():
            db.create_all()
            self.populate_test_data(self)

    @classmethod
    def tearDownClass(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def populate_test_data(self):
        try:
            # Create employees
            employees = [
                Employee(staff_id=130002, staff_fname='Jack', staff_lname='Sim', dept='CEO', position='MD', country='Singapore', email='jack.sim@allinone.com.sg', reporting_manager=130002, role=1),
                Employee(staff_id=140001, staff_fname='Derek', staff_lname='Tan', dept='Sales', position='Director', country='Singapore', email='Derek.Tan@allinone.com.sg', reporting_manager=130002, role=1),
                Employee(staff_id=140002, staff_fname='Susan', staff_lname='Goh', dept='Sales', position='Account Manager', country='Singapore', email='Susan.Goh@company.com', reporting_manager=140001, role=2),
                Employee(staff_id=140025, staff_fname='Emma', staff_lname='Heng', dept='Sales', position='Account Manager', country='Singapore', email='Emma.Heng@allinone.com.sg', reporting_manager=140001, role=2),
            ]
            db.session.add_all(employees)
            db.session.commit()

            # Insert WFH applications and schedules
            wfh_applications = [
                WFHApplication(staff_id=140002, time_slot='AM', staff_apply_reason='Urgent commitment', manager_reject_reason=None),
                WFHApplication(staff_id=140002, time_slot='PM', staff_apply_reason='Urgent commitment', manager_reject_reason=None),
                WFHApplication(staff_id=140025, time_slot='PM', staff_apply_reason='Urgent commitment', manager_reject_reason=None),
            ]
            db.session.add_all(wfh_applications)
            db.session.commit()

            # Insert WFH schedules that are older than 2 months
            two_months_ago = datetime.now() - timedelta(weeks=8)
            two_months_ago_plus_one_week = datetime.now() - timedelta(weeks=8) + timedelta(weeks=1)
            schedules = [
                WFHSchedule(application_id=wfh_applications[0].application_id, wfh_date=two_months_ago.date(), status='Pending_Approval', manager_withdraw_reason=None),
                WFHSchedule(application_id=wfh_applications[1].application_id, wfh_date=two_months_ago.date(), status='Pending_Withdrawal', manager_withdraw_reason=None),
                WFHSchedule(application_id=wfh_applications[2].application_id, wfh_date=two_months_ago.date(), status='Pending_Approval', manager_withdraw_reason=None),
                WFHSchedule(application_id=wfh_applications[2].application_id, wfh_date=two_months_ago_plus_one_week.date(), status='Pending_Approval', manager_withdraw_reason=None),
            ]
            db.session.add_all(schedules)
            db.session.commit()

            withdrawn =[
                WFHWithdrawal(wfh_id = schedules[1].wfh_id, staff_withdraw_reason='test auto withdrawal', manager_reject_withdrawal_reason=None)
            ]
            db.session.add_all(withdrawn)
            db.session.commit()  # Final commit to save schedules

        except Exception as e:
            db.session.rollback()
            raise e

    def test_auto_reject(self):
        with self.app.app_context():
            self.client.get('api/application/autoReject')

            # Fetch the updated schedules for both rejected and approved cases
            rejected_schedules = WFHSchedule.query.filter_by(status='Rejected').all()
            approved_schedule = WFHSchedule.query.filter_by(status='Approved').first()
            pending_approvals = WFHSchedule.query.filter_by(status='Pending_Approval').all()
            pending_withdrawals = WFHSchedule.query.filter_by(status='Pending_Withdrawal').all()

            # Assert that pending_approvals is empty
            self.assertEqual(len(pending_approvals), 0, "There should be no pending approvals")

            # Assert that pending_withdrawals is empty
            self.assertEqual(len(pending_withdrawals), 0, "There should be no pending withdrawals")


            # Assert that the pending approval has been rejected
            for rejected_schedule in rejected_schedules:
                self.assertIsNotNone(rejected_schedule)
                self.assertEqual(rejected_schedule.status, 'Rejected')
                rejected_application = WFHApplication.query.get(rejected_schedule.application_id)
                self.assertEqual(rejected_application.manager_reject_reason, 'rejected by system')

            # Assert that the pending withdrawal has been approved
            self.assertIsNotNone(approved_schedule)
            self.assertEqual(approved_schedule.status, 'Approved')
            approved_withdrawal = WFHWithdrawal.query.filter_by(wfh_id=approved_schedule.wfh_id).first()
            self.assertEqual(approved_withdrawal.manager_reject_withdrawal_reason, 'rejected by system')


    
    # Test case 5: Unexpected error handling test
    @patch.object(db.session, 'query')
    def test_auto_reject_unexpected_error(self, mock_commit):
        # Simulate an unexpected error (e.g., KeyError) during the process
        mock_commit.side_effect = KeyError("Unexpected error occurred")
        

        
        response = self.client.get('api/application/autoReject')
        
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'An unexpected error occurred', response.data)
    

    # Test case 4: Database connection issue simulation (OperationalError)
    @patch.object(db.session, 'query')
    def test_auto_reject_db_connection_error(self, mock_query):
        # Mocking an OperationalError during the commit
        mock_query.side_effect = OperationalError("DB Connection Error", None, None)
        response = self.client.get('api/application/autoReject')
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {'error':'Database connection issue.'})

    # Test case 5: SQLAlchemy error handling test
    @patch.object(db.session, 'query')
    def test_display_auto_reject_sqlalchemy_error(self, mock_query):
        # Simulate an SQLAlchemyError
        mock_query.side_effect = SQLAlchemyError("Database query error")

        response = self.client.get('api/application/autoReject')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {'error': 'Database query failed.'})

if __name__ == '__main__':
    unittest.main()
