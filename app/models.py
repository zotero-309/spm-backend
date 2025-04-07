# SQL alchemy to define classes (entities inside db)
# Relationships defined on top of foreign key in objects allow for easy reference in query
# backref just help to show bilateral relationship (whats on the other side of the relationship)

from app import db

class Employee(db.Model):
    __tablename__ = 'employee'

    staff_id = db.Column(db.Integer, primary_key=True)
    staff_fname = db.Column(db.String(255), nullable=False)
    staff_lname = db.Column(db.String(255), nullable=False)
    dept = db.Column(db.String(255))
    position = db.Column(db.String(255))
    country = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    reporting_manager = db.Column(db.Integer, db.ForeignKey('employee.staff_id'))
    role = db.Column(db.Integer)

    # Relationship for self-referencing manager (defines relationship to make it easier to navigate when querying)
    # remote_side required for self referencing, need to know parent (staff_id), backref sets bidirectional relationship
    manager = db.relationship('Employee', remote_side=[staff_id], backref='subordinates')

    # Relationship to other tables
    applications = db.relationship('WFHApplication', backref='employee', cascade="all, delete-orphan")
    login = db.relationship('Login', backref='employee', uselist=False, cascade="all, delete-orphan")

class Login(db.Model):
    __tablename__ = 'login'

    username = db.Column(db.String(255), primary_key=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('employee.staff_id'), nullable=False)

    # # Relationship to employee
    # # uselist being false helps to set 1-1 relationship
    # employee = db.relationship('Employee', backref=db.backref('login', uselist=False))

class WFHApplication(db.Model):
    __tablename__ = 'wfh_application'

    application_id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('employee.staff_id'), nullable=False)
    time_slot = db.Column(db.String(255))  # AM, PM, FULL
    staff_apply_reason = db.Column(db.String(255))
    manager_reject_reason = db.Column(db.String(255))

    # # Relationship to employee
    # employee = db.relationship('Employee', backref='wfh_application')

    # Relationship to WFH schedule
    schedules = db.relationship('WFHSchedule', backref='application', cascade="all, delete-orphan")

class WFHSchedule(db.Model):
    __tablename__ = 'wfh_schedule'

    wfh_id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('wfh_application.application_id'), nullable=False)
    wfh_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(255))  # Approved, Rejected, Pending Approval, Withdrawn, Pending Withdrawal
    manager_withdraw_reason = db.Column(db.String(255))

    withdrawals = db.relationship('WFHWithdrawal', backref='schedule', cascade='all, delete-orphan')

class WFHWithdrawal(db.Model):
    __tablename__ = 'wfh_withdrawal'

    withdrawal_id = db.Column(db.Integer, primary_key=True)
    wfh_id = db.Column(db.Integer, db.ForeignKey('wfh_schedule.wfh_id'), nullable=False)
    staff_withdraw_reason = db.Column(db.String(255))
    manager_reject_withdrawal_reason = db.Column(db.String(255))


