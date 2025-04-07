import unittest
import datetime
import json
from app import create_app, db


class TestOwnSchedule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create the Flask app instance
        cls.app = create_app()
        cls.app.config['TESTING'] = True

        # Use MySQL running in the CI environment, matching the pipeline setup
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://spmwfh:Password123_@spmwfh.c1mimsiy0o6r.us-east-1.rds.amazonaws.com:3306/wfh'
        cls.client = cls.app.test_client()

        # No need to create schema or insert data here; it's done by the CI pipeline

    def test_own_schedule(self):
        # Test fetching the schedule for a specific staff ID
        response = self.client.get('/api/schedule/own/1001')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        print(json.dumps(data, indent=4))  # Print the JSON response in a pretty format
        self.assertGreater(len(data), 0)  # Ensure some schedules are returned

        # Parse the date string from the response and compare just the date part
       # date_str = data[0]['dateStart']
      #  date_obj = datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')  # Parse the returned format
     #   self.assertEqual(date_obj.strftime('%Y-%m-%d'), '2024-10-01')  # Compare only the date
        # Ensure 'dateStart' exists in the first element
        self.assertIn('dateStart', data[0], "dateStart key not found in the response.")
        
        # Parse the date string from the response
        date_str = data[0]['dateStart']
        
        # Use the correct format for ISO 8601 date string
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')  # Corrected format

        # Compare only the date part
        self.assertEqual(date_obj.strftime('%Y-%m-%d'), '2024-10-01', "Parsed date does not match expected date.")

        # Verify specific data from the response
      #  self.assertEqual(data[0]['slot'], 'AM')  # Check if the first schedule slot is 'AM'
       # self.assertEqual(data[0]['date'], '2024-10-01')  # Check if the first schedule date is '2024-10-01'

    @classmethod
    def tearDownClass(cls):
        # Clean up or rollback any necessary changes if required, but database drop isn't needed
        pass

if __name__ == "__main__":
    unittest.main()
