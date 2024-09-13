from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User
from wtforms import StringField, TextAreaField, DateField, SubmitField

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    class_code = StringField('Class Code', validators=[Length(max=10)])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class AssignmentSubmissionForm(FlaskForm):
    html_file = FileField('HTML File', validators=[FileAllowed(['html']), DataRequired()])
    css_file = FileField('CSS File', validators=[FileAllowed(['css']), DataRequired()])
    js_file = FileField('JavaScript File', validators=[FileAllowed(['js']), DataRequired()])
    submit = SubmitField('Submit Assignment')

class ClassCreationForm(FlaskForm):
    class_code = StringField('Class Code', validators=[DataRequired(), Length(min=4, max=10)])
    submit = SubmitField('Create Class')

class AssignmentForm(FlaskForm):
    name = StringField('Assignment Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Create Assignment')