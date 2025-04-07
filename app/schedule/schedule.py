import math
from flask import jsonify, request
from app.schedule import schedule_blueprint  # Import the blueprint
from app import db
from app.models import WFHApplication, WFHSchedule, Employee
from sqlalchemy import and_,or_
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math
@schedule_blueprint.route('/own/<int:id>', methods=['GET'])
def own_schedule(id):
    # '''
    # Function: WFH application and schedule tables are joined, personal wfh dates are extracted
    # Error considered (server side):
    # 1. Database connection issue
    # 2. Databse Query fail
    # '''
    """
    Get own WFH schedule by staff ID.
    ---
    tags:
        - Schedules
    description: Returns WFH and in-office status of the staff's team for each day.
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: The staff ID to fetch the WFH schedule for.
    responses:
      200:
        description: A list of schedules for the staff.
        schema:
          type: array
          items:
            type: object
            properties:
              label:
                type: string
              dateStart:
                type: string
              dateEnd:
                type: string
              class:
                type: string
              description:
                type: string
      500:
        description: Server error.
    """
    try:
        # Query the WFH schedules for the staff
        wfh_arrs = db.session.query(WFHSchedule).join(WFHApplication).filter(
            WFHApplication.staff_id == id, 
            or_(WFHApplication.manager_reject_reason.is_(None), WFHApplication.manager_reject_reason == ''), 
            or_(WFHSchedule.manager_withdraw_reason.is_(None), WFHSchedule.manager_withdraw_reason == ''),
            or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Approval', WFHSchedule.status == 'Pending_Withdrawal')
        ).all()
        


        # Initialise return list
        schedule_list = []
        # Create a list of schedules with time_slot and wfh_date
        for schedule in wfh_arrs:

                # Extract the year, month, and day
                date = schedule.wfh_date
                year = date.year
                month = date.month
                day = date.day

                if schedule.application.time_slot == "AM":
                    start_time = 9
                    end_time = 13
                elif schedule.application.time_slot == "PM":
                    start_time = 14
                    end_time = 18
                else: #full day
                    start_time = 9
                    end_time = 18

                schedule_list.append(
                    {'label': schedule.application.time_slot,
                    'dateStart': datetime(year, month, day, start_time, 0).isoformat(), 
                    'dateEnd': datetime(year, month, day, end_time, 0).isoformat(),
                    'class': schedule.status,
                    'description': schedule.application.staff_apply_reason
                    }
                    )
            

        return jsonify(schedule_list), 200
    
    except OperationalError as e:
        print('Database connection issue.')
        return jsonify({'error': 'Database connection issue.'}), 500

    except SQLAlchemyError as e:
        print('Database query failed.')
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    # Catch unexpected errors (everything else)
    except Exception as e:
        print('error: An unexpected error occurred.')
        return jsonify({'error': 'An unexpected error occurred.'}), 500



