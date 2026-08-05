from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class GradeForm(FlaskForm):
    enrollment_id = HiddenField("Enrollment ID")
    grade = IntegerField("Grade", validators=[DataRequired(), NumberRange(0,100)])
    submit = SubmitField("Update Grade")
