use wfh;
-- Test login access
-- 130002 (ceo, role 1),  140001 (sales hr, role 1), 140736 (sales staff, role 2), 140008 (sales manager, role 3)
insert into login (username, password, staff_id)
values('ceo', 'ceo', 130002), ('saleshr', 'saleshr',140001), ('salesstaff','salesstaff', 140736 ), ('salesmanager', 'salesmanager', 140008);

-- Test view own schedule
-- Insert records into wfh_application table
INSERT INTO wfh_application (application_id, staff_id, time_slot, staff_apply_reason, manager_reject_reason)
VALUES (1, 140894, 'AM', 'Medical appointment in the morning', NULL);

INSERT INTO wfh_application (application_id, staff_id, time_slot, staff_apply_reason, manager_reject_reason)
VALUES (2, 140894, 'FULL', 'Need to take care of a family member', NULL);

INSERT INTO wfh_application (application_id, staff_id, time_slot, staff_apply_reason, manager_reject_reason)
VALUES (3, 140078, 'PM', 'Personal matters in the afternoon', 'Insufficient justification');

INSERT INTO wfh_application (application_id, staff_id, time_slot, staff_apply_reason, manager_reject_reason)
VALUES (4, 140078, 'FULL', 'Internet issues at the office', NULL);

INSERT INTO wfh_application (application_id, staff_id, time_slot, staff_apply_reason, manager_reject_reason)
VALUES (5, 140891, 'AM', 'Medical checkup', NULL);

-- Insert records into wfh_schedule table
INSERT INTO wfh_schedule (wfh_id, application_id, wfh_date, status, manager_withdraw_reason)
VALUES (1, 1, '2024-10-01', 'Approved', NULL);

INSERT INTO wfh_schedule (wfh_id, application_id, wfh_date, status, manager_withdraw_reason)
VALUES (2, 2, '2024-10-02', 'Pending_Approval', NULL);

INSERT INTO wfh_schedule (wfh_id, application_id, wfh_date, status, manager_withdraw_reason)
VALUES (3, 3, '2024-10-03', 'Rejected', NULL);

INSERT INTO wfh_schedule (wfh_id, application_id, wfh_date, status, manager_withdraw_reason)
VALUES (4, 4, '2024-10-04', 'Approved', NULL);

INSERT INTO wfh_schedule (wfh_id, application_id, wfh_date, status, manager_withdraw_reason)
VALUES (5, 5, '2024-10-05', 'Withdrawn', NULL);

-- Insert additional records into wfh_application table
INSERT INTO wfh_application (application_id, staff_id, time_slot, staff_apply_reason, manager_reject_reason)
VALUES (6, 140894, 'FULL', 'Family emergency', NULL),
       (7, 140078, 'AM', 'Doctor appointment', NULL),
       (8, 140078, 'FULL', 'Need to take care of personal matters', NULL),
       (9, 140891, 'PM', 'Meeting with contractor', NULL),
       (10, 140891, 'AM', 'Taking care of child', NULL),
       (11, 140894, 'FULL', 'Internet disruption at home', NULL),
       (12, 140078, 'FULL', 'Mental health break', NULL),
       (13, 140894, 'PM', 'Urgent family issue', NULL),
       (14, 140891, 'AM', 'Personal errand in the morning', NULL),
       (15, 140078, 'FULL', 'Technical issues at office', NULL),
       (16, 140891, 'AM', 'Medical follow-up', NULL),
       (17, 140894, 'FULL', 'School event for children', NULL),
       (18, 140078, 'PM', 'Need to attend workshop', NULL),
       (19, 140894, 'AM', 'Car servicing', NULL),
       (20, 140891, 'FULL', 'Unexpected household repair', NULL),
       (21, 140078, 'PM', 'Urgent work on a personal project', NULL),
       (22, 140894, 'FULL', 'Family event', NULL),
       (23, 140891, 'AM', 'Personal time for reflection', NULL),
       (24, 140078, 'FULL', 'Attending a conference', NULL),
       (25, 140894, 'PM', 'Need to travel out of town', NULL),
       (26, 140736, 'FULL', 'Family emergency', NULL),
       (27, 140736, 'AM', 'Medical appointment', NULL),
       (28, 140736, 'PM', 'Personal commitment in the afternoon', NULL),
       (29, 140736, 'FULL', 'Need to handle family matters', NULL),
       (30, 140736, 'AM', 'Medical checkup', NULL),
       (31, 140736, 'PM', 'Client meeting', NULL),
       (32, 140736, 'FULL', 'House renovation issues', NULL),
       (33, 140736, 'AM', 'School event for kids', NULL),
       (34, 140736, 'PM', 'Appointment with lawyer', NULL),
       (35, 140736, 'FULL', 'Technical issues with work system', NULL),
       (36, 140736, 'AM', 'Need to attend webinar', NULL),
       (37, 140736, 'FULL', 'Car repair issues', NULL),
       (38, 140736, 'PM', 'Urgent household issue', NULL),
       (39, 140736, 'AM', 'Attending a workshop', NULL),
       (40, 140736, 'FULL', 'Internet issues at home', NULL),
       (41, 140736, 'PM', 'Mentoring session in the afternoon', NULL),
       (42, 140736, 'FULL', 'Personal time for reflection', NULL),
       (43, 140736, 'AM', 'Doctor consultation', NULL),
       (44, 140736, 'FULL', 'Taking care of child', NULL),
       (45, 140736, 'PM', 'Meeting with contractor', NULL);

