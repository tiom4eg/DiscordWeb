from flask_wtf import *
from wtforms import SubmitField, StringField


class Add_review(FlaskForm):
    content = StringField('Enter your review here')
    submit = SubmitField('I finished')