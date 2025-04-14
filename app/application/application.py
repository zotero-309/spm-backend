import math
from flask import jsonify, request
from app.application import application_blueprint  # Import the blueprint
from app import db
from app.models import WFHApplication, WFHSchedule,Employee, WFHWithdrawal
from sqlalchemy import and_,or_
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

@application_blueprint.route('/apply/<int:id>', methods=['POST'])
def apply_wfh(id):
    # '''
    # Function:
    # 1. Receive a JSON body of {"time_slot": "AM", "apply_reason":"", "start_date":"2024-10-10", "end_date":"2024-10-10" }
    # 2. Check if database has existing application for same date but not rejected
    # 3. If conflicts --> return error
    # 4. If no conflict --> update db and return success application

    # Error considered (server side):
    # 1. Json data not sent (400)
    # 2. Application already exist
    # 3. Recurring dates overlaps with existing applications
    # 4. Database connection issue (500)
    # 5. Databse Query fail (500)

    # '''
    """
    Submit WFH application
    ---
    tags:
      - Apply
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            time_slot:
              type: string
            apply_reason:
              type: string
            start_date:
              type: string
              format: date
            end_date:
              type: string
              format: date
    responses:
      201:
        description: WFH application submitted successfully
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    try:
        # get the JSON data from the request
        # assumes the format of {"time_slot": "AM", "apply_reason":"", "start_date":"2024-10-10", "end_date":"2024-10-10" }
        json_data = request.get_json()
        if not json_data: # checks for first possible error
            return jsonify({"error": "JSON data passed from client side is insufficient"}), 400

        # checks if wfh application is day request or recurring
        date_list = [] 

        json_data['start_date'] = datetime.strptime(json_data['start_date'] , '%Y-%m-%dT%H:%M:%S.%fZ')
        json_data['start_date'] = json_data['start_date'].strftime('%Y-%m-%d')

        json_data['end_date'] = datetime.strptime(json_data['end_date'] , '%Y-%m-%dT%H:%M:%S.%fZ')
        json_data['end_date'] = json_data['end_date'].strftime('%Y-%m-%d')



        if json_data['start_date'] == json_data['end_date']: #same day request
            date_list.append(json_data["start_date"])
        else:
            # base on start date, start date is tue means every tue, end date doesnt have to include
            start_date = datetime.strptime(json_data['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(json_data['end_date'], '%Y-%m-%d')
            current_date = start_date
            while current_date <= end_date:
                date_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=7)
                
        if json_data["time_slot"] == "AM" or json_data["time_slot"] == "PM":
            conflict_wfh_count = db.session.query(WFHApplication).join(WFHSchedule).filter(
                WFHApplication.staff_id == id,
                WFHSchedule.wfh_date.in_(date_list),
                or_(WFHApplication.time_slot == json_data["time_slot"],WFHApplication.time_slot == "FULL"),
                or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Approval', WFHSchedule.status == 'Pending_Withdrawal')
                ).count()
        else:
            
            conflict_wfh_count = db.session.query(WFHApplication).join(WFHSchedule).filter(
                WFHApplication.staff_id == id,
                WFHSchedule.wfh_date.in_(date_list),
                or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Approval', WFHSchedule.status == 'Pending_Withdrawal')
                ).count()
            
        

        # Case where there is no current application in that slot that is Approved or pending
        if conflict_wfh_count == 0:
            
            # Create a WFHApplication instance (parent table)
            new_application = WFHApplication(
                staff_id=id,
                time_slot=json_data['time_slot'],
                staff_apply_reason=json_data['apply_reason'],
                manager_reject_reason=None  # Set to None initially, can be updated later
            )
        
            # Add the WFHApplication (parent)
            db.session.add(new_application)
            db.session.flush()  # Flush to get the application_id for the next step

            # Instantly approves CEO when he applies WFH
            if id == 130002:
                new_status = 'Approved'
            else:
                new_status = 'Pending_Approval'

            for date_inst in date_list:
                # Create a WFHSchedule instance (child table) using the foreign key (application_id)
                    
                new_schedule = WFHSchedule(
                    application_id=new_application.application_id,  # Use the ID from the parent
                    wfh_date=date_inst,
                    status=new_status,  # Initial status, can be updated later (REMOVED staff_withdraw_reason here 13/10)
                    manager_withdraw_reason=None
                )

                # Add the WFHSchedule (child)
                db.session.add(new_schedule)
            # Commit the transaction to save both the parent and child objects
            db.session.commit()
            return jsonify({'success': 'Application Success!'}), 201
        
        elif conflict_wfh_count > 0 and len(date_list) == 1: 
            #situation where there is conflict for day request
            return jsonify({'error': 'Application already exists!'}), 400
        elif len(date_list) != conflict_wfh_count:
            #situation where some of scheduled wfh is already
            return jsonify({'error': 'Application already exists on some recurring days!'}), 400
        else:
            return jsonify({'error': 'Application already exists!'}), 400
        
    except OperationalError as e:
        return jsonify({'error': 'Database connection issue.'}), 500

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    # Catch unexpected errors (everything else)
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred.'}), 500

@application_blueprint.route('/withdraw/<int:id>', methods=['POST'])
def withdrawal_wfh(id):
    """
    Withdraw WFH application
    ---
    tags:
      - Withdraw
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            time_slot:
              type: string
              description: Time slot for the WFH request (AM/PM/FULL)
            staff_withdraw_reason:
              type: string
              description: Reason for withdrawal
            date:
              type: string
              format: date
              description: Date of the WFH request to withdraw (YYYY-MM-DD format)
    responses:
      201:
        description: Withdrawal successful
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    try:
        # get the JSON data from the request
        json_data = request.get_json()
        if not json_data: # checks for first possible error
            return jsonify({"error": "JSON data passed from client side is insufficient"}), 400

        json_data['date'] = datetime.strptime(json_data['date'] , '%Y-%m-%dT%H:%M:%S.%fZ')
        json_data['date'] = json_data['date'].strftime('%Y-%m-%d')


        schedule_entry = db.session.query(WFHSchedule).join(WFHApplication).filter(
            WFHApplication.staff_id == id,
            WFHApplication.time_slot == json_data['time_slot'],
            WFHSchedule.wfh_date == json_data['date'],
            WFHSchedule.status == json_data['status']
            ).first()

        if schedule_entry:
            # Extract the year, month, and day
            date = schedule_entry.wfh_date
            year = date.year
            month = date.month
            day = date.day

            # Example current date (you can replace this with datetime.now() to get today's date)
            current_date = datetime.now()

            # Example Approved arrangement date (replace this with your actual date)
            Approved_arrangement_date = datetime(year, month, day)  # example date in YYYY, MM, DD format

            # Define the time range of 2 weeks
            two_weeks = timedelta(weeks=2)

            # Check if the Approved arrangement date is more than 2 weeks backward or 2 weeks forward
            if current_date < (Approved_arrangement_date - two_weeks) or current_date > (Approved_arrangement_date + two_weeks):
                # Here, you can handle the case when data should not be stored
                
                return jsonify({'failed': 'cannot withdraw!'}),201

            new_withdrawal_reason = WFHWithdrawal(
                wfh_id=schedule_entry.wfh_id,
                staff_withdraw_reason=json_data['staff_withdraw_reason']
            )
            db.session.add(new_withdrawal_reason)


            if (schedule_entry.status == "Approved" and id != 130002):
                schedule_entry.status = "Pending_Withdrawal"
                db.session.commit()
                return jsonify({'success': 'Sending Manager for Approval'}), 201
            elif schedule_entry.status == "Pending_Approval" or id == 130002:
                schedule_entry.status = "Withdrawn"

                db.session.commit()
                return jsonify({'success': 'Application Success!'}), 201
            else:
                return jsonify({"error": "JSON data passed from client side is insufficient or wrong"}), 404
        else:
            return jsonify({"error": "JSON data passed from client side is insufficient or wrong"}), 404
        
        
    except OperationalError as e:
        print("OperationalError:", str(e))  # Add this for debugging
        return jsonify({'error': f'Database connection issue: {str(e)}'}), 500


    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    # Catch unexpected errors (everything else)
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred.'}), 500 

    
    

