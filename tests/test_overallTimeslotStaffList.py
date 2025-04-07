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

class TestOverallWFHTimeSlotStaffList(unittest.TestCase):
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

    def test_wfh_timeslot_AM(self):
        print("OVS Test 3")
        # Simulate API call with the test client
        response = self.client.get("/api/schedule/HRO_wfh_slot_stafflist/151408/" + datetime.now().strftime('%Y-%m-%d') + "/AM")

        # Print the actual JSON response for debugging
        print("API Response:\n", response.json)

        # Assert the response status code is 200
        self.assertEqual(response.status_code, 200)
        
        # Expected data
        expected_data = [
            {'AM': {'employees': [{'country': 'Singapore', 'dept': 'Engineering', 'email': 'Aiden.Chan@allinone.com.sg', 'id': 150518, 'name': 'Aiden Chan', 'position': 'Call Centre', 'reporting_manager': 151408, 'role': 2, 'status': 'In-Office'}, 
                                  {'country': 'Singapore', 'dept': 'HR', 'email': 'Alexander.Heng@allinone.com.sg', 'id': 160155, 'name': 'Alexander Heng', 'position': 'HR Team', 'reporting_manager': 171029, 'role': 2, 'status': 'In-Office'}, 
                                  {'country': 'Singapore', 'dept': 'Finance', 'email': 'Chandra.Kong@allinone.com.sg', 'id': 171029, 'name': 'Chandra Kong', 'position': 'Finance Manager', 'reporting_manager': 151408, 'role': 3, 'status': 'In-Office'}], 
                                  'office': 3, 'wfh': 0}, 
                                  'date': datetime.now().strftime('%Y-%m-%d')}
        ]

        # Extract the actual data from the response
        actual_data = response.json
        expected_data.sort(key=lambda x: x["date"])
        for entry in expected_data:
            if "employees" in entry.get("AM", {}):
                entry["AM"]["employees"].sort(key=lambda emp: emp["id"])
            if "employees" in entry.get("PM", {}):
                entry["PM"]["employees"].sort(key=lambda emp: emp["id"])
        
        actual_data.sort(key=lambda x: x["date"])
        for entry in actual_data:
            if "employees" in entry.get("AM", {}):
                entry["AM"]["employees"].sort(key=lambda emp: emp["id"])
            if "employees" in entry.get("PM", {}):
                entry["PM"]["employees"].sort(key=lambda emp: emp["id"])

        print("Actual Data:\n", actual_data)
        print("Expected Data:\n",expected_data)
        

        # Assert that the actual data matches the expected data
        self.assertEqual(actual_data, expected_data)
        if actual_data == expected_data:
            print("OVS Test 3 Passed")

    def test_wfh_timeslot_PM(self):
        print("OVS Test 4")
        # Simulate API call with the test client
        response = self.client.get("/api/schedule/HRO_wfh_slot_stafflist/151408/" + datetime.now().strftime('%Y-%m-%d') + "/PM")

        # Print the actual JSON response for debugging
        print("API Response:\n", response.json)

        # Assert the response status code is 200
        self.assertEqual(response.status_code, 200)
        
        # Expected data
        expected_data = [
            {'PM': {'employees': [{'country': 'Singapore', 'dept': 'Engineering', 'email': 'Aiden.Chan@allinone.com.sg', 'id': 150518, 'name': 'Aiden Chan', 'position': 'Call Centre', 'reporting_manager': 151408, 'role': 2, 'status': 'In-Office'}, 
                                  {'country': 'Singapore', 'dept': 'HR', 'email': 'Alexander.Heng@allinone.com.sg', 'id': 160155, 'name': 'Alexander Heng', 'position': 'HR Team', 'reporting_manager': 171029, 'role': 2, 'status': 'In-Office'}, 
                                  {'country': 'Singapore', 'dept': 'Finance', 'email': 'Chandra.Kong@allinone.com.sg', 'id': 171029, 'name': 'Chandra Kong', 'position': 'Finance Manager', 'reporting_manager': 151408, 'role': 3, 'status': 'In-Office'}], 
                                  'office': 3, 'wfh': 0}, 
                                  'date': datetime.now().strftime('%Y-%m-%d')}
        ]

        # Extract the actual data from the response
        actual_data = response.json
        expected_data.sort(key=lambda x: x["date"])
        for entry in expected_data:
            if "employees" in entry.get("AM", {}):
                entry["AM"]["employees"].sort(key=lambda emp: emp["id"])
            if "employees" in entry.get("PM", {}):
                entry["PM"]["employees"].sort(key=lambda emp: emp["id"])
        
        actual_data.sort(key=lambda x: x["date"])
        for entry in actual_data:
            if "employees" in entry.get("AM", {}):
                entry["AM"]["employees"].sort(key=lambda emp: emp["id"])
            if "employees" in entry.get("PM", {}):
                entry["PM"]["employees"].sort(key=lambda emp: emp["id"])

        print("Actual Data:\n", actual_data)
        print("Expected Data:\n",expected_data)
        

        # Assert that the actual data matches the expected data
        self.assertEqual(actual_data, expected_data)
        if actual_data == expected_data:
            print("OVS Test 4 Passed")

    def test_wfh_count_day_AM(self):
        print("OVS Test 5")
        expected_data = []
        expected_data.append({'date': self.expected_start_date_formatted, 
                                      'AM': {'wfh': 2, 'office': 1, 
                                             'employees': [
                                                 {'id': 150518, 'name': 'Aiden Chan', 'dept': 'Engineering', 'position': 'Call Centre', 'email': 'Aiden.Chan@allinone.com.sg', 'status': 'WFH', 'country': 'Singapore', 'reporting_manager':151408,'role':2}, 
                                                 {'id': 171029, 'name': 'Chandra Kong', 'dept': 'Finance', 'position': 'Finance Manager', 'email': 'Chandra.Kong@allinone.com.sg', 'status': 'In-Office', 'country': 'Singapore', 'reporting_manager':151408,'role':3}, 
                                                 {'id': 160155, 'name': 'Alexander Heng', 'dept': 'HR', 'position': 'HR Team', 'email': 'Alexander.Heng@allinone.com.sg', 'status': 'WFH', 'country': 'Singapore', 'reporting_manager':171029,'role':2}
                                                           ]}})

        # Make a request to your team schedule endpoint
        response = self.client.get("/api/schedule/HRO_wfh_slot_stafflist/151408/" + self.expected_start_date_formatted + "/AM")

        # Assert the response status code is 200
        self.assertEqual(response.status_code, 200)

        actual_data = response.get_json()

        self.assertEqual(actual_data, expected_data)
        if actual_data == expected_data:
            print("OVS Test 5 Passed")

    def test_wfh_count_day_PM(self):
        print("OVS Test 6")
        expected_data = []
        expected_data.append({'date': self.expected_start_date_formatted, 
                                      'PM': {'wfh': 2, 'office': 1, 
                                             'employees': [
                                                 {'id': 150518, 'name': 'Aiden Chan', 'dept': 'Engineering', 'position': 'Call Centre', 'email': 'Aiden.Chan@allinone.com.sg', 'status': 'In-Office', 'country': 'Singapore', 'reporting_manager':151408,'role':2}, 
                                                 {'id': 171029, 'name': 'Chandra Kong', 'dept': 'Finance', 'position': 'Finance Manager', 'email': 'Chandra.Kong@allinone.com.sg', 'status': 'WFH', 'country': 'Singapore', 'reporting_manager':151408,'role':3}, 
                                                 {'id': 160155, 'name': 'Alexander Heng', 'dept': 'HR', 'position': 'HR Team', 'email': 'Alexander.Heng@allinone.com.sg', 'status': 'WFH', 'country': 'Singapore', 'reporting_manager':171029,'role':2}
                                                           ]}})

        # Make a request to your team schedule endpoint
        response = self.client.get("/api/schedule/HRO_wfh_slot_stafflist/151408/" + self.expected_start_date_formatted + "/PM")

        # Assert the response status code is 200
        self.assertEqual(response.status_code, 200)



        # Get the actual data from the response
        actual_data = response.get_json()

        self.assertEqual(actual_data, expected_data)
        if actual_data == expected_data:
            print("OVS Test 6 Passed")

    def test_invalid_time_slot(self):
        print("OVS Test 7")
        # Simulate API call with the test client
        response = self.client.get("/api/schedule/HRO_wfh_slot_stafflist/151408/" + self.expected_end_date_formatted + "/FULL")

        self.assertEqual(response.status_code, 400)

        response_data = response.get_json()

        # Assert the error message
        self.assertEqual(response_data, {"error": "The slot value can only be 'AM' or 'PM'."})
        if response_data == {"error": "The slot value can only be 'AM' or 'PM'."}:
            print("OVS Test 7 Passed")
    

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
            ("/api/schedule/HRO_wfh_slot_stafflist/151408/" + self.expected_end_date_formatted + "/AM", OperationalError, 'Database connection issue.'),
            ("/api/schedule/HRO_wfh_slot_stafflist/151408/" + self.expected_end_date_formatted + "/AM", Exception, 'An unexpected error occurred.'),
            ("/api/schedule/HRO_wfh_slot_stafflist/151408/" + self.expected_end_date_formatted + "/AM", SQLAlchemyError, 'Database query failed.'),
        ]

        # Loop through each endpoint and perform the error tests
        for endpoint, exception_type, expected_message in endpoints:
            with self.subTest(endpoint=endpoint, exception=exception_type.__name__):
                self.perform_error_test(endpoint, exception_type, expected_message)

if __name__ == "__main__":
    unittest.main()