# Route to get staff-related info based on manager
@schedule_blueprint.route('/team_schedule_manager/<int:staff_id>', methods=['GET'])
def team_schedule_manager(staff_id):
    response = []
    
    # Retrieve the manager based on the provided staff_id
    manager = Employee.query.filter_by(staff_id=staff_id).first()
    
    # Initialize the team list and add all staff who report to the manager
    team = []
    for staff in Employee.query.filter_by(reporting_manager=manager.staff_id).all(): 
        team.append(staff)

    # Fetch all "Approved" and "Pending_Withdrawal" WFH records for the team
    wfh_records = (
        db.session.query(
            Employee.staff_id,
            Employee.staff_fname,
            Employee.staff_lname,
            WFHApplication.application_id,
            WFHSchedule.wfh_date,
            WFHApplication.time_slot
        )
        .join(WFHApplication, Employee.staff_id == WFHApplication.staff_id)
        .join(WFHSchedule, WFHApplication.application_id == WFHSchedule.application_id)
        .filter(
            Employee.staff_id.in_([staff.staff_id for staff in team]),
            or_(
                WFHSchedule.status == "Approved",
                WFHSchedule.status == "Pending_Withdrawal"
            )
        )
        .all()
    )

    # Dictionary to store WFH records categorized by date and time slots (AM, PM, FULL)
    wfh_dict = {}

    # Valid time slots
    valid_time_slots = ["AM", "PM", "FULL"]

    # Process the fetched WFH records
    for record in wfh_records:
        date_str = str(record.wfh_date)
        
        # Initialize the dictionary for the date if it doesn't exist
        if date_str not in wfh_dict:
            wfh_dict[date_str] = {"AM": [], "PM": [], "FULL": []}
        
        # Check if the time slot is valid, then append the staff_id accordingly
        if record.time_slot in valid_time_slots:
            wfh_dict[date_str][record.time_slot].append(record.staff_id)
        else:
            # Handle unexpected time slot with a log message
            print(f"Unexpected time slot '{record.time_slot}' for staff_id: {record.staff_id} on {date_str}")

    # Define the current date and the date range (2 months back, 3 months forward)
    today = datetime.now()
    start_date = today - relativedelta(months=2)  # 2 months back
    end_date = today + relativedelta(months=3) - timedelta(days=1)   # 3 months forward

    # Get the total number of staff members in the team
    total_staff_strength = len(team)

    # Iterate over each day within the defined date range
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Initialize lists to store staff IDs for different statuses (WFH, In-Office)
        office_am = []
        office_pm = []
        wfh_am = []
        wfh_pm = []
        employees_am = []
        employees_pm = []
        employees_default = []
        
        # If there are WFH records for the current date, process them
        if date_str in wfh_dict:
            for staff in team:
                full_name = staff.staff_fname + " " + staff.staff_lname
                
                # Handle full-day WFH case
                if staff.staff_id in wfh_dict[date_str]["FULL"]:
                    wfh_am.append(staff.staff_id)
                    employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH", "role": staff.role, "reporting_manager": staff.reporting_manager})
                    wfh_pm.append(staff.staff_id)
                    employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH", "role": staff.role, "reporting_manager": staff.reporting_manager})
                else:
                    # Handle AM WFH slot
                    if staff.staff_id in wfh_dict[date_str]["AM"]:
                        wfh_am.append(staff.staff_id)
                        employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH", "role": staff.role, "reporting_manager": staff.reporting_manager})
                    else:
                        # Mark as "In-Office" if not WFH in AM
                        office_am.append(staff.staff_id)
                        employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "In-Office", "role": staff.role, "reporting_manager": staff.reporting_manager})

                    # Handle PM WFH slot
                    if staff.staff_id in wfh_dict[date_str]["PM"]:
                        wfh_pm.append(staff.staff_id)
                        employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH", "role": staff.role, "reporting_manager": staff.reporting_manager})
                    else:
                        # Mark as "In-Office" if not WFH in PM
                        office_pm.append(staff.staff_id)
                        employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "In-Office", "role": staff.role, "reporting_manager": staff.reporting_manager})

            # Append the day's summary to the response
            response.append({
                "date": date_str, 
                "am": {"wfh": len(wfh_am), "office": len(office_am), "employees": employees_am}, 
                "pm": {"wfh": len(wfh_pm), "office": len(office_pm), "employees": employees_pm}
            })
        else:
            # Default case if no WFH records exist for the date
            while len(employees_default) != total_staff_strength:
                for staff in team:
                    full_name = staff.staff_fname + " " + staff.staff_lname
                    employees_default.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "In-Office", "role": staff.role, "reporting_manager": staff.reporting_manager})

            # Append the default "In-Office" status to the response
            response.append({
                "date": date_str, 
                "am": {"wfh": 0, "office": total_staff_strength, "employees": employees_default}, 
                "pm": {"wfh": 0, "office": total_staff_strength, "employees": employees_default}
            })

        # Move to the next day in the range
        current_date += timedelta(days=1)
    
    # Return the JSON response with the WFH and In-Office status per day
    return jsonify(response), 200