@application_blueprint.route('/wfhrequest/<int:id>', methods=['GET'])
def display_wfh_request(id):
    # need group recurring together
    try:
        wfh_arrs = db.session.query(WFHSchedule).join(WFHApplication, WFHSchedule.application_id == WFHApplication.application_id).join(Employee, Employee.staff_id == WFHApplication.staff_id).join(WFHWithdrawal, WFHSchedule.wfh_id == WFHWithdrawal.wfh_id, isouter=True).filter(
            Employee.reporting_manager == id, 
            WFHApplication.manager_reject_reason.is_(None), 
            WFHSchedule.manager_withdraw_reason.is_(None),
            or_(WFHSchedule.status == 'Pending_Approval', WFHSchedule.status == 'Pending_Withdrawal')
            ).all()


        # Initialise return list
        schedule_list = []
        application_grp = {}

        # add all staff to the same team
        team = []
        # team.append(manager)
        for staff in Employee.query.filter_by(reporting_manager=id).all(): 
            if (id != staff.staff_id): # this line would make sure CEO is not inside 
                team.append(staff)

        # Create a list of schedules with time_slot and wfh_date
        for arr in wfh_arrs:

            # Extract the year, month, and day
            date = arr.wfh_date
            year = date.year
            month = date.month
            day = date.day

            if arr.application.time_slot == "AM":
                start_time = 9
                end_time = 13
            elif arr.application.time_slot == "PM":
                start_time = 14
                end_time = 18
            else: #full day
                start_time = 9
                end_time = 18

            # to calculate the wfh %
            wfh_am_length = 0
            wfh_pm_length = 0
            wfh_full_length = 0
            if arr.application.time_slot == 'AM':
                wfh_date_calculation_am = db.session.query(WFHSchedule).join(WFHApplication, WFHSchedule.application_id == WFHApplication.application_id).join(Employee, Employee.staff_id == WFHApplication.staff_id).filter(
                    Employee.reporting_manager == id, 
                    WFHSchedule.wfh_date == arr.wfh_date,
                    WFHApplication.time_slot == 'AM',
                    or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Withdrawal')
                    ).all()

                wfh_am_length = len(wfh_date_calculation_am)

            elif arr.application.time_slot == 'PM':
                wfh_date_calculation_pm = db.session.query(WFHSchedule).join(WFHApplication, WFHSchedule.application_id == WFHApplication.application_id).join(Employee, Employee.staff_id == WFHApplication.staff_id).filter(
                    Employee.reporting_manager == id, 
                    WFHSchedule.wfh_date == arr.wfh_date,
                    WFHApplication.time_slot == 'PM',
                    or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Withdrawal')
                    ).all()
                wfh_pm_length = len(wfh_date_calculation_pm)
            else:
                wfh_date_calculation_am = db.session.query(WFHSchedule).join(WFHApplication, WFHSchedule.application_id == WFHApplication.application_id).join(Employee, Employee.staff_id == WFHApplication.staff_id).filter(
                    Employee.reporting_manager == id, 
                    WFHSchedule.wfh_date == arr.wfh_date,
                    WFHApplication.time_slot == 'AM',
                    or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Withdrawal')
                    ).all()
                wfh_am_length = len(wfh_date_calculation_am)
                wfh_date_calculation_pm = db.session.query(WFHSchedule).join(WFHApplication, WFHSchedule.application_id == WFHApplication.application_id).join(Employee, Employee.staff_id == WFHApplication.staff_id).filter(
                    Employee.reporting_manager == id, 
                    WFHSchedule.wfh_date == arr.wfh_date,
                    WFHApplication.time_slot == 'PM',
                    or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Withdrawal')
                    ).all()
                wfh_pm_length = len(wfh_date_calculation_pm)
            
            wfh_date_calculation_full = db.session.query(WFHSchedule).join(WFHApplication, WFHSchedule.application_id == WFHApplication.application_id).join(Employee, Employee.staff_id == WFHApplication.staff_id).filter(
                Employee.reporting_manager == id, 
                WFHSchedule.wfh_date == arr.wfh_date,
                WFHApplication.time_slot == 'FULL',
                or_(WFHSchedule.status == 'Approved', WFHSchedule.status == 'Pending_Withdrawal')
                ).all()
            wfh_full_length = len(wfh_date_calculation_full)
            
            percentage = 0

            if arr.application.time_slot == 'FULL':
                am_percentage = 0
                pm_percentage = 0
                # Avoid division by zero
            
                am_percentage = math.floor(((wfh_am_length + wfh_full_length) / len(team)) * 100) if len(team) > 0 else 0
                pm_percentage = math.floor(((wfh_pm_length+wfh_full_length) / len(team)) * 100)if len(team) > 0 else 0
                percentage = [am_percentage, pm_percentage]

            else:
                percentage = math.floor(((wfh_am_length+wfh_full_length+wfh_pm_length) / len(team)) * 100)if len(team) > 0 else 0

            if arr.status == "Pending_Approval":
                app_id = arr.application_id
                if app_id in application_grp:
                    application_grp[app_id].append({
                        'wfh_id': arr.wfh_id,
                        'staff_id': arr.application.staff_id,
                        'label': arr.application.time_slot,
                        'dateStart': datetime(year, month, day, start_time, 0).isoformat(), 
                        'dateEnd': datetime(year, month, day, end_time, 0).isoformat(),
                        'class': arr.status,
                        'description': arr.application.staff_apply_reason,
                        'staff_name': arr.application.employee.staff_fname + " " + arr.application.employee.staff_lname,
                        'staff_dept': arr.application.employee.position,
                        'percentage': percentage
                    })
                else:
                    application_grp[app_id] = [{
                        'wfh_id': arr.wfh_id,
                        'staff_id': arr.application.staff_id,
                        'label': arr.application.time_slot,
                        'dateStart': datetime(year, month, day, start_time, 0).isoformat(), 
                        'dateEnd': datetime(year, month, day, end_time, 0).isoformat(),
                        'class': arr.status,
                        'description': arr.application.staff_apply_reason,
                        'staff_name': arr.application.employee.staff_fname + " " + arr.application.employee.staff_lname,
                        'staff_dept': arr.application.employee.position,
                        'percentage': percentage
                    }]
                
            else:
                # need change the test 
                app_id = str(arr.application_id)  + "-" +  str(arr.wfh_id)
                withdrawals = db.session.query(WFHWithdrawal).filter(WFHWithdrawal.wfh_id == arr.wfh_id).all()
                withdrawal = withdrawals[len(withdrawals)-1]
                application_grp[app_id] = [{
                    'wfh_id': arr.wfh_id,
                    'staff_id': arr.application.staff_id,
                    'label': arr.application.time_slot,
                    'dateStart': datetime(year, month, day, start_time, 0).isoformat(),
                    'dateEnd': datetime(year, month, day, end_time, 0).isoformat(),
                    'class': arr.status,
                    'description': withdrawal.staff_withdraw_reason,
                    'staff_name': arr.application.employee.staff_fname + " " + arr.application.employee.staff_lname,
                    'staff_dept': arr.application.employee.position,
                    'percentage': percentage
                }]

        # Looping through both keys and values
        for key, value in application_grp.items():
            schedule_list.append({'application_id': key,'listofschedule': value})

        return jsonify(schedule_list), 200
    
    except OperationalError as e:
        return jsonify({'error': 'Database connection issue.'}), 500

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    # Catch unexpected errors (everything else)
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred.'}), 500


