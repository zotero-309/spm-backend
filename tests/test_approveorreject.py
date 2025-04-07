from datetime import date
import sys
import os
import unittest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app import create_app, db
from app.models import Employee, WFHApplication, WFHSchedule, WFHWithdrawal

class TestWFHApproveOrReject(unittest.TestCase):
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
                WFHApplication(staff_id=140025, time_slot='AM', staff_apply_reason='test application for emma', manager_reject_reason=None),

                
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

                WFHSchedule(application_id=applications[3].application_id, wfh_date=date(2024, 10, 31), status='Pending_Withdrawal', manager_withdraw_reason=None),
            ]

            db.session.add_all(schedules)
            db.session.commit()  # Final commit to save schedules

            withdrawn =[
                WFHWithdrawal(wfh_id = schedules[1].wfh_id, staff_withdraw_reason='test withdrawal for james', manager_reject_withdrawal_reason=None),
                WFHWithdrawal(wfh_id = schedules[3].wfh_id, staff_withdraw_reason='test withdrawal for susan', manager_reject_withdrawal_reason=None),
                WFHWithdrawal(wfh_id = schedules[10].wfh_id, staff_withdraw_reason='test withdrawal for susan', manager_reject_withdrawal_reason=None)
            ]
            db.session.add_all(withdrawn)
            db.session.commit()  # Final commit to save schedules
        except Exception as e:
            db.session.rollback()
            raise e
        


    # Test Case 1: view the details of the Work-From-Home applications and withdrawal requests [MAA02], [MRA02]
    # KAIEN
    def test_view_application_under_me(self):
        print("test case 1")
        response = self.client.get('api/application/wfhrequest/140894')
        print("Response JSON:", response.json)
        expected_result = [
            {
                'application_id': 1,
                'listofschedule': [
                    {'wfh_id': 1, 'staff_id': 140878, 'label': 'AM', 'dateStart': '2024-10-22T09:00:00', 'dateEnd': '2024-10-22T13:00:00', 'class': 'Pending_Approval', 'description': 'test application for james',
                    'staff_name': 'James Tong', 'staff_dept': 'Account Manager', 'percentage': 25}
                ]
            },
            {
                'application_id': '2-2',
                'listofschedule': [
                    {'wfh_id': 2, 'staff_id': 140878, 'label': 'PM', 'dateStart': '2024-10-23T14:00:00', 'dateEnd': '2024-10-23T18:00:00', 'class': 'Pending_Withdrawal', 'description': 'test withdrawal for james',
                    'staff_name': 'James Tong', 'staff_dept': 'Account Manager', 'percentage': 50}
                ]
            },
            {
                'application_id': 3,
                'listofschedule': [
                    {'wfh_id': 3, 'staff_id': 140002, 'label': 'FULL', 'dateStart': '2024-10-23T09:00:00', 'dateEnd': '2024-10-23T18:00:00', 'class': 'Pending_Approval', 'description': 'test application for susan',
                    'staff_name': 'Susan Goh', 'staff_dept': 'Account Manager', 'percentage': [0,50]}
                ]
            },
            {
                'application_id': '4-4',
                'listofschedule': [
                    {'wfh_id': 4, 'staff_id': 140002, 'label': 'AM', 'dateStart': '2024-10-24T09:00:00', 'dateEnd': '2024-10-24T13:00:00', 'class': 'Pending_Withdrawal', 'description': 'test withdrawal for susan',
                    'staff_name': 'Susan Goh', 'staff_dept': 'Account Manager', 'percentage':75}
                ]
            },
            {
                'application_id': '4-11',
                'listofschedule': [
                    {'wfh_id': 11, 'staff_id': 140002, 'label': 'AM', 'dateStart': '2024-10-31T09:00:00', 'dateEnd': '2024-10-31T13:00:00', 'class': 'Pending_Withdrawal', 'description': 'test withdrawal for susan',
                    'staff_name': 'Susan Goh', 'staff_dept': 'Account Manager', 'percentage':25}
                ]
            },
            {
                'application_id': 9,
                'listofschedule': [
                    {'wfh_id': 9, 'staff_id': 140025, 'label': 'AM', 'dateStart': '2024-10-25T09:00:00', 'dateEnd': '2024-10-25T13:00:00', 'class': 'Pending_Approval', 'description': 'test application for emma',
                    'staff_name': 'Emma Heng', 'staff_dept': 'Account Manager', 'percentage': 0},
                    {'wfh_id': 10, 'staff_id': 140025, 'label': 'AM', 'dateStart': '2024-11-01T09:00:00', 'dateEnd': '2024-11-01T13:00:00', 'class': 'Pending_Approval', 'description': 'test application for emma',
                    'staff_name': 'Emma Heng', 'staff_dept': 'Account Manager', 'percentage': 0},
                ]
            },
        ]

        def rearrange_data(actual_data):
            # Initialize a list to hold the rearranged entries
            rearranged_data = []

            # Loop through each entry in actual_data
            for entry in actual_data:
                # Create a new entry with the desired order
                new_entry = {}
                new_entry['application_id'] = entry['application_id']

                for new_e in entry['listofschedule']:
                    new_entry['listofschedule'] = [];
                    new_entry['listofschedule'].append({
                        'class': new_e['class'],  # Accessing office time in am
                        'dateEnd': new_e['dateEnd'],          # Accessing wfh time in am
                        'dateStart': new_e['dateStart'],  # Directly adding the employees list
                        'description': new_e['description'],
                        'label': new_e['label'],
                        'percentage': new_e['percentage'],
                        'staff_dept': new_e['staff_dept'],
                        'staff_id': new_e['staff_id'],
                        'staff_name': new_e['staff_name'],
                        'wfh_id': new_e['wfh_id']
                    })
                new_entry['listofschedule'] = sorted(new_entry['listofschedule'], key=lambda x: x['dateStart'])

                

                # Append the new entry to the rearranged_data list
                rearranged_data.append(new_entry)

            return rearranged_data
        expected_result = rearrange_data(expected_result)
        actual_result = rearrange_data(response.json)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(actual_result, expected_result)
        print("finish")


    # test case 2: for ceo 
    def test_view_application_under_ceo(self):
        response = self.client.get('api/application/wfhrequest/130002')
        print("Response JSON:", response.json)
        def rearrange_data(actual_data):
            # Initialize a list to hold the rearranged entries
            rearranged_data = []

            # Loop through each entry in actual_data
            for entry in actual_data:
                # Create a new entry with the desired order
                new_entry = {}
                new_entry['application_id'] = entry['application_id']
                for entry in entry['listofschedule']:
                    
                    new_entry['listofschedule'] =[{
                            'class': entry['class'],  # Accessing office time in am
                            'dateEnd': entry['dateEnd'],          # Accessing wfh time in am
                            'dateStart': entry['dateStart'],  # Directly adding the employees list
                            'description': entry['description'],
                            'label': entry['label'],
                            'percentage': entry['percentage'],
                            'staff_dept': entry['staff_dept'],
                            'staff_id': entry['staff_id'],
                            'staff_name': entry['staff_name'],
                            'wfh_id': entry['wfh_id']
                        }]

                # Append the new entry to the rearranged_data list
                rearranged_data.append(new_entry)

            return rearranged_data

        expected_result =   [
                            ]
        expected_result = rearrange_data(expected_result)
        actual_result = rearrange_data(response.json)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(actual_result, expected_result)


    # Test case 5: Unexpected error handling test
    @patch.object(db.session, 'query')
    def test_auto_reject_unexpected_error(self, mock_commit):
        # Simulate an unexpected error (e.g., KeyError) during the process
        mock_commit.side_effect = KeyError("Unexpected error occurred")
        

        
        response = self.client.get('/api/application/wfhrequest/140894')
        
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'An unexpected error occurred', response.data)
    

    # Test case 4: Database connection issue simulation (OperationalError)
    @patch.object(db.session, 'query')
    def test_auto_reject_db_connection_error(self, mock_query):
        # Mocking an OperationalError during the commit
        mock_query.side_effect = OperationalError("DB Connection Error", None, None)

        
        response = self.client.get('/api/application/wfhrequest/140894')
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Database connection issue.')

    # Test case 5: SQLAlchemy error handling test
    @patch.object(db.session, 'query')
    def test_display_auto_reject_sqlalchemy_error(self, mock_query):
        # Simulate an SQLAlchemyError
        mock_query.side_effect = SQLAlchemyError("Database query error")

        response = self.client.get('/api/application/wfhrequest/140894')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {'error': 'Database query failed.'})




    # # Test Case 1: Less than 50% even after approving this (HAPPY PATH)
    # def test_less_than_fifty(self):
    #     print("test case1 ")
    #     response = self.client.post('api/application/approverejectapplication/140894',
    #     json={
    #             "application_id": 2,
    #             "status": "Approved",
    #             "staff_id": 140002
    #         }
    #     , headers={"Content-Type": "application/json"})
        
    #     self.assertEqual(response.status_code, 201)
    #     self.assertEqual(response.json, {'success': 'Approved'})
    #     print("finish")

    # # Test Case 2: More than 50% after approving this (NEGATIVE PATH)
    # def test_more_than_fifty(self):
    #     print("test case2 ")
    #     response = self.client.post('api/application/approverejectapplication/140894',
    #         json={
    #             "time_slot": "AM",
    #             "start_date": "2024-10-4T00:00:00.000000Z",
    #             "status": "Approved",
    #             "staff_id": 140003
    #         }, headers={"Content-Type": "application/json"})
        
    #     self.assertEqual(response.status_code, 201)
    #     self.assertEqual(response.json, {'failed': 'more than 50% of the people are wfh on this day'})
    #     print("finish")



    # # Test Case 3: Reject WFH Application
    # def test_reject_application(self):
    #     print("test case 3 ")
    #     response = self.client.post('api/application/approverejectapplication/140894', json={
    #             "application_id": 7,
    #             "status": "Rejected",
    #             "staff_id": 140003,
    #             "manager_reject_reason": "I need you at WORK always trying to WFH",
    #         }
    #         , headers={"Content-Type": "application/json"})
    #     self.assertEqual(response.status_code, 201)
    #     self.assertEqual(response.json, {'failed': 'Rejected'})
    #     print("finish")

    # # Test Case 4: Reject Recurring WFH Application
    # def test_reject_recurring_application(self):
    #     print("test case 4 ")
    #     response = self.client.post('api/application/approverejectapplication/140894', json={
    #             "application_id": 1,
    #             "status": "Rejected",
    #             "staff_id": 140002,
    #             "manager_reject_reason": "I need you at WORK always trying to WFH",
    #         }
    #         , headers={"Content-Type": "application/json"})
    #     self.assertEqual(response.status_code, 201)
    #     self.assertEqual(response.json, {'failed': 'Rejected'})
    #     print("finish")

    
    # # Test Case 6: Reject withdrawal WFH Application
    # def test_reject_withdrawal_application(self):
    #     print("test case 6 ")
    #     response = self.client.post('api/application/approverejectapplication/140894', json={
    #             "application_id": 8,
    #             "wfh_id": 9,
    #             "status": "Approved",
    #             "staff_id": 140003,
    #         }
    #         , headers={"Content-Type": "application/json"})
    #     self.assertEqual(response.status_code, 201)
    #     self.assertEqual(response.json, {'unsuccessful': 'unsuccesful withdraw'})
    #     print("Finish")
    
    # # Test Case 5: View Application of Staff under me
    # def test_view_application_under_me(self):
    #     print("test case 4 ")
    #     response = self.client.get('api/application/wfhrequest/140894')
    #     expected_result = [{'application_id': 2, 'listofschedule': [{'wfh_id': 3, 'staff_id': 140002, 'label': 'FULL', 'dateStart': '2024-11-03T09:00:00', 'dateEnd': '2024-11-03T18:00:00', 'class': 'Pending_Approval', 'description': 'Health reasons'}]}, {'application_id': 6, 'listofschedule': [{'wfh_id': 7, 'staff_id': 140003, 'label': 'AM', 'dateStart': '2024-10-04T09:00:00', 'dateEnd': '2024-10-04T13:00:00', 'class': 'Pending_Approval', 'description': 'Family matters'}]}]
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json, expected_result)
    #     print("finish")
    

    # # Test Case 6: % of wfh
    # def test_percentage_of_wfh(self):
    #     print("test case 6")
    #     response = self.client.get('api/schedule/numberofwfh/140894')
    #     expected_result = [{'date': '2024-10-27', 'am': {'wfhpercentage': 25}, 'pm': {'wfhpercentage': 25}}, {'date': '2024-10-04', 'am': {'wfhpercentage': 50}, 'pm': {'wfhpercentage': 0}}]
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json, expected_result)
    #     print("finish")

if __name__ == '__main__':
    unittest.main()