# Route to get the list of employees under a manager
@schedule_blueprint.route('/manageremployeelist/<int:staff_id>', methods=['GET'])
def employeelist_manager(staff_id):
    # Initialize response list
    response = []

    # Retrieve the manager details using staff_id
    manager = Employee.query.filter_by(staff_id=staff_id).first()
    
    # Initialize the list of team members under the manager
    team = []
    # Loop through all employees that report to the manager
    for staff in Employee.query.filter_by(reporting_manager=manager.staff_id).all():
        team.append(staff)

    # Initialize the employee list to be sent in response
    employees = []
    # Loop through each staff in the manager's team
    for staff in team:
        # Construct the full name of the employee
        full_name = staff.staff_fname + " " + staff.staff_lname
        # Add employee details to the list
        employees.append({
            "id": staff.staff_id, 
            "name": full_name, 
            "dept": staff.dept, 
            "position": staff.position, 
            "email": staff.email, 
            "status": "In-Office", 
            "role": staff.role, 
            "reporting_manager": staff.reporting_manager, 
            "country": staff.country
        })
    
    # Add employee list and strength of the team to the response
    response.append({
        "EmployeeStrength": len(team),
        "EmployeeList": employees
    })

    # Return the response in JSON format with status code 200 (OK)
    return jsonify(response), 200


# Route to get the work-from-home (WFH) schedule for a manager's team
@schedule_blueprint.route('/team_schedule/<int:staff_id>', methods=['GET'])
def team_schedule(staff_id):
    # Initialize response list
    response = []

    # Retrieve the staff member and their manager using the staff_id
    staff_member = Employee.query.filter_by(staff_id=staff_id).first()
    manager = Employee.query.filter_by(staff_id=staff_member.reporting_manager).first()
    
    # Initialize the list of team members under the manager
    team = []
    # Add all employees who report to the manager, excluding the current staff member
    for staff in Employee.query.filter_by(reporting_manager=manager.staff_id).all():
        if staff.staff_id != staff_member.staff_id: 
            team.append(staff)
    
    # Query all approved or pending withdrawal WFH records for the team
    wfh_records = (
        db.session.query(
            Employee.staff_id,
            Employee.staff_fname,
            Employee.staff_lname,
            WFHApplication.application_id,
            WFHSchedule.wfh_date,
            WFHApplication.time_slot
        )
        .join(WFHApplication, Employee.staff_id == WFHApplication.staff_id)
        .join(WFHSchedule, WFHApplication.application_id == WFHSchedule.application_id)
        .filter(
            Employee.staff_id.in_([staff.staff_id for staff in team]),
            or_(
                WFHSchedule.status == "Approved",
                WFHSchedule.status == "Pending_Withdrawal"
            )
        )
        .all()
    )

    # Initialize a dictionary to store WFH records by date and time slot
    wfh_dict = {}

    # Define valid time slots
    valid_time_slots = ["AM", "PM", "FULL"]

    # Process each WFH record and categorize them by date and time slot
    for record in wfh_records:
        date_str = str(record.wfh_date)
        
        # Initialize date entry in wfh_dict if it doesn't exist
        if date_str not in wfh_dict:
            wfh_dict[date_str] = {"AM": [], "PM": [], "FULL": []}
        
        # Add staff to the appropriate time slot
        if record.time_slot in valid_time_slots:
            wfh_dict[date_str][record.time_slot].append(record.staff_id)
        else:
            # Log unexpected time slots
            print(f"Unexpected time slot '{record.time_slot}' for staff_id: {record.staff_id} on {date_str}")
            
    # Get the current date
    today = datetime.now()

    # Set the date range to 2 months back and 3 months forward
    start_date = today - relativedelta(months=2)
    end_date = today + relativedelta(months=3)
    total_staff_strength = len(team)

    # Iterate over each day in the date range
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Lists to keep track of WFH and office presence in AM and PM slots
        office_am = []
        office_pm = []
        wfh_am = []
        wfh_pm = []
        employees_am = []
        employees_pm = []

        # If the current date has WFH records, process them
        if date_str in wfh_dict:
            for staff in team:
                full_name = staff.staff_fname + " " + staff.staff_lname
                
                # If staff has full-day WFH, mark both AM and PM as WFH
                if staff.staff_id in wfh_dict[date_str]["FULL"]:
                    wfh_am.append(staff.staff_id)
                    employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH"})
                    wfh_pm.append(staff.staff_id)
                    employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH"})
                else:
                    # If staff is WFH in AM, otherwise mark as in-office
                    if staff.staff_id in wfh_dict[date_str]["AM"]:
                        wfh_am.append(staff.staff_id)
                        employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH"})
                    else:
                        office_am.append(staff.staff_id)
                        employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "In-Office"})

                    # If staff is WFH in PM, otherwise mark as in-office
                    if staff.staff_id in wfh_dict[date_str]["PM"]:
                        wfh_pm.append(staff.staff_id)
                        employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH"})
                    else:
                        office_pm.append(staff.staff_id)
                        employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "In-Office"})

            # Append the day's AM/PM breakdown to the response
            response.append({
                "date": date_str, 
                "am": {"wfh": len(wfh_am), "office": len(office_am), "employees": employees_am}, 
                "pm": {"wfh": len(wfh_pm), "office": len(office_pm), "employees": employees_pm}
            })
        else:
            # If no WFH records exist for the date, assume all are in-office
            employees = []
            for staff in team:
                full_name = staff.staff_fname + " " + staff.staff_lname
                employees.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "In-Office"})
            
            # Append default in-office status for both AM and PM
            response.append({
                "date": date_str, 
                "am": {"wfh": 0, "office": total_staff_strength, "employees": employees}, 
                "pm": {"wfh": 0, "office": total_staff_strength, "employees": employees}
            })
        
        # Move to the next day
        current_date += timedelta(days=1)

    # Return the response in JSON format with status code 200 (OK)
    return jsonify(response), 200