-- Insert corresponding records into wfh_schedule table ensuring no duplicate dates for same staff
INSERT INTO wfh_schedule (wfh_id, application_id, wfh_date, status, manager_withdraw_reason)
VALUES
(6, 6, '2024-10-11', 'Approved', NULL),
(7, 7, '2024-10-12', 'Pending_Approval', NULL),
(8, 8, '2024-10-13', 'Approved', NULL),
(9, 9, '2024-10-14', 'Pending_Approval', NULL),
(10, 10, '2024-10-15', 'Approved', NULL),
(11, 11, '2024-10-16', 'Pending_Approval', NULL),
(12, 12, '2024-10-17', 'Approved', NULL),
(13, 13, '2024-10-18', 'Approved', NULL),
(14, 14, '2024-10-19', 'Pending_Approval', NULL),
(15, 15, '2024-10-20', 'Approved', NULL),
(16, 16, '2024-10-21', 'Pending_Approval', NULL),
(17, 17, '2024-10-22', 'Approved', NULL),
(18, 18, '2024-10-23', 'Pending_Approval', NULL),
(19, 19, '2024-10-24', 'Approved', NULL),
(20, 20, '2024-10-25', 'Pending_Approval', NULL),
(21, 21, '2024-10-26', 'Approved', NULL),
(22, 22, '2024-10-27', 'Pending_Approval', NULL),
(23, 23, '2024-10-28', 'Approved', NULL),
(24, 24, '2024-10-29', 'Pending_Approval', NULL),
(25, 25, '2024-10-30', 'Approved', NULL),
(26, 26, '2024-10-31', 'Pending_Approval', NULL),
(27, 27, '2024-11-01', 'Approved', NULL),
(28, 28, '2024-11-02', 'Pending_Approval', NULL),
(29, 29, '2024-11-03', 'Approved', NULL),
(30, 30, '2024-11-04', 'Pending_Approval', NULL),
(31, 31, '2024-11-05', 'Approved', NULL),
(32, 32, '2024-11-06', 'Pending_Approval', NULL),
(33, 33, '2024-11-07', 'Approved', NULL),
(34, 34, '2024-11-08', 'Pending_Approval', NULL),
(35, 35, '2024-11-09', 'Approved', NULL),
(36, 36, '2024-11-10', 'Pending_Approval', NULL),
(37, 37, '2024-11-11', 'Approved', NULL),
(38, 38, '2024-11-12', 'Pending_Approval', NULL),
(39, 39, '2024-11-13', 'Approved', NULL),
(40, 40, '2024-11-14', 'Pending_Approval', NULL),
(41, 41, '2024-11-15', 'Approved', NULL),
(42, 42, '2024-11-16', 'Pending_Approval', NULL),
(43, 43, '2024-11-17', 'Approved', NULL),
(44, 44, '2024-11-18', 'Pending_Approval', NULL),
(45, 45, '2024-11-19', 'Approved', NULL);