@application_blueprint.route('/approverejectapplication/<int:id>', methods=['POST'])
def manager_approve_staff_wfh(id):

    # to receive either one of the following JSON data
    #  1. Without wfh_id
    # {
    #     "application_id": 1234,
    #     "status": "Approve/Reject",
    #     "staff_id": "140078"
    #     "manager_reject_reason": "" (needed if status is reject)
    # }
    #  2. With wfh_id
    # {
    #     "application_id": 1234,
    #     "wfh_id": 1234,
    #     "status": "Approve/Reject",
    #     "staff_id": "140078"
    #     "manager_reject_reason": "" (needed if status is reject)
    # }

    try:
        json_data = request.get_json()
        if not json_data: # checks for first possible error
            return jsonify({"error": "JSON data passed from client side is insufficient"}), 400
        
        
        employee_check = db.session.query(Employee).filter(Employee.staff_id == json_data['staff_id']).first()
        if (employee_check.reporting_manager == id) :
            if ('wfh_id' in json_data) :
                schedule_entries = db.session.query(WFHSchedule).join(WFHApplication).filter(
                WFHApplication.staff_id == employee_check.staff_id,
                WFHSchedule.application_id == json_data['application_id'],
                WFHApplication.application_id == json_data['application_id'],
                WFHSchedule.wfh_id == json_data['wfh_id'],
                WFHSchedule.status == 'Pending_Withdrawal'
            ).all()
            else:
                schedule_entries = db.session.query(WFHSchedule).join(WFHApplication).filter(
                    WFHApplication.staff_id == employee_check.staff_id,
                    WFHSchedule.application_id == json_data['application_id'],
                    WFHApplication.application_id == json_data['application_id'],
                    WFHSchedule.status == 'Pending_Approval'
                ).all()

            print("schedule_entries", schedule_entries)
            if schedule_entries:
                approval_status = None
                for schedule_entry in schedule_entries:
                    # withdrawal 
                    if schedule_entry.status == "Pending_Withdrawal":
                        if json_data["status"] == "Approve":
                            # to withdrawal
                            schedule_entry.status = "Withdrawn"
                            approval_status = 'Withdrawal Approved'
                        elif json_data["status"] == "Reject" and json_data['manager_reject_reason'] != None:
                            # to not withdrawal
                
                            schedule_entry.status = "Approved"
                            # schedule_entry.wfh_withdrawal.manager_reject_withdrawal_reason = json_data['manager_reject_reason']
                            
                            rejected_schedule = WFHSchedule.query.filter_by(application_id=json_data['application_id']).first()

                            wfh_withdrawal = db.session.query(WFHWithdrawal).filter(
                                WFHWithdrawal.wfh_id == rejected_schedule.wfh_id
                            ).first()
                
                            wfh_withdrawal.manager_reject_withdrawal_reason = json_data['manager_reject_reason'] if wfh_withdrawal else None

                            approval_status = 'Withdrawal Rejected'
                        else:
                            approval_status = 'Approval or Rejection of withdrawal request not processed'
                    else:
                        if json_data['status'] == "Approve":
                            schedule_entry.status = "Approved"
                            approval_status = 'Application Approved'
                        elif json_data['status'] == "Reject" and json_data['manager_reject_reason'] != None:
                        
                            schedule_entry.status = "Rejected"
                            schedule_entry.application.manager_reject_reason = json_data['manager_reject_reason']

                            # Remove this cause by right it should have exist already at this point 
                            # wfh_application = db.session.query(WFHApplication).filter(
                            #     WFHApplication.application_id == json_data['application_id']
                            # ).first()

                            # if wfh_application:
                            #     wfh_application.manager_reject_reason = json_data['manager_reject_reason']

                            approval_status = 'Application Rejected'
                        else:
                            approval_status = 'Approval or Rejection of application request not processed'
                
                # Commit all the changes after the loop
                db.session.commit()

                # Return the final status after looping through all entries
                # Remove the If statement as because if its else we have no way of return and it doesnt make much sense for it to fail cause if it fail its the db problem which will trigger the catch
                return jsonify({'success': approval_status}), 201
            else: 
                return jsonify({'failed': 'No pending requests found'}), 201
            
        else:
            return jsonify({'failed': 'wrong reporting manager'}), 201
    except OperationalError as e:
        return jsonify({'error': 'Database connection issue.'}), 500

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    # Catch unexpected errors (everything else)
    except Exception as e:
        print(e)
        return jsonify({'error': 'An unexpected error occurred.'}), 500


