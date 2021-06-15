from wtforms import Form, validators, StringField, TextAreaField, PasswordField, SelectField, HiddenField
from wtforms.fields import DateField
from wtforms_components import DateRange
from datetime import date

class SearchBarForm(Form):
    searchQuery = StringField('Search Query', [validators.DataRequired()], render_kw={"placeholder": "Search for a post..."})
    topic = SelectField('Topic')

class FeedbackForm(Form):
    userID = StringField('User ID')
    reason = StringField('Reason', [validators.DataRequired()], render_kw={"placeholder": "e.g. Feedback regarding post moderation"})
    comment = TextAreaField('Comment', [validators.DataRequired()], render_kw={"rows": 10, "placeholder": "Enter comment here..."})

class LoginForm(Form):
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])

class SignUpForm(Form):
    today = str(date.today())
    year, month, day = today.split('-')
    minYear = int(year) - 13
    month, day = int(month), int(day)

    email = StringField('Email Address', [validators.DataRequired(), validators.Regexp(r'^.+@[^.].*\.[a-z]{2,10}$', message="Invalid email address.")])
    username = StringField('Username', [validators.DataRequired()])
    dob = DateField('Date of Birth', [DateRange(max=date(minYear, month, day), message="You have to be at least 13 years old to register for an account.")])
    status = StringField('Status')
    name = StringField('Full Name', [validators.DataRequired()])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirmPassword', message='Passwords do not match.')
    ])
    confirmPassword = PasswordField('Re-enter Password', [validators.DataRequired()])


class PostForm(Form):
    userID = StringField('User ID')
    topic = SelectField('Topic')
    title = StringField('Title', [validators.DataRequired()], render_kw={"placeholder": "e.g. Error Exception handling in Python"})
    content = TextAreaField('Content', [validators.DataRequired()], render_kw={"rows": 10, "placeholder": "Enter content here..."})

class CommentForm(Form):
    comment = TextAreaField('Comment', [validators.DataRequired()], render_kw={"rows": 3, "placeholder": "Enter comment here..."})

class ReplyForm(Form):
    repliedID = HiddenField()
    reply = TextAreaField('Comment', [validators.DataRequired()], render_kw={"rows": 3, "placeholder": "Enter comment here..."})

class ReplyFeedbackForm(Form):
    # repliedID = HiddenField()
    reply = TextAreaField('Reply', [validators.DataRequired()], render_kw={"rows": 3, "placeholder": "Enter reply here..."})

class TopicForm(Form):
    topic = StringField('Topic', [validators.DataRequired()])
