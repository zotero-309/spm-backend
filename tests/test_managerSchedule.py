from datetime import date
import sys
import os
import unittest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import io

from app import create_app, db
from app.models import Employee, WFHApplication, WFHSchedule

class TestManagerSchedule(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Set up the test client and in-memory database
        # set maxDiff to None due to large json
        self.maxDiff = None
        self.app = create_app(test_config=True)
        self.client = self.app.test_client()

        # date for testing 2 months back and 3 months forward
        self.today = datetime.now()
        self.expected_start_date = self.today - relativedelta(months=2)
        self.expected_end_date = self.today + relativedelta(months=3) - timedelta(days=1)
        self.expected_start_date_formatted = self.expected_start_date.strftime('%Y-%m-%d')
        self.expected_end_date_formatted = self.expected_end_date.strftime('%Y-%m-%d')
        
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
            employees = [
                # manager
                Employee(staff_id=140894, staff_fname="Rahim", staff_lname="Khalid", dept="Sales", position="Sales Manager", country="Singapore", email="Rahim.Khalid@allinone.com.sg", reporting_manager=None,role=3),
                # staff in team
                Employee(staff_id=140078, staff_fname="Amelia", staff_lname="Ong", dept="Sales", position="Account Manager", country="Singapore", email="Amelia.Ong@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140036, staff_fname="Charlotte", staff_lname="Wong", dept="Sales", position="Account Manager", country="Singapore", email="Charlotte.Wong@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140025, staff_fname="Emma", staff_lname="Heng", dept="Sales", position="Account Manager", country="Singapore", email="Emma.Heng@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140102, staff_fname="Eva", staff_lname="Yong", dept="Sales", position="Account Manager", country="Singapore", email="Eva.Yong@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140878, staff_fname="James", staff_lname="Tong", dept="Sales", position="Account Manager", country="Singapore", email="James.Tong@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140003, staff_fname="Janice", staff_lname="Chan", dept="Sales", position="Account Manager", country="Singapore", email="Janice.Chan@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140108, staff_fname="Liam", staff_lname="The", dept="Sales", position="Account Manager", country="Singapore", email="Liam.The@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140004, staff_fname="Mary", staff_lname="Teo", dept="Sales", position="Account Manager", country="Singapore", email="Mary.Teo@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140115, staff_fname="Noah", staff_lname="Ng", dept="Sales", position="Account Manager", country="Singapore", email="Noah.Ng@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140015, staff_fname="Olivia", staff_lname="Lim", dept="Sales", position="Account Manager", country="Singapore", email="Oliva.Lim@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140525, staff_fname="Oliver", staff_lname="Tan", dept="Sales", position="Account Manager", country="Singapore", email="Oliver.Tan@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140002, staff_fname="Susan", staff_lname="Goh", dept="Sales", position="Account Manager", country="Singapore", email="Susan.Goh@allinone.com.sg", reporting_manager=140894, role=2),
                Employee(staff_id=140736, staff_fname="William", staff_lname="Fu", dept="Sales", position="Account Manager", country="Singapore", email="William.Fu@allinone.com.sg", reporting_manager=140894, role=2)
            ]
            db.session.add_all(employees)
            db.session.commit()

            applications = [
                # include AM, PM and FULL applications
                # First day, 2 months back
                WFHApplication(staff_id=140078, time_slot="AM", staff_apply_reason="test manager view", manager_reject_reason=None),
                WFHApplication(staff_id=140036, time_slot="PM", staff_apply_reason="test manager view", manager_reject_reason=None),
                WFHApplication(staff_id=140025, time_slot="FULL", staff_apply_reason="test manager view", manager_reject_reason=None),

                # Last day, 3 months forward
                WFHApplication(staff_id=140102, time_slot="AM", staff_apply_reason="test manager view", manager_reject_reason=None),
                WFHApplication(staff_id=140878, time_slot="PM", staff_apply_reason="test manager view", manager_reject_reason=None),
                WFHApplication(staff_id=140003, time_slot="FULL", staff_apply_reason="test manager view", manager_reject_reason=None)
            ]

            db.session.add_all(applications)
            db.session.commit()

            schedules = [
                # First day, 2 months back
                WFHSchedule(application_id=applications[0].application_id, wfh_date=self.expected_start_date_formatted, status="Approved", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[1].application_id, wfh_date=self.expected_start_date_formatted, status="Approved", manager_withdraw_reason=None), # visible
                WFHSchedule(application_id=applications[2].application_id, wfh_date=self.expected_start_date_formatted, status="Pending_Approval", manager_withdraw_reason=None), # not visible

                # Last day, 3 months forward
                WFHSchedule(application_id=applications[3].application_id, wfh_date=self.expected_end_date_formatted, status="Rejected", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[4].application_id, wfh_date=self.expected_end_date_formatted, status="Withdrawn", manager_withdraw_reason=None), # not visible
                WFHSchedule(application_id=applications[5].application_id, wfh_date=self.expected_end_date_formatted, status="Pending_Withdrawal", manager_withdraw_reason=None) # visible
            ]

            db.session.add_all(schedules)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise e
    
    def test_manager_able_to_view_schedule(self):
        print("MVS Test 1")
        # Simulate API call with the test client
        response = self.client.get("/api/schedule/team_schedule_manager/140894")

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
                        "dept": "Sales",
                        "email": "Amelia.Ong@allinone.com.sg",
                        "id": 140078,
                        "name": "Amelia Ong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "WFH"
                    },
                    {
                        "dept": "Sales",
                        "email": "Charlotte.Wong@allinone.com.sg",
                        "id": 140036,
                        "name": "Charlotte Wong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Emma.Heng@allinone.com.sg",
                        "id": 140025,
                        "name": "Emma Heng",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Eva.Yong@allinone.com.sg",
                        "id": 140102,
                        "name": "Eva Yong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "James.Tong@allinone.com.sg",
                        "id": 140878,
                        "name": "James Tong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Janice.Chan@allinone.com.sg",
                        "id": 140003,
                        "name": "Janice Chan",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Liam.The@allinone.com.sg",
                        "id": 140108,
                        "name": "Liam The",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Mary.Teo@allinone.com.sg",
                        "id": 140004,
                        "name": "Mary Teo",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Noah.Ng@allinone.com.sg",
                        "id": 140115,
                        "name": "Noah Ng",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Oliva.Lim@allinone.com.sg",
                        "id": 140015,
                        "name": "Olivia Lim",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Oliver.Tan@allinone.com.sg",
                        "id": 140525,
                        "name": "Oliver Tan",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Susan.Goh@allinone.com.sg",
                        "id": 140002,
                        "name": "Susan Goh",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "William.Fu@allinone.com.sg",
                        "id": 140736,
                        "name": "William Fu",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    }
                    ],
                    "office": 12,
                    "wfh": 1
                },
                "date": self.expected_start_date_formatted,
                "pm": {
                    "employees": [
                    {
                        "dept": "Sales",
                        "email": "Amelia.Ong@allinone.com.sg",
                        "id": 140078,
                        "name": "Amelia Ong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Charlotte.Wong@allinone.com.sg",
                        "id": 140036,
                        "name": "Charlotte Wong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "WFH"
                    },
                    {
                        "dept": "Sales",
                        "email": "Emma.Heng@allinone.com.sg",
                        "id": 140025,
                        "name": "Emma Heng",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Eva.Yong@allinone.com.sg",
                        "id": 140102,
                        "name": "Eva Yong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "James.Tong@allinone.com.sg",
                        "id": 140878,
                        "name": "James Tong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Janice.Chan@allinone.com.sg",
                        "id": 140003,
                        "name": "Janice Chan",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Liam.The@allinone.com.sg",
                        "id": 140108,
                        "name": "Liam The",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Mary.Teo@allinone.com.sg",
                        "id": 140004,
                        "name": "Mary Teo",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Noah.Ng@allinone.com.sg",
                        "id": 140115,
                        "name": "Noah Ng",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Oliva.Lim@allinone.com.sg",
                        "id": 140015,
                        "name": "Olivia Lim",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Oliver.Tan@allinone.com.sg",
                        "id": 140525,
                        "name": "Oliver Tan",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Susan.Goh@allinone.com.sg",
                        "id": 140002,
                        "name": "Susan Goh",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "William.Fu@allinone.com.sg",
                        "id": 140736,
                        "name": "William Fu",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    }
                    ],
                    "office": 12,
                    "wfh": 1
                }
            },
            {
                "am": {
                    "employees": [
                    {
                        "dept": "Sales",
                        "email": "Amelia.Ong@allinone.com.sg",
                        "id": 140078,
                        "name": "Amelia Ong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Charlotte.Wong@allinone.com.sg",
                        "id": 140036,
                        "name": "Charlotte Wong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Emma.Heng@allinone.com.sg",
                        "id": 140025,
                        "name": "Emma Heng",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Eva.Yong@allinone.com.sg",
                        "id": 140102,
                        "name": "Eva Yong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "James.Tong@allinone.com.sg",
                        "id": 140878,
                        "name": "James Tong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Janice.Chan@allinone.com.sg",
                        "id": 140003,
                        "name": "Janice Chan",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "WFH"
                    },
                    {
                        "dept": "Sales",
                        "email": "Liam.The@allinone.com.sg",
                        "id": 140108,
                        "name": "Liam The",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Mary.Teo@allinone.com.sg",
                        "id": 140004,
                        "name": "Mary Teo",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Noah.Ng@allinone.com.sg",
                        "id": 140115,
                        "name": "Noah Ng",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Oliva.Lim@allinone.com.sg",
                        "id": 140015,
                        "name": "Olivia Lim",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Oliver.Tan@allinone.com.sg",
                        "id": 140525,
                        "name": "Oliver Tan",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Susan.Goh@allinone.com.sg",
                        "id": 140002,
                        "name": "Susan Goh",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "William.Fu@allinone.com.sg",
                        "id": 140736,
                        "name": "William Fu",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    }
                    ],
                    "office": 12,
                    "wfh": 1
                },
                "date": self.expected_end_date_formatted,
                "pm": {
                    "employees": [
                    {
                        "dept": "Sales",
                        "email": "Amelia.Ong@allinone.com.sg",
                        "id": 140078,
                        "name": "Amelia Ong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Charlotte.Wong@allinone.com.sg",
                        "id": 140036,
                        "name": "Charlotte Wong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Emma.Heng@allinone.com.sg",
                        "id": 140025,
                        "name": "Emma Heng",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Eva.Yong@allinone.com.sg",
                        "id": 140102,
                        "name": "Eva Yong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "James.Tong@allinone.com.sg",
                        "id": 140878,
                        "name": "James Tong",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Janice.Chan@allinone.com.sg",
                        "id": 140003,
                        "name": "Janice Chan",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "WFH"
                    },
                    {
                        "dept": "Sales",
                        "email": "Liam.The@allinone.com.sg",
                        "id": 140108,
                        "name": "Liam The",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Mary.Teo@allinone.com.sg",
                        "id": 140004,
                        "name": "Mary Teo",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Noah.Ng@allinone.com.sg",
                        "id": 140115,
                        "name": "Noah Ng",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Oliva.Lim@allinone.com.sg",
                        "id": 140015,
                        "name": "Olivia Lim",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Oliver.Tan@allinone.com.sg",
                        "id": 140525,
                        "name": "Oliver Tan",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "Susan.Goh@allinone.com.sg",
                        "id": 140002,
                        "name": "Susan Goh",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    },
                    {
                        "dept": "Sales",
                        "email": "William.Fu@allinone.com.sg",
                        "id": 140736,
                        "name": "William Fu",
                        "position": "Account Manager",
                        "reporting_manager": 140894,
                        "role": 2,
                        "status": "In-Office"
                    }
                    ],
                    "office": 12,
                    "wfh": 1
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
        self.assertAlmostEqual(actual_data, expected_data)
        if actual_data == expected_data:
            print("MVS Test 1 Passed")
    
    def test_manager_able_to_view_team(self):
        print("MVS Test 2")
        # Simulate API call with the test client
        response = self.client.get("/api/schedule/manageremployeelist/140894")

        # Print the actual JSON response for debugging
        print("API Response:\n", response.json)

        # Assert the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Expected data
        expected_data = [
            {
                "EmployeeList": [
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Amelia.Ong@allinone.com.sg",
                    "id": 140078,
                    "name": "Amelia Ong",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Charlotte.Wong@allinone.com.sg",
                    "id": 140036,
                    "name": "Charlotte Wong",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Emma.Heng@allinone.com.sg",
                    "id": 140025,
                    "name": "Emma Heng",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Eva.Yong@allinone.com.sg",
                    "id": 140102,
                    "name": "Eva Yong",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "James.Tong@allinone.com.sg",
                    "id": 140878,
                    "name": "James Tong",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Janice.Chan@allinone.com.sg",
                    "id": 140003,
                    "name": "Janice Chan",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Liam.The@allinone.com.sg",
                    "id": 140108,
                    "name": "Liam The",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Mary.Teo@allinone.com.sg",
                    "id": 140004,
                    "name": "Mary Teo",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Noah.Ng@allinone.com.sg",
                    "id": 140115,
                    "name": "Noah Ng",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Oliva.Lim@allinone.com.sg",
                    "id": 140015,
                    "name": "Olivia Lim",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Oliver.Tan@allinone.com.sg",
                    "id": 140525,
                    "name": "Oliver Tan",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "Susan.Goh@allinone.com.sg",
                    "id": 140002,
                    "name": "Susan Goh",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    },
                    {
                    "country": "Singapore",
                    "dept": "Sales",
                    "email": "William.Fu@allinone.com.sg",
                    "id": 140736,
                    "name": "William Fu",
                    "position": "Account Manager",
                    "reporting_manager": 140894,
                    "role": 2,
                    "status": "In-Office"
                    }
                ],
                "EmployeeStrength": 13
            }
        ]
        
        # Extract the actual data from the response
        actual_data = response.json

        # Sorting data
        sorted_expected_data = [ { "EmployeeList": sorted( expected_data[0]["EmployeeList"], key=lambda x: x["name"] ), "EmployeeStrength": expected_data[0]["EmployeeStrength"] } ]
        sorted_actual_data = [ { "EmployeeList": sorted( actual_data[0]["EmployeeList"], key=lambda x: x["name"] ), "EmployeeStrength": actual_data[0]["EmployeeStrength"] } ]
        print("Actual Data:\n", actual_data)
        print("Expected Data:\n", expected_data)

        # Assert that the actual data matches the expected data
        self.assertEqual(sorted_actual_data, sorted_expected_data)
        if sorted_actual_data == sorted_expected_data:
            print("MVS Test 2 Passed")

    def test_manager_invalid_time_slot(self):
        print("MVS Test 3")
        with self.app.app_context():
            # Insert the invalid time slot application specific to this test case
            invalid_application = WFHApplication(
                staff_id=140078, time_slot="INVALID", 
                staff_apply_reason="test invalid time slot", manager_reject_reason=None
            )
            db.session.add(invalid_application)
            db.session.commit()

            invalid_schedule = WFHSchedule(
                application_id=invalid_application.application_id, 
                wfh_date=self.expected_start_date_formatted, 
                status="Approved", 
                manager_withdraw_reason=None
            )
            db.session.add(invalid_schedule)
            db.session.commit()

            # Capture stdout to intercept print statements
            captured_output = io.StringIO()
            sys.stdout = captured_output  # Redirect stdout to the StringIO object

            # Request the endpoint
            response = self.client.get('/api/schedule/team_schedule_manager/140894')
            self.assertEqual(response.status_code, 200)

            # Restore stdout to default
            sys.stdout = sys.__stdout__

            # Extract the captured output
            output = captured_output.getvalue()

            # Verify the print message for the invalid time slot
            expected_message = f"Unexpected time slot 'INVALID' for staff_id: 140078 on {self.expected_start_date_formatted}\n"
            self.assertIn(expected_message, output)  # Assert that the expected message is in the captured output
            if expected_message == output:
                print("MVS Test 3 Passed")

if __name__ == "__main__":
    unittest.main()