@application_blueprint.route('/manager_withdraw/<int:id>', methods=['POST'])
def manager_withdrawal_wfh(id):
    '''
    Function:
    1. Receive a JSON body:
    {
        "time_slot": "AM",
        "manager_withdraw_reason": "Urgent Product Release Meeting",
        "date": "2024-10-18T00:00:00.000000Z"
    }
    2. Extract specific Approved wfh date for staff
    3. Checks for 3 months forward, 1 month backward
    4. If no issue, updates status to "Withdrawn" and includes Manager withdraw reason

    Error considered (server side):
    1. JSON data not sent (400)
    2. current date is either more than 3 months after/1 month before WFH date
    3. Database connection issue (500)
    4. Databse Query fail (500)

    note:
    1. (id in the url parameter is staff, not manager)
    2. Assume incoming JSON status is "Approved"

    '''
    try:
        # get the JSON data from the request
        json_data = request.get_json()
        if not json_data: # checks for first possible error
            return jsonify({"error": "JSON data passed from client side is insufficient"}), 400

        # convert to yy-mm-dd format and change type to date
        json_data['date'] = datetime.strptime(json_data['date'] , '%Y-%m-%dT%H:%M:%S.%fZ')
        json_data['date'] = json_data['date'].strftime('%Y-%m-%d')
        
        wfh_arrs = db.session.query(WFHSchedule).join(WFHApplication).filter(
            WFHApplication.staff_id == id,
            or_(WFHApplication.time_slot == json_data['time_slot'], WFHApplication.time_slot == "FULL"),
            WFHSchedule.wfh_date == json_data['date'],
            WFHSchedule.status == "Approved"
            ).first()
            
        
        if wfh_arrs == None:
            return jsonify({'failed': 'No approved arrangement found!'}), 201

        # Extract the year, month, and day
        date = wfh_arrs.wfh_date
        year = date.year
        month = date.month
        day = date.day

        # Example current date (you can replace this with datetime.now() to get today's date)
        current_date = datetime.now()

        # Example Approved arrangement date (replace this with your actual date)
        Approved_arrangement_date = datetime(year, month, day)  # example date in YYYY, MM, DD format

        # Define the time range of 2 weeks
        three_months_Forward = Approved_arrangement_date + relativedelta(months=3)
        one_month_Backward = Approved_arrangement_date - relativedelta(months=1)

        # Check if the Approved arrangement date is more than 2 weeks backward or 2 weeks forward
        if current_date > three_months_Forward or current_date < one_month_Backward:
            print("Approved arrangement is more than 3 months forward or 1 month backward.")
            # Here, you can handle the case when data should not be stored
            return jsonify({'failed': 'Approved arrangement is more than 3 months forward or 1 month backward!'}),201

        wfh_arrs.status = "Withdrawn"
        wfh_arrs.manager_withdraw_reason = json_data['manager_withdraw_reason']
        db.session.commit()
        return jsonify({'success': 'Successful Withdrawal!'}), 201
        
        
        
    except OperationalError as e:
        return jsonify({'error': 'Database connection issue.'}), 500

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    # Catch unexpected errors (everything else)
    except Exception as e:
        print(e)
        return jsonify({'error': 'An unexpected error occurred.'}), 500

