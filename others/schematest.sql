-- Create Database
DROP DATABASE IF EXISTS `wfh`;
CREATE DATABASE IF NOT EXISTS `wfh` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `wfh`;

-- Table for EMPLOYEE
CREATE TABLE employee (
    staff_id INT PRIMARY KEY,
    staff_fname VARCHAR(255),
    staff_lname VARCHAR(255),
    dept VARCHAR(255),
    position VARCHAR(255),
    country VARCHAR(255),
    email VARCHAR(255),
    reporting_manager INT,
    role INT,
    FOREIGN KEY (reporting_manager) REFERENCES employee(staff_id) ON DELETE CASCADE -- Self-referencing foreign key
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Table for LOGIN
CREATE TABLE login (
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    staff_id INT,
    PRIMARY KEY (username),
    FOREIGN KEY (staff_id) REFERENCES employee(staff_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Table for WFH_APPLICATION
CREATE TABLE wfh_application (
    application_id INT AUTO_INCREMENT PRIMARY KEY, 
    staff_id INT,
    time_slot VARCHAR(255), -- AM, PM, FULL
    staff_apply_reason VARCHAR(255),
    manager_reject_reason VARCHAR(255),
    FOREIGN KEY (staff_id) REFERENCES employee(staff_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Table for WFH_SCHEDULE
CREATE TABLE wfh_schedule (
    wfh_id INT AUTO_INCREMENT PRIMARY KEY, 
    application_id INT,
    wfh_date DATE,
    status VARCHAR(255), -- Approved, Rejected, Pending, Withdrawn
    staff_withdraw_reason VARCHAR(255),
    manager_withdraw_reason VARCHAR(255),
    FOREIGN KEY (application_id) REFERENCES wfh_application(application_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
