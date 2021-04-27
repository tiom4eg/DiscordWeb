from flask_wtf import *
from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import EmailField


class Register(FlaskForm):
    email = EmailField('Your email.', validators=[DataRequired()])
    nickname = StringField('What nickname would you like to have?')
    password = PasswordField('Your password. Fast.', validators=[DataRequired()])
    repeat_password = PasswordField('Password. Again.', validators=[DataRequired()])
    submit = SubmitField('I wanna register')