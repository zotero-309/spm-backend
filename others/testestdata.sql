-- Insert records into employee table
INSERT INTO employee (staff_id, staff_fname, staff_lname, dept, position, country, email, reporting_manager, role)
VALUES 
(140894, 'John', 'Doe', 'Engineering', 'Developer', 'USA', 'john.doe@example.com', NULL, 1),
(140078, 'Jane', 'Smith', 'HR', 'Manager', 'USA', 'jane.smith@example.com', NULL, 1),
(140891, 'Alice', 'Johnson', 'Finance', 'Analyst', 'USA', 'alice.johnson@example.com', NULL, 1);

-- Insert records into wfh_application table
INSERT INTO wfh_application (application_id, staff_id, time_slot, staff_apply_reason, manager_reject_reason)
VALUES 
(1, 140894, 'AM', 'Medical appointment in the morning', NULL),
(2, 140894, 'FULL', 'Need to take care of a family member', NULL),
(3, 140078, 'PM', 'Personal matters in the afternoon', 'Insufficient justification'),
(4, 140078, 'FULL', 'Internet issues at the office', NULL),
(5, 140891, 'AM', 'Medical checkup', NULL);


-- Insert records into wfh_schedule table
INSERT INTO wfh_schedule (wfh_id, application_id, wfh_date, status, staff_withdraw_reason, manager_withdraw_reason)
VALUES 
(1, 1, '2024-10-01', 'Approved', NULL, NULL),
(2, 2, '2024-10-02', 'Pending_Approval', NULL, NULL),
(3, 3, '2024-10-03', 'Rejected', NULL, NULL),
(4, 4, '2024-10-04', 'Pending_Withdrawal', NULL, NULL),
(5, 5, '2024-10-05', 'Withdrawn', 'Unable to work in the morning', NULL);


