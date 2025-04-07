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

class TestOverallSchedule(unittest.TestCase):
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
        self.expected_end_date = self.today + relativedelta(months=3)- timedelta(days=1)
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
                # CEO
                Employee(staff_id=130002, staff_fname="Jack", staff_lname="Sim", dept="CEO", position="MD", country="Singapore", email="jack.sim@allinone.com.sg", reporting_manager=130002,role=1),

                # Consultancy
                # Director
                Employee(staff_id=180001, staff_fname="Ernst", staff_lname="Sim", dept="Consultancy", position="Director", country="Singapore", email="Ernst.Sim@allinone.com.sg", reporting_manager=130002,role=1),
                # Staff
                Employee(staff_id=180021, staff_fname="Amara", staff_lname="Kesavan", dept="Consultancy", position="Counsultant", country="Singapore", email="Amara.Kesavan@allinone.com.sg", reporting_manager=180001,role=2),

                # Engineering
                # Director
                Employee(staff_id=151408, staff_fname="Philip", staff_lname="Lee", dept="Engineering", position="Director", country="Singapore", email="Philip.Lee@allinone.com.sg", reporting_manager=130002,role=1),
                # Staff
                Employee(staff_id=151510, staff_fname="Anh", staff_lname="Ly", dept="Engineering", position="Operation Planning Team", country="Indonesia", email="Anh.Ly@allinone.com.id", reporting_manager=151408,role=2),

                # Finance
                # Director
                Employee(staff_id=170166, staff_fname="David", staff_lname="Yap", dept="Finance", position="Director", country="Singapore", email="David.Yap@allinone.com.sg", reporting_manager=130002,role=1),
                # Manager
                Employee(staff_id=171029, staff_fname="Chandra", staff_lname="Kong", dept="Finance", position="Finance Manager", country="Singapore", email="Chandra.Kong@allinone.com.sg", reporting_manager=170166,role=3),
                # Staff
                Employee(staff_id=171024, staff_fname="Anh", staff_lname="Kong", dept="Finance", position="Finance Executive", country="Singapore", email="Anh.Kong@allinone.com.sg", reporting_manager=171029,role=2),

                # HR
                # Director
                Employee(staff_id=160008, staff_fname="Sally", staff_lname="Loh", dept="HR", position="Director", country="Singapore", email="Sally.Loh@allinone.com.sg", reporting_manager=130002,role=1),
                # Staff
                Employee(staff_id=160155, staff_fname="Alexander", staff_lname="Heng", dept="HR", position="HR Team", country="Singapore", email="Alexander.Heng@allinone.com.sg", reporting_manager=160008,role=1),

                # IT
                # Director
                Employee(staff_id=210001, staff_fname="Peter", staff_lname="Yap", dept="IT", position="Director", country="Singapore", email="Peter.aypallinone.com.sg", reporting_manager=130002,role=1),
                # Staff
                Employee(staff_id=210028, staff_fname="An", staff_lname="Vo", dept="IT", position="IT Team", country="Singapore", email="An.Vo@allinone.com.sg", reporting_manager=210001,role=2),

                # Sales
                # Director
                Employee(staff_id=140001, staff_fname="Derek", staff_lname="Tan", dept="Sales", position="Director", country="Singapore", email="Derek.Tan@allinone.com.sg", reporting_manager=130002,role=1),
                # Manager
                Employee(staff_id=140879, staff_fname="Siti", staff_lname="Abdullah", dept="Sales", position="Sales Manager", country="Singapore", email="Siti.Abdullah@allinone.com.sg", reporting_manager=140001,role=3),
                # Staff
                Employee(staff_id=140929, staff_fname="Tat", staff_lname="Nguyen", dept="Sales", position="Account Manager", country="Hong Kong", email="Tat.Nguyen@allinone.com.hk", reporting_manager=140879,role=2),

                # Solutioning
                # Director
                Employee(staff_id=150008, staff_fname="Eric", staff_lname="Loh", dept="Solutioning", position="Director", country="Singapore", email="Eric.Loh@allinone.com.sg", reporting_manager=130002,role=1),
                # Staff
                Employee(staff_id=190077, staff_fname="Anhu", staff_lname="Pham", dept="Solutioning", position="Support Team", country="Singapore", email="Vietnam	Anhu.Pham@allinone.com.sg", reporting_manager=150008,role=2)
            ]
            db.session.add_all(employees)
            db.session.commit()

            applications = [
                # AM, PM, FULL
                # Approved, Pending Approval, Rejected, Withdrawn, Pending Withdrawal

                # First day, 2 months back
                # All directors
                WFHApplication(staff_id=130002, time_slot="AM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=180001, time_slot="AM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=151408, time_slot="AM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=170166, time_slot="PM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=160008, time_slot="PM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=210001, time_slot="PM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=140001, time_slot="FULL", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=150008, time_slot="FULL", staff_apply_reason="test overall view", manager_reject_reason=None),
                
                # Last day, 3 months forward
                # All managers, staff
                WFHApplication(staff_id=180021, time_slot="AM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=151510, time_slot="AM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=171029, time_slot="AM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=171024, time_slot="PM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=160155, time_slot="PM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=210028, time_slot="PM", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=140879, time_slot="FULL", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=140929, time_slot="FULL", staff_apply_reason="test overall view", manager_reject_reason=None),
                WFHApplication(staff_id=190077, time_slot="FULL", staff_apply_reason="test overall view", manager_reject_reason=None)
            ]

            db.session.add_all(applications)
            db.session.commit()

            schedules = [
                # First day, 2 months back
                WFHSchedule(application_id=applications[0].application_id, wfh_date=self.expected_start_date_formatted, status="Approved", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[1].application_id, wfh_date=self.expected_start_date_formatted, status="Pending_Approval", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[2].application_id, wfh_date=self.expected_start_date_formatted, status="Rejected", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[3].application_id, wfh_date=self.expected_start_date_formatted, status="Withdrawn", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[4].application_id, wfh_date=self.expected_start_date_formatted, status="Pending_Withdrawal", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[5].application_id, wfh_date=self.expected_start_date_formatted, status="Approved", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[6].application_id, wfh_date=self.expected_start_date_formatted, status="Pending_Approval", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[7].application_id, wfh_date=self.expected_start_date_formatted, status="Rejected", manager_withdraw_reason=None), # not visible

                # Last day, 3 months forward
                WFHSchedule(application_id=applications[8].application_id, wfh_date=self.expected_end_date_formatted, status="Withdrawn", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[9].application_id, wfh_date=self.expected_end_date_formatted, status="Pending_Withdrawal", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[10].application_id, wfh_date=self.expected_end_date_formatted, status="Approved", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[11].application_id, wfh_date=self.expected_end_date_formatted, status="Pending_Approval", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[12].application_id, wfh_date=self.expected_end_date_formatted, status="Rejected", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[13].application_id, wfh_date=self.expected_end_date_formatted, status="Withdrawn", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[14].application_id, wfh_date=self.expected_end_date_formatted, status="Pending_Withdrawal", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[15].application_id, wfh_date=self.expected_end_date_formatted, status="Approved", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[16].application_id, wfh_date=self.expected_end_date_formatted, status="Pending_Approval", manager_withdraw_reason=None) # not visible
            ]

            db.session.add_all(schedules)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise e
    
    def test_able_to_view_overall_schedule(self):
        print("OVS Test 1")
        # Simulate API call with the test client
        response = self.client.get("/api/schedule/HRO_overall")

        # Print the actual JSON response for debugging
        print("API Response:\n", response.json)

        # Assert the response status code is 200
        self.assertEqual(response.status_code, 200)
        
        # Expected data
        expected_data = [
            {
                "am": {
                "employees": [
                    {
                    "dept": "CEO",
                    "email": "jack.sim@allinone.com.sg",
                    "id": 130002,
                    "name": "Jack Sim",
                    "position": "MD",
                    "status": "WFH"
                    }
                ],
                "office": 16,
                "wfh": 1
                },
                "date": self.expected_start_date_formatted,
                "pm": {
                "employees": [
                    {
                    "dept": "IT",
                    "email": "Peter.aypallinone.com.sg",
                    "id": 210001,
                    "name": "Peter Yap",
                    "position": "Director",
                    "status": "WFH"
                    },
                    {
                    "dept": "HR",
                    "email": "Sally.Loh@allinone.com.sg",
                    "id": 160008,
                    "name": "Sally Loh",
                    "position": "Director",
                    "status": "WFH"
                    }
                ],
                "office": 15,
                "wfh": 2
                }
            },
            {
                "am": {
                "employees": [
                    {
                    "dept": "Engineering",
                    "email": "Anh.Ly@allinone.com.id",
                    "id": 151510,
                    "name": "Anh Ly",
                    "position": "Operation Planning Team",
                    "status": "WFH"
                    },
                    {
                    "dept": "Finance",
                    "email": "Chandra.Kong@allinone.com.sg",
                    "id": 171029,
                    "name": "Chandra Kong",
                    "position": "Finance Manager",
                    "status": "WFH"
                    },
                    {
                    "dept": "Sales",
                    "email": "Siti.Abdullah@allinone.com.sg",
                    "id": 140879,
                    "name": "Siti Abdullah",
                    "position": "Sales Manager",
                    "status": "WFH"
                    },
                    {
                    "dept": "Sales",
                    "email": "Tat.Nguyen@allinone.com.hk",
                    "id": 140929,
                    "name": "Tat Nguyen",
                    "position": "Account Manager",
                    "status": "WFH"
                    }
                ],
                "office": 13,
                "wfh": 4
                },
                "date": self.expected_end_date_formatted,
                "pm": {
                "employees": [
                    {
                    "dept": "Sales",
                    "email": "Siti.Abdullah@allinone.com.sg",
                    "id": 140879,
                    "name": "Siti Abdullah",
                    "position": "Sales Manager",
                    "status": "WFH"
                    },
                    {
                    "dept": "Sales",
                    "email": "Tat.Nguyen@allinone.com.hk",
                    "id": 140929,
                    "name": "Tat Nguyen",
                    "position": "Account Manager",
                    "status": "WFH"
                    }
                ],
                "office": 15,
                "wfh": 2
                }
            }
        ]

        # Extract the actual data from the response
        actual_data = [response.json[0], response.json[-1]]
        
        # Sorting data
        for item in expected_data:
            for session in ["am", "pm"]:
                item[session]["employees"].sort(key=lambda x: x["name"])

        for item in actual_data:
            for session in ["am", "pm"]:
                item[session]["employees"].sort(key=lambda x: x["name"])

        print("Actual Data:\n", actual_data)
        print("Expected Data:\n",expected_data)

        # Assert that the actual data matches the expected data
        self.assertEqual(actual_data, expected_data)
        if actual_data == expected_data:
            print("OVS Test 1 Passed")

    def test_HR_overall_invalid_time_slot(self):
        print("OVS Test 2")
        with self.app.app_context():
            # Insert the invalid time slot application specific to this test case
            invalid_application = WFHApplication(
                staff_id=160155, time_slot="INVALID", 
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
            response = self.client.get('/api/schedule/HRO_overall')
            self.assertEqual(response.status_code, 200)

            # Restore stdout to default
            sys.stdout = sys.__stdout__

            # Extract the captured output
            output = captured_output.getvalue()

            # Verify the print message for the invalid time slot
            expected_message = f"Unexpected time slot 'INVALID' for staff_id: 160155 on {self.expected_end_date_formatted}\n"
            self.assertIn(expected_message, output)  # Assert that the expected message is in the captured output
            if expected_message == output:
                print("OVS Test 2 Passed")

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
            ('/api/schedule/HRO_overall', OperationalError, 'Database connection issue.'),
            ('/api/schedule/HRO_overall',  Exception, 'An unexpected error occurred.'),
            ('/api/schedule/HRO_overall',  SQLAlchemyError, 'Database query failed.'),
        ]

        # Loop through each endpoint and perform the error tests
        for endpoint, exception_type, expected_message in endpoints:
            with self.subTest(endpoint=endpoint, exception=exception_type.__name__):
                self.perform_error_test(endpoint, exception_type, expected_message)

    

if __name__ == "__main__":
    unittest.main()
        