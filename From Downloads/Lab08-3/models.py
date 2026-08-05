from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# -----------------------
# USER
# -----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    enrollments = db.relationship(
        'Enrollment',
        back_populates='student',
        cascade='all, delete-orphan'
    )
    courses = db.relationship(
        'Course',
        back_populates='teacher',
        foreign_keys='Course.teacher_id'
    )

    def set_password(self, pw):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(pw, method='pbkdf2:sha256')

    def check_password(self, pw):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, pw)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# -----------------------
# COURSE
# -----------------------
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    capacity = db.Column(db.Integer, default=30)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    time = db.Column(db.String(50))

    teacher = db.relationship('User', back_populates='courses')
    enrollments = db.relationship(
        'Enrollment',
        back_populates='course',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Course {self.name}>"


# -----------------------
# ENROLLMENT
# -----------------------
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    grade = db.Column(db.String(10))

    student = db.relationship('User', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')

    def __repr__(self):
        return f"<Enrollment s:{self.student_id} c:{self.course_id}>"
