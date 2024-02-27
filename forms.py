from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


class CommentForm(FlaskForm):
    """Form for commenting"""

    comment = TextAreaField('Type comment here', validators=[DataRequired()])

class RatingForm(FlaskForm):
    """Form for rating"""

    score = IntegerField('Score from 1-10', validators=[DataRequired(),NumberRange(min=1, max=10)])

class RegisterForm(FlaskForm):
    """Form for adding users."""

    username = StringField('(Required) Username', validators=[DataRequired()])
    password = PasswordField('(Required) Password', validators=[Length(min=6)])
    email = StringField('(Required) E-mail', validators=[DataRequired(), Email()])
    image_url = StringField('(Optional) Image URL for Profile Picture')


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class EditUserForm(FlaskForm):
    """Edit form"""
    username = StringField('New Username')
    email = StringField('New E-mail', validators=[Optional(), Email()])
    image_url = StringField('New Profile Image URL')
    bio = StringField('New Bio')
    password =  PasswordField('New Password', validators=[Optional(), Length(min=6)])



