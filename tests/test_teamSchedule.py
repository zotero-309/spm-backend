from datetime import datetime
import sys
import os
import unittest
import io

from sqlalchemy import text
from app import create_app, db
from app.models import Employee, WFHApplication, WFHSchedule, WFHWithdrawal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class TestWFHTeamSchedule(unittest.TestCase):

    # Helper function to sort the response data structure
    # def sort_schedule_data(self, schedule_data):
    #     for entry in schedule_data:
    #         entry['am']['employees'].sort(key=lambda x: x['id'])  # Sorting AM employees by id
    #         entry['pm']['employees'].sort(key=lambda x: x['id'])  # Sorting PM employees by id
    #     return schedule_data

    def sort_schedule_data(self, schedule_data):
        sorted_data = []
        for data in schedule_data:
            if 'employees' in data['am'] or 'employees' in data['pm']:
                # Sorting the dictionary and its contents
                sorted_data.append({
                    'date': data['date'],  # date is already a single string, no need to sort
                    'am': {
                        'wfh': data['am']['wfh'],
                        'office': data['am']['office'],
                        'employees': sorted(data['am']['employees'], key=lambda x: x['name'])  # Sort am employees by name
                    },
                    'pm': {
                        'wfh': data['pm']['wfh'],
                        'office': data['pm']['office'],
                        'employees': sorted(data['pm']['employees'], key=lambda x: x['name'])  # Sort pm employees by name
                    }
                })
            else:
                sorted_data.append({
                    'date': data['date'], 
                    'am': {'office': 5, 'wfh': 0}, 
                    'pm': {'office': 5, 'wfh': 0}
                    })
        return sorted_data


    
    # def sort_schedule_data(self, schedule_data):
    #     for data in schedule_data:
    #         for session in ['am', 'pm']:
    #             if 'employees' in data[session]:
    #                 data[session]['employees'].sort(key=lambda x: x['name']) 
    #     return schedule_data

    def sort_employee_data(self, employee_data):
        for entry in employee_data:
            entry['EmployeeList'].sort(key=lambda x: x['id'])  # Sorting employees by id
        return employee_data
    

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
                Employee(staff_id=140894, staff_fname='Rahim', staff_lname='Khalid', dept='Sales', position='Sales Manager', country='Singapore', email='Rahim.Khalid@allinone.com.sg', reporting_manager=140001, role=3),
                Employee(staff_id=140878, staff_fname='James', staff_lname='Tong', dept='Sales', position='Account Manager', country='Singapore', email='James.Tong@allinone.com.sg', reporting_manager=140894, role=2),
                Employee(staff_id=140002, staff_fname='Susan', staff_lname='Goh', dept='Sales', position='Account Manager', country='Singapore', email='Susan.Goh@allinone.com.sg', reporting_manager=140894, role=2),
                Employee(staff_id=140015, staff_fname='Oliva', staff_lname='Lim', dept='Sales', position='Account Manager', country='Singapore', email='Oliva.Lim@allinone.com.sg', reporting_manager=140894, role=2),
                Employee(staff_id=140025, staff_fname='Emma', staff_lname='Heng', dept='Sales', position='Account Manager', country='Singapore', email='Emma.Heng@allinone.com.sg', reporting_manager=140894, role=2),
                Employee(staff_id=140108, staff_fname='Liam', staff_lname='The', dept='Sales', position='Account Manager', country='Singapore', email='Liam.The@allinone.com.sg', reporting_manager=140894, role=2),
                Employee(staff_id=140115, staff_fname='Noah', staff_lname='Ng', dept='Sales', position='Account Manager', country='Singapore', email='Noah.Ng@allinone.com.sg', reporting_manager=140894, role=2),
            ]

            # Insert employees into the database
            db.session.add_all(employees)
            db.session.commit()  # Commit to get IDs for applications

            # Dynamically generate dates for WFH applications
            today = datetime.now().date()
            future_date = today + timedelta(days=7)
            past_date = today - timedelta(days=7)

            # Create WFH applications
            applications = [
                WFHApplication(staff_id=140894, time_slot='AM', staff_apply_reason='Online meeting', manager_reject_reason=None),
                WFHApplication(staff_id=140878, time_slot='AM', staff_apply_reason='Conference', manager_reject_reason=None),
                WFHApplication(staff_id=140015, time_slot='PM', staff_apply_reason='Test', manager_reject_reason=None),
                WFHApplication(staff_id=140115, time_slot='FULL', staff_apply_reason='Conference', manager_reject_reason=None),
                WFHApplication(staff_id=140001, time_slot='AM', staff_apply_reason='Online meeting', manager_reject_reason=None),
            ]

            db.session.add_all(applications)
            db.session.commit()  # Commit to generate application IDs

            # Create schedules with different statuses and dynamically generated dates
            schedules = [
                WFHSchedule(application_id=applications[0].application_id, wfh_date=today, status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[1].application_id, wfh_date=today, status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[2].application_id, wfh_date=today, status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[3].application_id, wfh_date=today, status='Approved', manager_withdraw_reason=None),
                WFHSchedule(application_id=applications[4].application_id, wfh_date=future_date, status='Pending_Approval', manager_withdraw_reason=None),
            ]

            db.session.add_all(schedules)
            db.session.commit()  # Final commit to save schedules



        except Exception as e:
            db.session.rollback()  # Roll back any changes if an error occurs
            raise e


    # def generate_expected_team_schedule(self, start_date, end_date):
    #     expected_data = []
    #     current_date = start_date
    #     while current_date <= end_date:
    #         date_str = current_date.strftime('%Y-%m-%d')
    #         if current_date == datetime.now():
                
    #             expected_data.append({'date': date_str, 
    #                                   'am': {'wfh': 1, 'office': 4, 
    #                                          'employees': [{'id': 140015, 'name': 'Olivia Lim', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Oliva.Lim@allinone.com.sg', 'status': 'In-Office'}, 
    #                                                        {'id': 140025, 'name': 'Emma Heng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Emma.Heng@allinone.com.sg', 'status': 'In-Office'}, 
    #                                                        {'id': 140108, 'name': 'Liam The', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Liam.The@allinone.com.sg', 'status': 'In-Office'}, 
    #                                                        {'id': 140115, 'name': 'Noah Ng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Noah.Ng@allinone.com.sg', 'status': 'In-Office'}, 
    #                                                        {'id': 140878, 'name': 'James Tong', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'James.Tong@allinone.com.sg', 'status': 'WFH'}
    #                                                        ]}, 
    #                                     'pm': {'wfh': 0, 'office': 5, 
    #                                            'employees': [{'id': 140015, 'name': 'Olivia Lim', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Oliva.Lim@allinone.com.sg', 'status': 'In-Office'}, 
    #                                                          {'id': 140025, 'name': 'Emma Heng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Emma.Heng@allinone.com.sg', 'status': 'In-Office'}, 
    #                                                          {'id': 140108, 'name': 'Liam The', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Liam.The@allinone.com.sg', 'status': 'In-Office'}, 
    #                                                          {'id': 140115, 'name': 'Noah Ng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Noah.Ng@allinone.com.sg', 'status': 'In-Office'}, 
    #                                                          {'id': 140878, 'name': 'James Tong', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'James.Tong@allinone.com.sg', 'status': 'In-Office'}
    #                                                          ]}})

    #         else:
    #             expected_data.append({
    #                 'date': date_str, 
    #                 'am': {'office': 5, 'wfh': 0}, 
    #                 'pm': {'office': 5, 'wfh': 0}
    #                 })

    #         current_date += timedelta(days=1)


    #     return expected_data

    # Test Case: view own + team schedule
    def test_team_schedule(self):
        # Ensure that you're within the application context
        # Define the start and end date for the test 
        today = datetime.now()
        start_date = today - relativedelta(months=2)
        end_date = today + relativedelta(months=3)

        # Generate the expected data dynamically
        # expected_data = self.generate_expected_team_schedule(start_date, end_date)
        expected_data = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if current_date == today:
                
                expected_data.append({'date': date_str, 
                                      'am': {'wfh': 2, 'office': 3, 
                                             'employees': [{'id': 140015, 'name': 'Oliva Lim', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Oliva.Lim@allinone.com.sg', 'status': 'In-Office'}, 
                                                           {'id': 140025, 'name': 'Emma Heng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Emma.Heng@allinone.com.sg', 'status': 'In-Office'}, 
                                                           {'id': 140108, 'name': 'Liam The', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Liam.The@allinone.com.sg', 'status': 'In-Office'}, 
                                                           {'id': 140115, 'name': 'Noah Ng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Noah.Ng@allinone.com.sg', 'status': 'WFH'}, 
                                                           {'id': 140878, 'name': 'James Tong', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'James.Tong@allinone.com.sg', 'status': 'WFH'}
                                                           ]}, 
                                        'pm': {'wfh': 2, 'office': 3, 
                                               'employees': [{'id': 140015, 'name': 'Oliva Lim', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Oliva.Lim@allinone.com.sg', 'status': 'WFH'}, 
                                                             {'id': 140025, 'name': 'Emma Heng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Emma.Heng@allinone.com.sg', 'status': 'In-Office'}, 
                                                             {'id': 140108, 'name': 'Liam The', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Liam.The@allinone.com.sg', 'status': 'In-Office'}, 
                                                             {'id': 140115, 'name': 'Noah Ng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Noah.Ng@allinone.com.sg', 'status': 'WFH'}, 
                                                             {'id': 140878, 'name': 'James Tong', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'James.Tong@allinone.com.sg', 'status': 'In-Office'}
                                                             ]}})

            else:
                expected_data.append({
                    'date': date_str, 
                    'am': {'office': 5, 'wfh': 0,
                        'employees': [{'id': 140015, 'name': 'Oliva Lim', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Oliva.Lim@allinone.com.sg', 'status': 'In-Office'}, 
                            {'id': 140025, 'name': 'Emma Heng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Emma.Heng@allinone.com.sg', 'status': 'In-Office'}, 
                            {'id': 140108, 'name': 'Liam The', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Liam.The@allinone.com.sg', 'status': 'In-Office'}, 
                            {'id': 140115, 'name': 'Noah Ng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Noah.Ng@allinone.com.sg', 'status': 'In-Office'}, 
                            {'id': 140878, 'name': 'James Tong', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'James.Tong@allinone.com.sg', 'status': 'In-Office'}
                        ]}, 
                    'pm': {'office': 5, 'wfh': 0,
                        'employees': [{'id': 140015, 'name': 'Oliva Lim', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Oliva.Lim@allinone.com.sg', 'status': 'In-Office'}, 
                            {'id': 140025, 'name': 'Emma Heng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Emma.Heng@allinone.com.sg', 'status': 'In-Office'}, 
                            {'id': 140108, 'name': 'Liam The', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Liam.The@allinone.com.sg', 'status': 'In-Office'}, 
                            {'id': 140115, 'name': 'Noah Ng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Noah.Ng@allinone.com.sg', 'status': 'In-Office'}, 
                            {'id': 140878, 'name': 'James Tong', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'James.Tong@allinone.com.sg', 'status': 'In-Office'}
                        ]}
                })

            current_date += timedelta(days=1)
        # Make a request to your team schedule endpoint
        response = self.client.get('/api/schedule/team_schedule/140002')

        # Assert the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Get the actual data from the response
        actual_data = response.get_json()

        def rearrange_data(actual_data):
            # Initialize a list to hold the rearranged entries
            rearranged_data = []

            # Loop through each entry in actual_data
            for entry in actual_data:
                # Create a new entry with the desired order
                new_entry = {}
                new_entry['date'] = entry['date']

                # Process the 'am' section
                if 'employees' in entry['am']:
                    entry['am']['employees'].sort(key=lambda x: x['name'])  # Sorting AM employees by name
                    new_entry['am'] = {
                        'office': entry['am']['office'],  # Accessing office time in am
                        'wfh': entry['am']['wfh'],         # Accessing wfh time in am
                        'employees': entry['am']['employees']  # Directly adding the employees list
                    }
                else:
                    new_entry['am'] = {
                        'office': entry['am']['office'],  # Accessing office time in am
                        'wfh': entry['am']['wfh']           # Accessing wfh time in am
                    }

                # Process the 'pm' section
                if 'employees' in entry['pm']:
                    entry['pm']['employees'].sort(key=lambda x: x['name'])  # Sorting PM employees by name
                    new_entry['pm'] = {
                        'office': entry['pm']['office'],  # Accessing office time in pm
                        'wfh': entry['pm']['wfh'],         # Accessing wfh time in pm
                        'employees': entry['pm']['employees']  # Directly adding the employees list
                    }
                else:
                    new_entry['pm'] = {
                        'office': entry['pm']['office'],  # Accessing office time in pm
                        'wfh': entry['pm']['wfh']           # Accessing wfh time in pm
                    }

                # Append the new entry to the rearranged_data list
                rearranged_data.append(new_entry)

            return rearranged_data

        # Rearrange the actual data
        rearranged_actual_data = rearrange_data(actual_data)
        rearranged_expected_data = rearrange_data(expected_data)
        # print the element 61
        print("Actual Data:", rearranged_actual_data[61])
        print("Expected Data:", rearranged_expected_data[61])

        self.maxDiff = None


        # Assert that the actual data matches the expected data
        self.assertEqual(rearranged_actual_data, rearranged_expected_data)


    

    
    # Test Case: employee list
    def test_employee_list(self):
        response = self.client.get('api/schedule/employeelist/140002')

        # Assert the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Expected data
        expected_data = [
            {
                "EmployeeStrength": 5,
                "EmployeeList":
                    [
                        {"id": 140108, "name": "Liam The", "dept": "Sales", "position": "Account Manager", "email": "Liam.The@allinone.com.sg", "status": "In-Office"},
                        {"id": 140878, "name": "James Tong", "dept": "Sales", "position": "Account Manager", "email": "James.Tong@allinone.com.sg", "status": "In-Office"},
                        {"id": 140115, "name": "Noah Ng", "dept": "Sales", "position": "Account Manager", "email": "Noah.Ng@allinone.com.sg", "status": "In-Office"},
                        {"id": 140015, "name": "Oliva Lim", "dept": "Sales", "position": "Account Manager", "email": "Oliva.Lim@allinone.com.sg", "status": "In-Office"},
                        {"id": 140025, "name": "Emma Heng", "dept": "Sales", "position": "Account Manager", "email": "Emma.Heng@allinone.com.sg", "status": "In-Office"},
                    ]
            }
        ]

        # expected_data = [{'EmployeeStrength': 5, 'EmployeeList': [{'id': 140015, 'name': 'Olivia Lim', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Oliva.Lim@allinone.com.sg', 'status': 'In-Office'}, {'id': 140025, 'name': 'Emma Heng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Emma.Heng@allinone.com.sg', 'status': 'In-Office'}, {'id': 140108, 'name': 'Liam The', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Liam.The@allinone.com.sg', 'status': 'In-Office'}, {'id': 140115, 'name': 'Noah Ng', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'Noah.Ng@allinone.com.sg', 'status': 'In-Office'}, {'id': 140878, 'name': 'James Tong', 'dept': 'Sales', 'position': 'Account Manager', 'email': 'James.Tong@allinone.com.sg', 'status': 'In-Office'}]}]

        # Extract the actual data from the response
        actual_data = response.json

        # Sort both the expected and actual data before comparison
        sorted_actual_data = self.sort_employee_data(actual_data)
        sorted_expected_data = self.sort_employee_data(expected_data)

        # print("Actual Data:", sorted_actual_data)
        # print("----")
        # print("Expected Data:", sorted_expected_data)

        # Assert that the actual data matches the expected data
        self.assertEqual(sorted_actual_data, sorted_expected_data)


    def test_team_schedule_invalid_time_slot(self):
        with self.app.app_context():
            # Insert the invalid time slot application specific to this test case
            invalid_application = WFHApplication(
                staff_id=140025, time_slot="INVALID", 
                staff_apply_reason="test invalid time slot", manager_reject_reason=None
            )
            db.session.add(invalid_application)
            db.session.commit()

            invalid_schedule = WFHSchedule(
                application_id=invalid_application.application_id, 
                wfh_date=datetime.now().strftime('%Y-%m-%d'), 
                status="Approved", 
                manager_withdraw_reason=None
            )
            db.session.add(invalid_schedule)
            db.session.commit()

            # Capture stdout to intercept print statements
            captured_output = io.StringIO()
            sys.stdout = captured_output  # Redirect stdout to the StringIO object

            # Request the endpoint
            response = self.client.get('/api/schedule/team_schedule/140002')
            self.assertEqual(response.status_code, 200)

            # Restore stdout to default
            sys.stdout = sys.__stdout__

            # Extract the captured output
            output = captured_output.getvalue()

            # Verify the print message for the invalid time slot
            expected_message = f"Unexpected time slot 'INVALID' for staff_id: 140025 on {datetime.now().strftime('%Y-%m-%d')}\n"
            self.assertIn(expected_message, output)  # Assert that the expected message is in the captured output


if __name__ == '__main__':
    unittest.main()