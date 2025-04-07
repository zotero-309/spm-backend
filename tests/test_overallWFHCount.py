from datetime import date
import sys
import os
import unittest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from operator import itemgetter
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from unittest.mock import patch
import io

from app import create_app, db
from app.models import Employee, WFHApplication, WFHSchedule

class TestOverallWFHCount(unittest.TestCase):
    @classmethod
    def setUp(self):
        # Set up the test client and in-memory database
        # set maxDiff to None due to large json
        self.maxDiff = None
        self.app = create_app(test_config=True)
        self.client = self.app.test_client()

        # date for testing 2 months back and 3 months forward
        self.today = datetime.now()
        self.expected_start_date = self.today - relativedelta(months=2)
        self.expected_end_date = self.today + relativedelta(months=3)
        self.expected_start_date_formatted = self.expected_start_date.strftime("%Y-%m-%d")
        self.expected_end_date_formatted = self.expected_end_date.strftime("%Y-%m-%d")
        
        # Push the application context and initialize the database
        with self.app.app_context():
            db.create_all()  # Create tables for the test
            self.populate_test_data(self)  # Populate some initial test data if needed


    @classmethod
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def populate_test_data(self):
        try:
            employees = [
                # managers, needed for reporting manager to not be None
                Employee(staff_id=151408, staff_fname="Philip", staff_lname="Lee", dept="Engineering", position="Director", country="Singapore", email="Philip.Lee@allinone.com.sg", reporting_manager=151408,role=1),
                

                # staff from each department
                Employee(staff_id=130002, staff_fname="Jack", staff_lname="Sim", dept="CEO", position="MD", country="Singapore", email="jack.sim@allinone.com.sg", reporting_manager=None,role=1),
                Employee(staff_id=150518, staff_fname="Aiden", staff_lname="Chan", dept="Engineering", position="Call Centre", country="Singapore", email="Aiden.Chan@allinone.com.sg", reporting_manager=151408,role=2),
                Employee(staff_id=171029, staff_fname="Chandra", staff_lname="Kong", dept="Finance", position="Finance Manager", country="Singapore", email="Chandra.Kong@allinone.com.sg", reporting_manager=151408,role=3),
                Employee(staff_id=160155, staff_fname="Alexander", staff_lname="Heng", dept="HR", position="HR Team", country="Singapore", email="Alexander.Heng@allinone.com.sg", reporting_manager=171029,role=2),
                ]
            db.session.add_all(employees)
            db.session.commit()

            applications = [
                # include AM, PM and FULL applications
                # First day, 2 months back
                WFHApplication(staff_id=150518, time_slot="AM", staff_apply_reason="test manager view", manager_reject_reason=None),
                WFHApplication(staff_id=171029, time_slot="PM", staff_apply_reason="test manager view", manager_reject_reason=None),
                WFHApplication(staff_id=160155, time_slot="FULL", staff_apply_reason="test manager view", manager_reject_reason=None),

                # Last day, 3 months forward
                WFHApplication(staff_id=150518, time_slot="AM", staff_apply_reason="test manager view", manager_reject_reason=None),
                WFHApplication(staff_id=171029, time_slot="PM", staff_apply_reason="test manager view", manager_reject_reason=None),
            ]

            db.session.add_all(applications)
            db.session.commit()

            schedules = [
                # First day, 2 months back
                WFHSchedule(application_id=applications[0].application_id, wfh_date=self.expected_start_date_formatted, status="Approved", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[1].application_id, wfh_date=self.expected_start_date_formatted, status="Approved", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[2].application_id, wfh_date=self.expected_start_date_formatted, status="Approved", manager_withdraw_reason=None), # not visible

                # # Last day, 3 months forward
                WFHSchedule(application_id=applications[0].application_id, wfh_date=self.expected_end_date_formatted, status="Rejected", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[1].application_id, wfh_date=self.expected_end_date_formatted, status="Withdrawn", manager_withdraw_reason=None), # not visible
            ]

            db.session.add_all(schedules)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise e

    def test_wfh_count_overall(self):
        print("VOS Test 1")
        today = datetime.now()
        start_date = today - relativedelta(months=2)
        end_date = today + relativedelta(months=3) - timedelta(days=1)

        # Generate the expected data dynamically
        # expected_data = self.generate_expected_team_schedule(start_date, end_date)
        expected_data = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str == self.expected_start_date_formatted:
                expected_data.append({'date': date_str, 
                                      'am': {'wfh': 2, 'office': 1, 
                                             'employees': [
                                                 {'id': 150518, 'name': 'Aiden Chan', 'dept': 'Engineering', 'position': 'Call Centre', 'email': 'Aiden.Chan@allinone.com.sg', 'status': 'WFH'}, 
                                                #  {'id': 171029, 'name': 'Chandra Kong', 'dept': 'Finance', 'position': 'Finance Manager', 'email': 'Chandra.Kong@allinone.com.sg', 'status': 'In-Office'}, 
                                                 {'id': 160155, 'name': 'Alexander Heng', 'dept': 'HR', 'position': 'HR Team', 'email': 'Alexander.Heng@allinone.com.sg', 'status': 'WFH'}
                                                           ]}, 
                                        'pm': {'wfh': 2, 'office': 1, 
                                               'employees': [
                                                #    {'id': 150518, 'name': 'Aiden Chan', 'dept': 'Engineering', 'position': 'Call Centre', 'email': 'Aiden.Chan@allinone.com.sg', 'status': 'In-Office'}, 
                                                   {'id': 171029, 'name': 'Chandra Kong', 'dept': 'Finance', 'position': 'Finance Manager', 'email': 'Chandra.Kong@allinone.com.sg', 'status': 'WFH'}, 
                                                   {'id': 160155, 'name': 'Alexander Heng', 'dept': 'HR', 'position': 'HR Team', 'email': 'Alexander.Heng@allinone.com.sg', 'status': 'WFH'}
                                                             ]}})

            else:
                expected_data.append({
                    'date': date_str, 
                    'am': {'office': 3, 'wfh': 0}, 
                    'pm': {'office': 3, 'wfh': 0}
                })

            current_date += timedelta(days=1)
        # Make a request to your team schedule endpoint
        response = self.client.get("/api/schedule/HRO_wfh_count/151408")

        # Assert the response status code is 200
        self.assertEqual(response.status_code, 200)



        # Get the actual data from the response
        actual_data = response.get_json()

        print("NOT ARRANGED actual:", actual_data[152])
        print("NOT ARRANGED expected:",expected_data[152])

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

        # print("actual:", rearranged_actual_data[153])
        # print("expected:",rearranged_expected_data[153])

        self.maxDiff = None
        self.assertEqual(rearranged_actual_data, rearranged_expected_data)
        if rearranged_actual_data == rearranged_expected_data:
            print("VOS Test 1 Passed")

    def test_HR_WFHCount_invalid_time_slot(self):
        with self.app.app_context():
            # Insert the invalid time slot application specific to this test case
            invalid_application = WFHApplication(
                staff_id=150518, time_slot="INVALID", 
                staff_apply_reason="test invalid time slot", manager_reject_reason=None
            )
            db.session.add(invalid_application)
            db.session.commit()

            invalid_schedule = WFHSchedule(
                application_id=invalid_application.application_id, 
                wfh_date=self.expected_end_date_formatted, 
                status="Approved", 
                manager_withdraw_reason=None
            )
            db.session.add(invalid_schedule)
            db.session.commit()

            # Capture stdout to intercept print statements
            captured_output = io.StringIO()
            sys.stdout = captured_output  # Redirect stdout to the StringIO object

            # Request the endpoint
            response = self.client.get('/api/schedule/HRO_wfh_count/151408')
            self.assertEqual(response.status_code, 200)

            # Restore stdout to default
            sys.stdout = sys.__stdout__

            # Extract the captured output
            output = captured_output.getvalue()

            # Verify the print message for the invalid time slot
            expected_message = f"Unexpected time slot 'INVALID' for staff_id: 150518 on {self.expected_end_date_formatted}\n"
            self.assertIn(expected_message, output)  # Assert that the expected message is in the captured output

    # Assertion in the loop below
    def perform_error_test(self, endpoint, exception_type, expected_message):
        with patch.object(db.session, 'query') as mock_query:
            # Set the appropriate exception based on the test
            mock_query.side_effect = exception_type("Simulated Error", None, None)
            
            # Make the request to the endpoint
            response = self.client.get(endpoint)
            
            # Validate the response
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json['error'], expected_message)

    # Collecting API Endpoints
    def test_error_handling_for_endpoints(self):
        # Define the endpoints and exceptions to test
        endpoints = [
            ('/api/schedule/HRO_wfh_count/151408', OperationalError, 'Database connection issue.'),
            ('/api/schedule/HRO_wfh_count/151408', Exception, 'An unexpected error occurred.'),
            ('/api/schedule/HRO_wfh_count/151408', SQLAlchemyError, 'Database query failed.'),
        ]

        # Loop through each endpoint and perform the error tests
        for endpoint, exception_type, expected_message in endpoints:
            with self.subTest(endpoint=endpoint, exception=exception_type.__name__):
                self.perform_error_test(endpoint, exception_type, expected_message)

if __name__ == "__main__":
    unittest.main()