# Employee List
@schedule_blueprint.route('/employeelist/<int:staff_id>', methods=['GET'])
def employeelist(staff_id):
    
    response = []

    
    # retrieve staff member and manager
    staff_member = Employee.query.filter_by(staff_id=staff_id).first()
    manager = Employee.query.filter_by(staff_id=staff_member.reporting_manager).first()
    
    # add all staff to the same team
    team = []
    # team.append(manager)
    for staff in Employee.query.filter_by(reporting_manager=manager.staff_id).all():
        if staff.staff_id != staff_member.staff_id: 
            team.append(staff)

    employees = []
    for staff in team:
        full_name = staff.staff_fname + " " + staff.staff_lname
        employees.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "In-Office"})
            

    response.append({
        "EmployeeStrength": len(team),
        "EmployeeList": employees
    })

    return jsonify(response), 200


@schedule_blueprint.route('/HRO_overall', methods=['GET'])
def overall_schedule_everyone():
    """
    Returns consolidated WFH count of all employees in the organisation for overall schedule display.
    ---
    tags:
      - HR View Overall Schedule
    responses:
      200:
        description: Successful response with the WFH status of entire organisation.
      500:
        description: Internal server error.
    """
    try:
        response = []
        # Retrieve all employees in the organization
        team = db.session.query(Employee).all()

        # Fetch all WFH records where the status is either 'Approved' or 'Pending_Withdrawal'
        wfh_records = db.session.query(Employee.staff_id, Employee.staff_fname, Employee.staff_lname, WFHApplication.application_id, WFHSchedule.wfh_date, WFHApplication.time_slot)\
            .join(WFHApplication, Employee.staff_id == WFHApplication.staff_id)\
            .join(WFHSchedule, WFHApplication.application_id == WFHSchedule.application_id)\
            .filter(or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Withdrawal')).all()

        # Dictionary to store WFH records by date and time slots
        wfh_dict = {}

        # Valid time slots for WFH (AM, PM, FULL)
        valid_time_slots = ["AM", "PM", "FULL"]

        # Loop through all WFH records and populate the dictionary based on the date and time slot
        for record in wfh_records:
            date_str = str(record.wfh_date)
            
            # Initialize the dictionary for each date if not already present
            if date_str not in wfh_dict:
                wfh_dict[date_str] = {"AM": [], "PM": [], "FULL": []}
            
            # Ensure the time slot is valid before adding it to the dictionary
            if record.time_slot in valid_time_slots:
                wfh_dict[date_str][record.time_slot].append(record.staff_id)
            else:
                # Handle unexpected time slot values (for debugging purposes)
                print(f"Unexpected time slot '{record.time_slot}' for staff_id: {record.staff_id} on {date_str}")

        # Get today's date
        today = datetime.now()

        # Define the date range to display (2 months back to 3 months forward)
        start_date = today - relativedelta(months=2)  # 2 months back
        end_date = today + relativedelta(months=3) - timedelta(days=1)   # 3 months forward
        total_staff_strength = len(team)  # Total number of employees

        # Iterate over the specified date range, day by day
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            office_am = []  # List to hold staff who are in-office in the morning
            office_pm = []  # List to hold staff who are in-office in the afternoon
            wfh_am = []     # List to hold staff working from home in the morning
            wfh_pm = []     # List to hold staff working from home in the afternoon
            employees_am = []  # List to store details of employees in the morning
            employees_pm = []  # List to store details of employees in the afternoon

            # If there are WFH records for the current date
            if date_str in wfh_dict:
                # Loop through all employees to determine their WFH or in-office status for the current date
                for staff in team:
                    full_name = staff.staff_fname + " " + staff.staff_lname

                    # If the employee is working from home the entire day
                    if staff.staff_id in wfh_dict[date_str]["FULL"]:
                        wfh_am.append(staff.staff_id)
                        employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH"})
                        wfh_pm.append(staff.staff_id)
                        employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH"})
                    else:
                        # Check if the employee is working from home in the morning (AM)
                        if staff.staff_id in wfh_dict[date_str]["AM"]:
                            wfh_am.append(staff.staff_id)
                            employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH"})
                        else:
                            # If not working from home, mark them as in-office in the morning
                            office_am.append(staff.staff_id)
                        
                        # Check if the employee is working from home in the afternoon (PM)
                        if staff.staff_id in wfh_dict[date_str]["PM"]:
                            wfh_pm.append(staff.staff_id)
                            employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH"})
                        else:
                            # If not working from home, mark them as in-office in the afternoon
                            office_pm.append(staff.staff_id)

                # Add the date's information to the response with morning and afternoon WFH and in-office counts
                response.append({
                    "date": date_str, 
                    "am": {"wfh": len(wfh_am), "office": len(office_am), "employees": employees_am}, 
                    "pm": {"wfh": len(wfh_pm), "office": len(office_pm), "employees": employees_pm}
                })
            else:
                # If no WFH records exist for the current date, assume all employees are in-office
                response.append({
                    "date": date_str, 
                    "am": {"wfh": 0, "office": total_staff_strength, "employees": []}, 
                    "pm": {"wfh": 0, "office": total_staff_strength, "employees": []}
                })

            # Move to the next day in the date range
            current_date += timedelta(days=1)

        # Return the response with the consolidated WFH and in-office information
        return jsonify(response), 200
    
    except OperationalError as e:
        # Handle database connection errors
        return jsonify({'error': 'Database connection issue.'}), 500

    except SQLAlchemyError as e:
        # Rollback any database changes in case of a query failure
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    except Exception as e:
        # Handle any other unexpected errors
        return jsonify({'error': 'An unexpected error occurred.'}), 500


@schedule_blueprint.route('/HRO_wfh_count/<int:staff_id>', methods=['GET'])
def HRO_wfh_count(staff_id):
    """
    Returns conslidated WFH count of all employees below input staff_id for overall schedule display.
    ---
    tags:
      - HR View Overall Schedule
    parameters:
      - name: staff_id
        in: path
        required: true
        description: ID of the staff member whose team is being queried.
        type: integer
        default: 140001
    responses:
      200:
        description: Successful response with the WFH status of team members.
      500:
        description: Internal server error.
    """
    
    def find_team(manager_id):
        # Get all staff who report to the given manager
        team = Employee.query.filter_by(reporting_manager=manager_id).all()
        full_team = []  # Store all team members

        for staff in team:
            # Add the current staff member to the team list
            if staff.staff_id != manager_id and staff.staff_id != staff.reporting_manager:  # Avoid adding the manager themselves
                full_team.append(staff)
            
            # Recursively check if this staff is a manager and find their subordinates
            if staff.role != 2 and staff.staff_id != staff.reporting_manager:
                subordinates = find_team(staff.staff_id)
                full_team.extend(subordinates)  # Add all subordinates to the full team

        return full_team
    try: 
        response = []

        # Retrieve the initial staff member
        staff_member = Employee.query.filter_by(staff_id=staff_id).first()

        # Find all team members under the staff member
        full_team = find_team(staff_member.staff_id)

        # Fetch all WFH records
        wfh_records = db.session.query(Employee.staff_id, Employee.staff_fname, Employee.staff_lname, WFHApplication.application_id, WFHSchedule.wfh_date, WFHApplication.time_slot).join(WFHApplication, Employee.staff_id == WFHApplication.staff_id).join(WFHSchedule, WFHApplication.application_id == WFHSchedule.application_id).filter(Employee.staff_id.in_([staff.staff_id for staff in full_team]), or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Withdrawal')).all()

        # Dictionary to store WFH records by date and time slots
        wfh_dict = {}

        # Valid time slots
        valid_time_slots = ["AM", "PM", "FULL"]
        

        for record in wfh_records:
            date_str = str(record.wfh_date)
            
            # Initialize the dictionary for the date if it doesn't exist
            if date_str not in wfh_dict:
                wfh_dict[date_str] = {"AM": [], "PM": [], "FULL": []}
            
            # Check if the time slot is valid
            if record.time_slot in valid_time_slots:
                wfh_dict[date_str][record.time_slot].append(record.staff_id)
            else:
                # Handle unexpected time slot
                print(f"Unexpected time slot '{record.time_slot}' for staff_id: {record.staff_id} on {date_str}")

        # Get the current date
        today = datetime.now()

        # Calculate the date range: 2 months back, 3 months forward
        start_date = today - relativedelta(months=2)  # 2 months back
        end_date = today + relativedelta(months=3) - timedelta(days=1)   # 3 months forward
        total_staff_strength = len(full_team)

        # Iterate over the date range day by day
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            office_am = []
            office_pm = []
            wfh_am = []
            wfh_pm = []
            employees_am = []
            employees_pm = []

            if date_str in wfh_dict:
                # Process the team for this specific date
                for staff in full_team:
                    full_name = staff.staff_fname + " " + staff.staff_lname

                    # If staff has a full-day WFH record
                    if date_str in wfh_dict and staff.staff_id in wfh_dict[date_str]["FULL"]:
                        wfh_am.append(staff.staff_id)
                        employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.    position, "email": staff.email, "status": "WFH"})
                        wfh_pm.append(staff.staff_id)
                        employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.    position, "email": staff.email, "status": "WFH"})
                    else:
                        # Check AM slot
                        if date_str in wfh_dict and staff.staff_id in wfh_dict[date_str]["AM"]:
                            wfh_am.append(staff.staff_id)
                            employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position":   staff.position, "email": staff.email, "status": "WFH"})
                        else:
                            office_am.append(staff.staff_id)
                        #     employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position":     staff.position, "email": staff.email, "status": "In-Office"})

                        # Check PM slot
                        if date_str in wfh_dict and staff.staff_id in wfh_dict[date_str]["PM"]:
                            wfh_pm.append(staff.staff_id)
                            employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position":   staff.position, "email": staff.email, "status": "WFH"})
                        else:
                            office_pm.append(staff.staff_id)
                        #     employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position":     staff.position, "email": staff.email, "status": "In-Office"})

                # Append the date's information to the response
                response.append({
                    "date": date_str, 
                    "am": {"wfh": len(wfh_am), "office": len(office_am), "employees": employees_am}, 
                    "pm": {"wfh": len(wfh_pm), "office": len(office_pm), "employees": employees_pm}
                })
            else:
                # If the date doesn't exist in wfh_dict, append a default entry
                response.append({
                    "date": date_str, 
                    "am": {"wfh": 0, "office": total_staff_strength}, 
                    "pm": {"wfh": 0, "office": total_staff_strength}
                })

            # Move to the next day
            current_date += timedelta(days=1)
        return jsonify(response), 200
    
    except OperationalError as e:
        return jsonify({'error': 'Database connection issue.'}), 500

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    # Catch unexpected errors (everything else)
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred.'}), 500

