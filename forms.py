from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class MessageForm(FlaskForm):
    """Form for adding/editing messages (warbles)."""

    text = TextAreaField('text', validators=[DataRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users to database."""

    # Field for username, required input
    username = StringField('Username', validators=[DataRequired()])

    # Field for email, must be a valid email and required input
    email = StringField('E-mail', validators=[DataRequired(), Email()])

    # Field for password, must be at least 6 characters long and required input
    password = PasswordField('Password', validators=[Length(min=6)])

    # Optional field for profile image URL
    image_url = StringField('(Optional) Image URL')

class UserEditForm(FlaskForm):
    """Form for editing an existing user's information."""

    # Field for username, required input
    username = StringField('Username', validators=[DataRequired()])

    # Field for email, required input and must be a valid email
    email = StringField('Email', validators=[DataRequired(), Email()])

    # Optional field for profile image URL
    image_url = StringField('Profile Image URL', validators=[Optional()])

    # Optional field for header image URL
    header_image_url = StringField('Header Image URL', validators=[Optional()])

    # Optional field for bio
    bio = StringField('Bio', validators=[Optional()])

    # Password field, required input to confirm changes
    password = PasswordField('Password (required to confirm changes)', validators=[DataRequired()])

class LoginForm(FlaskForm):
    """Form for user login."""

    # Field for username, required input
    username = StringField('Username', validators=[DataRequired()])

    # Field for password, must be at least 6 characters long
    password = PasswordField('Password', validators=[Length(min=6)])
