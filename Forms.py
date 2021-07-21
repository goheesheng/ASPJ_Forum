from wtforms import validators, StringField, TextAreaField, PasswordField, SelectField, HiddenField,Form
from wtforms.fields import DateField
from wtforms_components import DateRange
from datetime import date
import re




class baseform(Form):
    csrf_token = HiddenField()


class SearchBarForm(baseform):
    searchQuery = StringField('Search Query', render_kw={"placeholder": "Search for a post..."})
    topic = SelectField('Topic')

class FeedbackForm(baseform):
    userID = HiddenField()
    reason = StringField('Reason', [validators.DataRequired()], render_kw={"placeholder": "e.g. Feedback regarding post moderation"})
    comment = TextAreaField('Comment', [validators.DataRequired()], render_kw={"rows": 10, "placeholder": "Enter comment here..."})

class LoginForm(baseform):
    username = StringField('Username', [validators.DataRequired(),validators.Regexp(re.compile('^([a-zA-Z0-9]+)([a-zA-Z0-9]{2,5})$'))]) #,message= "Username can contain only alphanumeric characters!")])
    password = PasswordField('Password', [validators.DataRequired()])

class SignUpForm(baseform):
    today = str(date.today())
    year, month, day = today.split('-')
    minYear = int(year) - 13
    month, day = int(month), int(day)
    email = StringField('Email Address', [validators.DataRequired(), validators.Regexp(re.compile('^.+@[^.].*\.[a-z]{2,10}$'), message="Invalid email address.")])
    username = StringField('Username', [validators.DataRequired(),validators.Regexp(re.compile('^([a-zA-Z0-9]+)([a-zA-Z0-9]{2,5})$'),message= "Username can contain only alphanumeric characters!")])
    dob = DateField('Date of Birth', [DateRange(max=date(minYear, month, day), message="You have to be at least 13 years old to register for an account.")])
    status = StringField('Status')
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.Regexp(re.compile('^(?=\S{10,20}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[^A-Za-z\s0-9])'), message= "Password must contain 10-20 characters, number, uppercase, lowercase, special character."),
        validators.EqualTo('confirmPassword', message='Passwords do not match.')
    ])
    confirmPassword = PasswordField('Re-enter Password', [validators.DataRequired()])

class UpdateEmail(baseform):
    email = StringField('Email Address', [validators.DataRequired(), validators.Regexp(r'^.+@[^.].*\.[a-z]{2,10}$', message="Invalid email address.")])

class UpdateUsername(baseform):
    username = StringField('Username', [validators.DataRequired()])

class UpdateStatus(baseform):
    status = StringField('Status')

class UpdatePassword(baseform):
    email = StringField('Email Address', [validators.DataRequired(), validators.Regexp(r'^.+@[^.].*\.[a-z]{2,10}$', message="Invalid email address.")])
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.Regexp(re.compile('^(?=\S{10,20}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[^A-Za-z\s0-9])'), message= "Password must contain 10-20 characters, number, uppercase, lowercase, special character."),
        validators.EqualTo('confirmPassword', message='Passwords do not match.')
    ])
    confirmPassword = PasswordField('Re-enter Password', [validators.DataRequired()])

class PostForm(baseform):
    userID = HiddenField()
    topic = SelectField('Topic')
    title = StringField('Title', [validators.DataRequired()], render_kw={"placeholder": "e.g. Error Exception handling in Python"})
    content = TextAreaField('Content', [validators.DataRequired()], render_kw={"rows": 10, "placeholder": "Enter content here..."})

class CommentForm(baseform):
    userID = HiddenField()
    comment = TextAreaField('Comment', [validators.DataRequired()], render_kw={"rows": 3, "placeholder": "Enter comment here..."})

class ReplyForm(baseform):
    userID = HiddenField()
    repliedID = HiddenField()
    reply = TextAreaField('Comment', [validators.DataRequired()], render_kw={"rows": 3, "placeholder": "Enter comment here..."})

class ReplyFeedbackForm(baseform):
    # repliedID = HiddenField()
    reply = TextAreaField('Reply', [validators.DataRequired()], render_kw={"rows": 3, "placeholder": "Enter reply here..."})

class TopicForm(baseform):
    topic = StringField('Topic', [validators.DataRequired()])

class OTPForm(baseform):
    otp = StringField('OTP', [validators.DataRequired()])

class enterUsernameForm(Form):
    # for forget password
    username = StringField('Username', [validators.DataRequired(),validators.Regexp(re.compile('^([a-zA-Z0-9]+)([a-zA-Z0-9]{2,5})$'),message= "Username can contain only alphanumeric characters!")])