@schedule_blueprint.route('/HRO_wfh_slot_stafflist/<int:staff_id>/<date>/<slot>', methods=['GET'])
def HRO_wfh_slot_stafflist(staff_id, date, slot):
    """
    Get list of WFH status of employees under the staff_id for a specific date and time slot.
    ---
    tags:
      - HR View Overall Schedule
    description: 'WARNING: selectedSlot passed into the axios MUST be in caps eg. "AM" or "PM". small letter "am" or "pm" will not work'
    parameters:
      - name: staff_id
        in: path
        required: true
        description: ID of the staff member (default id sales, Derek Tan).
        type: integer
        default: 140001
      - name: date
        in: path
        required: true
        description: Date in YYYY-MM-DD format.
        type: string
        default: "2024-10-01"
      - name: slot
        in: path
        required: true
        description: Time slot ('AM' or 'PM').
        type: string
        enum:
          - AM
          - PM
    responses:
      200:
        description: Successful response with WFH status of all staffs below staff_id.
      400:
        description: Invalid slot value.
      500:
        description: Internal server error.
    """
    # Check if the slot is "FULL" and return an error
    if slot != "AM" and slot != "PM":
        return jsonify({"error": "The slot value can only be 'AM' or 'PM'."}), 400
    
    def find_team(manager_id):
        # Get all staff who report to the given manager
        team = Employee.query.filter_by(reporting_manager=manager_id).all()
        full_team = []  # Store all team members

        for staff in team:
            # Add the current staff member to the team list
            if staff.staff_id != manager_id and staff.staff_id != staff.reporting_manager:  # Avoid adding the manager themselves
                full_team.append(staff)
            
            # Recursively check if this staff is a manager and find their subordinates
            if staff.role != 2 and staff.staff_id != staff.reporting_manager:
                subordinates = find_team(staff.staff_id)
                full_team.extend(subordinates)  # Add all subordinates to the full team

        return full_team
    
    try: 
        response = []

        # Retrieve the initial staff member
        staff_member = Employee.query.filter_by(staff_id=staff_id).first()

        # Find all team members under the staff member
        full_team = find_team(staff_member.staff_id)

        # Fetch all WFH records for the specified date
        wfh_records = db.session.query(Employee.staff_id, Employee.staff_fname, Employee.staff_lname, WFHApplication.application_id, WFHSchedule.wfh_date, WFHApplication.time_slot).join(WFHApplication, Employee.staff_id == WFHApplication.staff_id).join(WFHSchedule, WFHApplication.application_id == WFHSchedule.application_id).filter(Employee.staff_id.in_([staff.staff_id for staff in full_team]), WFHSchedule.wfh_date == date, or_(WFHApplication.time_slot == slot, WFHApplication.time_slot == 'FULL'), or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Withdrawal')).all()

        # Dictionary to store WFH records by date and time slots
        wfh_dict = {}
        

        # Valid time slots
        # valid_time_slots = ["AM", "PM", "FULL"]
        
        if wfh_records:
            for record in wfh_records:
                date_str = str(record.wfh_date)


                # Initialize the dictionary for the date if it doesn't exist
                if date_str not in wfh_dict:
                    wfh_dict[date_str] = {"AM": [], "PM": [], "FULL": []}

                # Check if the time slot is valid
                # if record.time_slot in valid_time_slots:
                wfh_dict[date_str][record.time_slot].append(record.staff_id)
                # else:
                #     # Handle unexpected time slot
                #     print(f"Unexpected time slot '{record.time_slot}' for staff_id: {record.staff_id} on {date_str}")


            # Process the specific date for the team
            office_am = []
            office_pm = []
            wfh_am = []
            wfh_pm = []
            employees_am = []
            employees_pm = []

            # Process the team for this specific date
            for staff in full_team:
                full_name = staff.staff_fname + " " + staff.staff_lname

                # If staff has a full-day WFH record
                if date in wfh_dict and staff.staff_id in wfh_dict[date]["FULL"]:
                    wfh_am.append(staff.staff_id)
                    employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH", "role": staff.role, "reporting_manager": staff.reporting_manager,"country": staff.country})
                    wfh_pm.append(staff.staff_id)
                    employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH", "role": staff.role, "reporting_manager": staff.reporting_manager,"country": staff.country})
                else:
                    # Check AM slot
                    if date in wfh_dict and staff.staff_id in wfh_dict[date]["AM"]:
                        wfh_am.append(staff.staff_id)
                        employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH", "role": staff.role, "reporting_manager": staff.reporting_manager,"country": staff.country})
                    else:
                        office_am.append(staff.staff_id)
                        employees_am.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "In-Office", "role": staff.role,   "reporting_manager": staff.reporting_manager,"country": staff.country})

                    # Check PM slot
                    if date in wfh_dict and staff.staff_id in wfh_dict[date]["PM"]:
                        wfh_pm.append(staff.staff_id)
                        employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "WFH", "role": staff.role, "reporting_manager": staff.reporting_manager,"country": staff.country})
                    else:
                        office_pm.append(staff.staff_id)
                        employees_pm.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "In-Office", "role": staff.role, "reporting_manager": staff.reporting_manager,"country": staff.country})

            # Append the date's information to the response
            if slot == "AM":
                response.append({
                    "date": date, 
                    "AM": {"wfh": len(wfh_am), "office": len(office_am), "employees": employees_am}
                })
            if slot == "PM":
                response.append({
                    "date": date, 
                    "PM": {"wfh": len(wfh_pm), "office": len(office_pm), "employees": employees_pm}
                })
            return jsonify(response), 200
        else:
            office = []
            employees = []
            for staff in full_team:
                full_name = staff.staff_fname + " " + staff.staff_lname

                office.append(staff.staff_id)
                employees.append({"id": staff.staff_id, "name": full_name, "dept": staff.dept, "position": staff.position, "email": staff.email, "status": "In-Office", "role": staff.role, "reporting_manager": staff.reporting_manager,"country": staff.country})
            
            if slot == "AM":
                response.append({
                    "date": date, 
                    "AM": {"wfh": 0, "office": len(office), "employees": employees}
                })
            if slot == "PM":
                response.append({
                    "date": date, 
                    "PM": {"wfh": 0, "office": len(office), "employees": employees}
                })
            return jsonify(response), 200
    
    except OperationalError as e:
        return jsonify({'error': 'Database connection issue.'}), 500

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    # Catch unexpected errors (everything else)
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred.'}), 500

