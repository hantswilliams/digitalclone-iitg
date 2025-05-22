"""
Authentication forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from app.utils.forms import validate_password_strength, validate_username


class BasicLoginForm(FlaskForm):
    """Form for basic username/password login"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    remember = BooleanField('Remember Me')


class RegisterForm(FlaskForm):
    """Form for user registration with username/password"""
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=64),
        validate_username
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        validate_password_strength
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    name = StringField('Full Name', validators=[DataRequired()])
