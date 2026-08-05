from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from wtforms import PasswordField
from wtforms_sqlalchemy.fields import QuerySelectField
from forms import LoginForm, GradeForm
import os

# -----------------------
# APP SETUP
# -----------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret'

# -----------------------
# DATABASE SETUP
# -----------------------
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

db_path = os.path.join(instance_path, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

# -----------------------
# MODELS
# -----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    enrollments = db.relationship('Enrollment', back_populates='student', cascade='all, delete-orphan')
    courses = db.relationship('Course', back_populates='teacher', foreign_keys='Course.teacher_id')

    def set_password(self, pw):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(pw, method='pbkdf2:sha256')

    def check_password(self, pw):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, pw)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    capacity = db.Column(db.Integer, default=30)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    teacher = db.relationship('User', back_populates='courses', foreign_keys=[teacher_id])
    enrollments = db.relationship('Enrollment', back_populates='course', cascade='all, delete-orphan')
    time = db.Column(db.String(50))  # Added time field for class schedule

    def __repr__(self):
        return f"<Course {self.name}>"

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    grade = db.Column(db.String(10))
    student = db.relationship('User', back_populates='enrollments', foreign_keys=[student_id])
    course = db.relationship('Course', back_populates='enrollments', foreign_keys=[course_id])

    def __repr__(self):
        return f"<Enrollment s:{self.student_id} c:{self.course_id}>"

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# -----------------------
# ROUTES
# -----------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "student":
            return redirect(url_for("student_dashboard"))
        if current_user.role == "teacher":
            return redirect(url_for("teacher_dashboard"))
        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(username=form.username.data).first()
        if u and u.check_password(form.password.data):
            login_user(u)
            return redirect(url_for("index"))
        flash("Invalid username or password","danger")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# -----------------------
# STUDENT DASHBOARD
# -----------------------
@app.route("/student")
@login_required
def student_dashboard():
    if current_user.role != "student":
        return redirect(url_for("index"))
    courses = Course.query.all()
    enrolled_courses = [e.course for e in current_user.enrollments]
    course_counts = {c.id: len(c.enrollments) for c in courses}
    return render_template("student_dashboard.html",
                           courses=courses,
                           enrolled=enrolled_courses,
                           course_counts=course_counts)

@app.route("/student/signup/<int:course_id>", methods=["POST"])
@login_required
def signup_course(course_id):
    if current_user.role != "student":
        return redirect(url_for("index"))
    course = Course.query.get_or_404(course_id)
    if len(course.enrollments) >= course.capacity:
        flash("Course is full.","warning")
    elif Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first():
        flash("You are already enrolled.", "info")
    else:
        db.session.add(Enrollment(student_id=current_user.id, course_id=course.id))
        db.session.commit()
        flash("Successfully enrolled!", "success")
    return redirect(url_for("student_dashboard"))

# -----------------------
# TEACHER DASHBOARD
# -----------------------
@app.route("/teacher")
@login_required
def teacher_dashboard():
    if current_user.role != "teacher":
        return redirect(url_for("index"))
    courses = current_user.courses
    return render_template("teacher_dashboard.html", courses=courses)

@app.route('/teacher/course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def teacher_course(course_id):
    if current_user.role != "teacher":
        return redirect(url_for("login"))
    course = Course.query.get_or_404(course_id)
    form = GradeForm()
    if form.validate_on_submit():
        student_id = request.form.get("student_id")
        e = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
        if e:
            e.grade = form.grade.data
            db.session.commit()
            flash("Grade updated successfully!", "success")
        return redirect(url_for("teacher_course", course_id=course_id))
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    return render_template("teacher_course.html", course=course, enrollments=enrollments, form=form)

# -----------------------
# ADMIN DASHBOARD
# -----------------------
@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("index"))
    return render_template("admin.html")

# -----------------------
# FLASK-ADMIN SETUP
# -----------------------
admin = Admin(app, name="Lab08 Admin", template_mode="bootstrap3")

class UserAdmin(ModelView):
    column_exclude_list = ['password_hash']
    column_searchable_list = ['username', 'role']
    column_filters = ['role']
    form_extra_fields = {'password': PasswordField('Password')}
    form_create_rules = ['username', 'role', 'password']
    form_edit_rules = ['username', 'role', rules.HTML('<em>Leave password blank to keep current</em>'), 'password']

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)

class CourseAdmin(ModelView):
    column_list = ['name', 'teacher', 'capacity', 'time']
    column_searchable_list = ['name']
    column_filters = ['teacher']
    form_extra_fields = {
        'teacher': QuerySelectField(
            'Teacher',
            query_factory=lambda: User.query.filter_by(role='teacher').all(),
            get_label='username',
            allow_blank=True
        )
    }
    form_create_rules = ['name', 'teacher', 'capacity', 'time']
    form_edit_rules = ['name', 'teacher', 'capacity', 'time']

class EnrollmentAdmin(ModelView):
    column_list = ['student', 'course', 'grade']
    column_searchable_list = ['student.username', 'course.name']
    column_filters = ['student', 'course']

admin.add_view(UserAdmin(User, db.session))
admin.add_view(CourseAdmin(Course, db.session))
admin.add_view(EnrollmentAdmin(Enrollment, db.session))

# -----------------------
# DATABASE INIT
# -----------------------
if not os.path.exists(db_path):
    db.create_all()

# -----------------------
# RUN APP
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)