@application_blueprint.route('/autoReject', methods=['GET'])
def auto_reject():
    '''
    Function: Checks status "Pending_Approval" every 24 hours if it is more than 2 months old from wfh arrangement date and changes status to "Rejected"
    '''
    try:
        # Ensure the function runs within Flask's application context
            print("function started for scheduler")
            # Fetch all "Pending_Approval" WFH records
            wfh_records = db.session.query(WFHSchedule).filter(
                or_(WFHSchedule.status == "Pending_Approval", WFHSchedule.status == "Pending_Withdrawal")
            ).all()
            print("wfh records returned")

            # Define the time range of 2 months
            two_months = timedelta(weeks=8)

            # Loop through each record
            for record in wfh_records:
                # Extract the year, month, and day
                date = record.wfh_date
                year = date.year
                month = date.month
                day = date.day

                # Example current date (you can replace this with datetime.now() to get today's date)
                current_date = datetime.now()

                # Example Approved arrangement date (replace this with your actual date)
                Approved_arrangement_date = datetime(year, month, day)  # example date in YYYY, MM, DD format

                # Check if the Approved arrangement date is more than 2 months backward or 2 months forward
                if current_date > (Approved_arrangement_date + two_months):
                    print("Approved arrangement is more than 2 months forward. Changing status to Rejected.")
                    if record.status == "Pending_Approval":
                        print(record.application_id , "Pending_Approval")
                        
                        wfh_sch_app = db.session.query(WFHSchedule).filter(
                            WFHSchedule.application_id == record.application_id
                        ).all()

                        for wfh_sch in wfh_sch_app:
                            wfh_sch.status = "Rejected"
                            print(wfh_sch.wfh_id)

                        wfh_app_rec = db.session.query(WFHApplication).filter(
                            (WFHApplication.application_id == record.application_id)
                        ).first()

                        wfh_app_rec.manager_reject_reason = "rejected by system"
                    # elif record.status == "Pending_Withdrawal": # Pending_Withdrawal
                    else:
                        print(record.wfh_id, record.status)
                        record.status = "Approved"
                        wfh_app_rec = db.session.query(WFHWithdrawal).filter(
                            WFHWithdrawal.wfh_id == record.wfh_id
                        ).first()
                        
                        wfh_app_rec.manager_reject_withdrawal_reason = "rejected by system" if wfh_app_rec and wfh_app_rec.manager_reject_withdrawal_reason is None else None
                
                    db.session.commit()  # Commit all updates
            return jsonify({'success': 'Auto Reject went through!'}), 201
            
    except OperationalError as e:
        return jsonify({'error': 'Database connection issue.'}), 500

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database query failed.'}), 500

    # Catch unexpected errors (everything else)
    except Exception as e:
        print(e)
        return jsonify({'error': 'An unexpected error occurred.'}), 500




