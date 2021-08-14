from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, \
    send_from_directory, session, get_flashed_messages, abort
from flask_talisman import Talisman
from functools import wraps
import mysql.connector, re, random
from datetime import datetime, timedelta  # for session timeout
# file uploads
from werkzeug.utils import secure_filename
import imghdr,os,base64,secrets,sys,DatabaseManager,Forms,logging
from logging.handlers import SMTPHandler
from flask_mail import Mail, Message
from flask import Flask, redirect, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)


from oauthlib.oauth2 import WebApplicationClient
import requests

GOOGLE_CLIENT_ID ="712694618800-4dh6s5mhdl62fhrbafnedkpbqggj7ome.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "E7vsZe1K44KoZofsH69hZSlH"
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

print(GOOGLE_CLIENT_ID)

client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Do set this
# os.environ['DB_USERNAME'] = 'ASPJuser'
# os.environ['DB_PASSWORD'] = 'P@55w0rD'
#
# print(os.environ['DB_USERNAME'])
# print(os.environ.['DB_PASSWORD'])
# os.environ['DB_USERNAME'] = 'ASPJuser'
# os.environ['DB_PASSWORD'] = 'P@55w0rD'

db = mysql.connector.connect(
    host="localhost",
    user=os.environ['DB_USERNAME'],  # do not want to leak the db username
    password=os.environ['DB_PASSWORD'],  # do not want to leak the db password
    database="mydatabase"
)

tupleCursor = db.cursor(buffered=True)
dictCursor = db.cursor(buffered=True, dictionary=True)
tupleCursor.execute("SHOW TABLES")
print(tupleCursor)

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)


# line 42 - 43 For file upload
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']


"self' means localhost, local filesystem, or anything on the same host. It doesn't mean any of those. " \
"It means sources that have the same scheme (protocol), " \
"same host, and same port as the file the content policy is defined in. " \
"Serving your site over HTTP? No https for you then, unless you define it explicitly."
csp = {
    'script-src': [
        '\'self\'',
        'https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/js/bootstrap.min.js',
        'https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js',
        'https://code.jquery.com/jquery-3.5.1.slim.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css',
        'https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css',
        'http://127.0.0.1:5000/templates/login.html',
        'https://accounts.google.com/gsi/client',

    ],
    #'img-src': 'http://127.0.0.1:5000/templates/login.html',
    'img-src': 'http://127.0.0.1:5000/static/uploads/',
}
talisman = Talisman(app, content_security_policy=csp, content_security_policy_nonce_in=['script-src','img-src'])

# Do set this, go discord and follow instructions
# os.environ['MAIL_USERNAME'] = 'appdevescip2003@gmail.com'
# os.environ['MAIL_PASSWORD'] = 'appdev7181'
#
# print(os.environ['MAIL_USERNAME'])
# print(os.environ['MAIL_PASSWORD'])


app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.environ['MAIL_USERNAME'],  # do not want to leak the mail username
    MAIL_PASSWORD=os.environ["MAIL_PASSWORD"],  # do not want to leak the mail password
    MAIL_DEBUG=True,
    MAIL_SUPPRESS_SEND=False,
    MAIL_ASCII_ATTACHMENTS=True,
    # Directory for admins to refer files (Files) #inside has session logs
    UPLOAD_FOLDER="templates\Files",
    permanent=True,
    expirydate=None
)
cursor = db.cursor()
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
mail = Mail(app)

#logging scheninagans
#serialization loggercode
serializationlogger=logging.getLogger(__name__+"serializer")
serializationlogger.setLevel(logging.DEBUG)
formatterserialize=logging.Formatter('%(asctime)s:%(levelname)s:%(message)s:%(ipaddress)s:%(username)s')
file_handlerserialize=logging.FileHandler('logs/serialization.txt')
file_handlerserialize.setFormatter(formatterserialize)
serializationlogger.addHandler(file_handlerserialize)

#loginsystemlogger
loginlogger=logging.getLogger(__name__+"login")
loginlogger.setLevel(logging.DEBUG)
formatterlogin=logging.Formatter('%(asctime)s:%(levelname)s:%(message)s:%(ipaddress)s:%(username)s')
file_handler_login=logging.FileHandler('logs/login.txt')
file_handler_login.setFormatter(formatterlogin)
loginlogger.addHandler(file_handler_login)



class customFiler(logging.Filter):
    def __init__(self,ipaddress,username='AnnoynomousUser'):
        self.username=username
        self.ipaddress=ipaddress

    def filter(self,record):
        record.ipaddress=self.ipaddress
        record.username=self.username
        return True

#For file upload

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(stream):
    header = stream.read(512)  # 512 bytes should be enough for a header check
    stream.seek(0)  # reset stream pointer
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')



def custom_login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if session is None:
            return redirect(url_for('login'))

        if app.config['expirydate'] is not None and app.config['expirydate']<= datetime.utcnow():
            flash('sesison expired','warning')
            app.config['expirydate']=None
            return redirect(url_for('login'))

        if session.get('csrf_token') is None:
            print('session modifed')
            ipaddress=request.remote_addr
            if app.config['lastusername'] is not None:
                print('hello world')
                filter=customFiler(ipaddress,app.config['lastusername'])
            else:
                filter = customFiler(ipaddress)


            serializationlogger.addFilter(filter)
            serializationlogger.warning('Cookie has been modified')
            return redirect(url_for('login'))

        if 'login' not in session or session['login']!=True:
            flash("Please log in to access this page","warning")
            return redirect(url_for('login'))

        return f(*args,**kwargs)

    return wrap

# broken access control fix
# @identity_loaded.connect_via(app)
# def on_identity_loaded(sender, identity):
#     # set the identity user object
#     identity.user = current_user
#     # add the UserNeed to the identity
#     if not session['isAdmin']:
#         # create a permission with a single Need, in this case a RoleNeed.
#         admin_permission = Permission(RoleNeed('admin'))


# brute force attack prevention on password field
class Tries:
    def __init__(self, tries):
        self.tries = tries
        self.default_tries = tries

    def get_tries(self):
        return self.tries

    def reset_tries(self):
        self.tries = self.default_tries

    def add_tries(self, num):
        self.tries += num


tries = Tries(0)


def get_all_topics(option):
    sql = "SELECT TopicID, Content FROM topic ORDER BY Content"
    dictCursor.execute(sql)
    listOfTopics = dictCursor.fetchall()
    topicTuples = []
    for topic in listOfTopics:
        topicTuples.append((str(topic['TopicID']), topic['Content']))

    if option == 'all':
        topicTuples.insert(0, ('0', 'All Topics'))
    return topicTuples

@app.route('/temp', methods=["POST"])
def temp():
    flash('Please login to upvote or downvote',"warning")
    return make_response(jsonify(url_for('login')),200)
import json
@app.route("/googlelogin/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    print( userinfo_response.json().get("email_verified"))
    print(userinfo_response.json())
    print('logged in')
    return redirect(url_for("home"))


@custom_login_required
@app.route('/postVote', methods=["GET", "POST"])
def postVote():
    data = request.get_json(force=True)
    currentVote = DatabaseManager.get_user_post_vote(str(session.get('userID')), data['postID'])

    if currentVote == None:
        if data['voteValue'] == '1':
            toggleUpvote = True
            toggleDownvote = False
            newVote = 1
            upvoteChange = '+1'
            downvoteChange = '0'
        else:
            toggleUpvote = False
            toggleDownvote = True
            newVote = -1
            upvoteChange = '0'
            downvoteChange = '+1'

        DatabaseManager.insert_post_vote(str(session.get('userID')), data['postID'], data['voteValue'])

    else:  # If vote for post exists
        if currentVote['Vote'] == 1:
            upvoteChange = '-1'
            if data['voteValue'] == '1':
                toggleUpvote = True
                toggleDownvote = False
                newVote = 0
                downvoteChange = '0'
            else:
                toggleUpvote = True
                toggleDownvote = True
                newVote = -1
                downvoteChange = '+1'

        else:  # currentVote['Vote']==-1
            downvoteChange = '-1'
            if data['voteValue'] == '1':
                toggleUpvote = True
                toggleDownvote = True
                newVote = 1
                upvoteChange = '+1'
            else:
                toggleUpvote = False
                toggleDownvote = True
                newVote = 0
                upvoteChange = '0'

        if newVote == 0:
            DatabaseManager.delete_post_vote(str(session.get('userID')), data['postID'])
        else:
            DatabaseManager.update_post_vote(str(newVote), str(session.get('userID')), data['postID'])

    DatabaseManager.update_overall_post_vote(upvoteChange, downvoteChange, data['postID'])
    updatedVoteTotal = DatabaseManager.calculate_updated_post_votes(data['postID'])
    return make_response(jsonify({'toggleUpvote': toggleUpvote, 'toggleDownvote': toggleDownvote
                                     , 'newVote': newVote, 'updatedVoteTotal': updatedVoteTotal,
                                  'postID': data['postID']}), 200)

@custom_login_required
@app.route('/commentVote', methods=["GET", "POST"])
def commentVote():
    data = request.get_json(force=True)
    currentVote = DatabaseManager.get_user_comment_vote(str(session.get('userID')), data['commentID'])
    if currentVote == None:
        if data['voteValue'] == '1':
            toggleUpvote = True
            toggleDownvote = False
            newVote = 1
            upvoteChange = '+1'
            downvoteChange = '0'
        else:
            toggleUpvote = False
            toggleDownvote = True
            newVote = -1
            upvoteChange = '0'
            downvoteChange = '+1'

        DatabaseManager.insert_comment_vote(str(session.get('userID')), data['commentID'], data['voteValue'])

    else:  # If vote for post exists
        if currentVote['Vote'] == 1:
            upvoteChange = '-1'
            if data['voteValue'] == '1':
                toggleUpvote = True
                toggleDownvote = False
                newVote = 0
                downvoteChange = '0'
            else:
                toggleUpvote = True
                toggleDownvote = True
                newVote = -1
                downvoteChange = '+1'

        else:  # currentVote['Vote']==-1
            downvoteChange = '-1'
            if data['voteValue'] == '1':
                toggleUpvote = True
                toggleDownvote = True
                newVote = 1
                upvoteChange = '+1'
            else:
                toggleUpvote = False
                toggleDownvote = True
                newVote = 0
                upvoteChange = '0'

        if newVote == 0:
            DatabaseManager.delete_comment_vote(str(session.get('userID')), data['commentID'])
        else:
            DatabaseManager.update_comment_vote(str(newVote), str(session.get('userID')), data['commentID'])

    DatabaseManager.update_overall_comment_vote(upvoteChange, downvoteChange, data['commentID'])
    updatedCommentTotal = DatabaseManager.calculate_updated_comment_votes(data['commentID'])
    return make_response(jsonify({'toggleUpvote': toggleUpvote, 'toggleDownvote': toggleDownvote
                                     , 'newVote': newVote, 'updatedCommentTotal': updatedCommentTotal,
                                  'commentID': data['commentID']}), 200)

@app.route('/')
def main():
    return redirect("/home")


# # for flask session timeout
# @app.route('/hello')
# def hello():
#     if current_user.is_authenticated:
#         return 'Hello %s!' %current_user.name
#     else:
#         return 'You are not logged in!'
#
#
# @app.route('/settings')
# @login_required
# def settings():
#     pass


@app.route('/home', methods=["GET", "POST"])
def home():
    searchBarForm = Forms.SearchBarForm(request.form)
    searchBarForm.topic.choices = get_all_topics('all')
    if request.method=="GET":
        session['csrf_token']= base64.b64encode(os.urandom(16))

    if request.method == "POST" and searchBarForm.validate():
        print(searchBarForm.csrf_token.data) #technically we translate the bytes to literally string
        print(type(searchBarForm.csrf_token.data))
        print(session.get('csrf_token'))
        if searchBarForm.csrf_token.data!=str(session.get('csrf_token')):
            # print('enter')
            return redirect(url_for('login'))
    if request.method == 'POST' and searchBarForm.validate():
        return redirect(
            url_for('searchPosts', searchQuery=searchBarForm.searchQuery.data, topic=searchBarForm.topic.data))

    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, post.TopicID, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " ORDER BY post.PostID DESC LIMIT 6"

    dictCursor.execute(sql)
    recentPosts = dictCursor.fetchall()

    for post in recentPosts:
        if session.get('login'):
            currentVote = DatabaseManager.get_user_post_vote(str(session.get('userID')), str(post['PostID']))
            if currentVote == None:
                post['UserVote'] = 0
            else:
                post['UserVote'] = currentVote['Vote']
        else:
            post['UserVote'] = 0
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        post['Content'] = post['Content'][:200]
    print(session)
    print(get_all_topics('all'))


    return render_template('home.html', currentPage='home', **session, searchBarForm=searchBarForm,recentPosts=recentPosts)

@app.route('/searchPosts', methods=["GET", "POST"])
def searchPosts():
    session['prevPage'] = request.headers.get("Referer")

    searchBarForm = Forms.SearchBarForm(request.form)
    searchBarForm.topic.choices = get_all_topics('all')

    if request.method=="GET":
        session['csrf_token']= base64.b64encode(os.urandom(16))

    if request.method == "POST" and searchBarForm.validate():
        print(searchBarForm.csrf_token.data) #technically we translate the bytes to literally string
        print(type(searchBarForm.csrf_token.data))
        print(session.get('csrf_token'))
        if searchBarForm.csrf_token.data!=str(session.get('csrf_token')):
            # print('enter')
            return redirect(url_for('login'))
    if request.method == 'POST' and searchBarForm.validate():
        print('here2')
        return redirect(
            url_for('searchPosts', searchQuery=searchBarForm.searchQuery.data, topic=searchBarForm.topic.data))

    searchQuery = request.args.get('searchQuery', default='')
    searchBarForm.searchQuery.data = searchQuery

    searchTopic = request.args.get('topic', default='0')
    searchBarForm.topic.data = int(searchTopic)

    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.userID=user.userID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " WHERE post.Title LIKE %s"

    print(type(sql))

    searchQuery = "%" + searchQuery + "%"

    if searchTopic != '0':
        sql += " AND topic.TopicID = %s"  # if there is a topic
        val = (searchQuery, searchTopic)
    else:
        val = (searchQuery,)  # escape values (Almost forgetten about this), It is crucial.

    dictCursor.execute(sql, val)
    relatedPosts = dictCursor.fetchall()
    for post in relatedPosts:
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        post['Content'] = post['Content'][:200]

    return render_template('searchPost.html', currentPage='search', **session, searchBarForm=searchBarForm,
                           postList=relatedPosts)

@custom_login_required
@app.route('/viewPost/<int:postID>/', methods=["GET", "POST"])
def viewPost(postID):
    print('i')
    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID = user.UserID"
    sql += " INNER JOIN topic ON post.TopicID = topic.TopicID"
    sql += " WHERE PostID = %s"
    val = (postID,)
    dictCursor.execute(sql, val)
    post = dictCursor.fetchone()
    post['TotalVotes'] = post['Upvotes'] - post['Downvotes']

    currentVote = DatabaseManager.get_user_post_vote(str(session.get('userID')), str(postID))
    if currentVote == None:
        post['UserVote'] = 0
    else:
        post['UserVote'] = currentVote['Vote']

    sql = "SELECT comment.CommentID, comment.Content, comment.DatetimePosted, comment.Upvotes, comment.Downvotes, comment.DatetimePosted, user.Username FROM comment"
    sql += " INNER JOIN user ON comment.UserID=user.UserID"
    sql += " WHERE comment.PostID=%s"
    val = (postID,)
    dictCursor.execute(sql, val)
    commentList = dictCursor.fetchall()
    for comment in commentList:
        comment['TotalVotes'] = comment['Upvotes'] - comment['Downvotes']

        currentVote = DatabaseManager.get_user_comment_vote(str(session.get('userID')), str(comment['CommentID']))
        if currentVote == None:
            comment['UserVote'] = 0
        else:
            comment['UserVote'] = currentVote['Vote']

        sql = "SELECT reply.Content, reply.DatetimePosted, reply.DatetimePosted, user.Username FROM reply"
        sql += " INNER JOIN user ON reply.UserID=user.UserID"
        sql += " WHERE reply.CommentID=%s"
        val = (comment['CommentID'],)
        dictCursor.execute(sql, val)
        replyList = dictCursor.fetchall()
        comment['ReplyList'] = replyList

    commentForm = Forms.CommentForm(request.form)
    commentForm.userID.data = session.get('userID')
    replyForm = Forms.ReplyForm(request.form)
    replyForm.userID.data = session.get('userID')

    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and commentForm.validate():
        print(commentForm.csrf_token.data)  # technically we translate the bytes to literally string
        print(type(commentForm.csrf_token.data))
        print(session.get('csrf_token'))
        if commentForm.csrf_token.data != (session.get('csrf_token')):
            # print('enter')
            return redirect(url_for('login'))
    if request.method == 'POST' and commentForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO comment (PostID, UserID, Content, DateTimePosted, Upvotes, Downvotes) VALUES (%s, %s, %s, %s, %s, %s)'
        val = (postID, commentForm.userID.data, commentForm.comment.data, dateTime, 0, 0)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Comment posted!', 'success')
        # return redirect('/viewPost/%d/%d' %(postID,session['login']))
        return redirect('/viewPost/%d' % (postID))

    if request.method == 'POST' and replyForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO reply (UserID, CommentID, Content, DateTimePosted) VALUES (%s, %s, %s, %s)'
        val = (replyForm.userID.data, replyForm.repliedID.data, replyForm.reply.data, dateTime)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Comment posted!', 'success')
        # return redirect('/viewPost/%d/%d' %(postID, session['login']))
        return redirect('/viewPost/%d' % (postID))
    return render_template('viewPost.html', currentPage='viewPost', **session, commentForm=commentForm,
                           replyForm=replyForm, post=post, commentList=commentList)

@custom_login_required
@app.route('/addPost', methods=["GET", "POST"])
def addPost():
    sql = "SELECT TopicID, Content FROM topic ORDER BY Content"
    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()

    postForm = Forms.PostForm(request.form)
    postForm.topic.choices = get_all_topics('default')
    postForm.userID.data = session.get('userID')
    if request.method=="GET":
        session['csrf_token']= base64.b64encode(os.urandom(16))

    if request.method == "POST" and postForm.validate():
        print(postForm.csrf_token.data) #technically we translate the bytes to literally string
        print(type(postForm.csrf_token.data))
        print(session.get('csrf_token'))
        if postForm.csrf_token.data!=str(session.get('csrf_token')):
            # print('enter')
            return redirect(url_for('login'))
    if request.method == 'POST' and postForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO post (TopicID, UserID, DateTimePosted, Title, Content, Upvotes, Downvotes) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        val = (postForm.topic.data, postForm.userID.data, dateTime, postForm.title.data, postForm.content.data, 0, 0)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Post successfully created!', 'success')
        return redirect('/home')

    return render_template('addPost.html', currentPage='addPost', **session, postForm=postForm)

@custom_login_required
@app.route('/feedback', methods=["GET", "POST"])
def feedback():
    print(session)
    feedbackForm = Forms.FeedbackForm(request.form)
    feedbackForm.userID.data = session.get('userID')
    if request.method=="GET":
        session['csrf_token']= base64.b64encode(os.urandom(16))

    if request.method == "POST" and feedbackForm.validate():
        print(feedbackForm.csrf_token.data) #technically we translate the bytes to literally string
        print(type(feedbackForm.csrf_token.data))
        print(session.get('csrf_token'))
        if feedbackForm.csrf_token.data!=str(session.get('csrf_token')):
            # print('enter')
            return redirect(url_for('login'))
    if request.method == 'POST' and feedbackForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO feedback (UserID, Reason, Content, DateTimePosted, Resolved) VALUES (%s, %s, %s, %s, %s)'
        val = (feedbackForm.userID.data, feedbackForm.reason.data, feedbackForm.comment.data, dateTime, 0)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Feedback sent!', 'success')
        return redirect("/home")
    return render_template('feedback.html', currentPage='feedback', **session, feedbackForm=feedbackForm)

@app.route('/googlelogin',methods=["GET","POST"])
def googlelogin():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route('/login', methods=["GET", "POST"])
def login():
    # # setting session timeout
    # session.permanent = True
    # app.permanent_session_lifetime = timedelta(minutes=1)
    # if form is submitted
    loginForm = Forms.LoginForm(request.form)
    print(get_flashed_messages())

    if request.method=="GET":
        session['csrf_token']= base64.b64encode(os.urandom(16))

    if request.method == "POST" and loginForm.validate():
        print(loginForm.csrf_token.data) #technically we translate the bytes to literally string
        print(type(loginForm.csrf_token.data))
        print(session.get('csrf_token'))
        if loginForm.csrf_token.data!=str(session.get('csrf_token')):
            # print('enter')
            return redirect(url_for('login'))
        else:
            sql = "SELECT UserID, Email, Username, Password FROM user WHERE Username = %s"
            val = (loginForm.username.data,)
            dictCursor.execute(sql, val)
            findUser = dictCursor.fetchone()
            if findUser ==None  or loginForm.password.data != findUser["Password"]:
                loginForm.password.errors.append('Wrong username or password.')
                tries.add_tries(1)
                ipaddress = request.remote_addr
                filter = customFiler(ipaddress,"Anonymous")
                loginlogger.addFilter(filter)
                loginlogger.info(f'Login attempt of {tries.get_tries()}')

            else:
                tries.reset_tries()
                # flask session timeout

                session['login'] = True
                session['userID'] = int(findUser['UserID'])
                session['username'] = findUser['Username']

                sql = "SELECT * FROM admin WHERE UserID=%s"
                val = (int(findUser['UserID']),)
                dictCursor.execute(sql, val)
                findAdmin = dictCursor.fetchone()
                sql = "UPDATE user SET LoginAttempts = %s WHERE Username = %s"
                val = (str(0), findUser['Username'])
                tupleCursor.execute(sql, val)
                db.commit()
                flash('Welcome! You are now logged in as %s.' % (session['username']), 'success')
                session.permanent = True
                app.permanent_session_lifetime = timedelta(seconds=50)
                app.config['expirydate']=app.session_interface.get_expiration_time(app,session)
                app.config['lastusername']=session['username']
                if findAdmin != None:
                    session['isAdmin'] = True
                    return redirect('/adminHome')
                else:
                    session['isAdmin'] = False
                    return redirect('/home')

            render_template("login.html", loginForm=loginForm, tries=tries)
    return render_template("login.html", loginForm=loginForm, tries=tries)

@app.route('/logout')
@custom_login_required
# flask session timeout
def logout():
    # timed_out = request.args.get('timeout')
    # if request.args.get('timeout'):
    #     flash('Session timeout, please re-login.', 'warning')
    session["name"] = None
    session['isAdmin']=False
    session['login'] = False
    session['userID'] = 0
    session['username'] = ''
    app.config['expirydate']=None
    app.config['lastusername']=None
    return redirect("/home")
    # return render_template('home.html', timed_out=timed_out)



#flask_wtf is shit
# sign up final stage
@app.route('/login/<link>', methods=["GET", "POST"])
def otp(link):
    global temp_signup
    otpform = Forms.OTPForm(request.form)
    if request.method == "GET":
        session['csrf_token']= base64.b64encode(os.urandom(16))

    if request.method == "POST" and otpform.validate():
        print(otpform.csrf_token.data) #technically we translate the bytes to literally string
        print(type(otpform.csrf_token.data))
        print(session.get('csrf_token'))
        if otpform.csrf_token.data!=str(session.get('csrf_token')):
            # print('enter')
            return redirect(url_for('login'))
    sql = "SELECT otp, TIME_TO_SEC(TIMEDIFF(%s, Time_Created)) from otp WHERE link = %s"  # set timer for opt 3 mins, time_created was created in db schema
    val = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), link)  # retrieve current time
    tupleCursor.execute(sql, val)
    otp = tupleCursor.fetchone()
    print(val)
    print(otp, 'otoptuple')
    if otp is None:  # Null
        abort(404)
    print(otpform.validate())
    print(otpform.otp.data)
    if request.method == "POST" and otpform.validate():
        if otp[1] > 180:
            flash('Your OTP has expired. Please resubmit the signup form', 'danger')
            sql = "DELETE from otp WHERE link =%s"
            val = (link,)
            tupleCursor.execute(sql, val)
            temp_signup.pop(link)
            db.commit()
            return redirect('/signup')
        print(otp, 'test')
        temp_details = temp_signup[link]
        print(otp[1], otp[0], otp, 'otp')
        if str(otp[0]) == otpform.otp.data:
            try:
                sql = "INSERT INTO user (Email, Username, Birthday, Password) VALUES (%s, %s, %s, %s)"
                val = (temp_details["Email"], temp_details["Username"], temp_details["Birthday"],
                       temp_details["Password"])  # insert the data only after OTP is successful
                tupleCursor.execute(sql, val)
                db.commit()

            except mysql.connector.errors.IntegrityError as errorMsg:  # Prevent Error-based sql injection
                errorMsg = str(errorMsg)
                print('error here')
                if 'email' in errorMsg.lower():
                    otpform.otp.errors.append(
                        'The email has already been linked to another account. Please use a different email.')
                elif 'username' in errorMsg.lower():
                    otpform.otp.errors.append('This username is already taken.')

            else:
                print('pass')
                temp_signup.pop(link)
                sql = "DELETE from otp WHERE link =%s"  # ensure otp with same link wont be exploited
                val = (link,)
                tupleCursor.execute(sql, val)
                db.commit()
                sql = "SELECT UserID, Username FROM user WHERE Username=%s AND Password=%s"
                val = (temp_details["Username"], temp_details["Password"])
                tupleCursor.execute(sql, val)
                findUser = tupleCursor.fetchone()
                session['login'] = True
                session['userID'] = int(findUser[0])
                session['username'] = findUser[1]

                flash('Account successfully created! You are now logged in as %s.' % (session['username']), 'success')
                return redirect('/home')

        elif temp_details[
            "Resend count"] < 3:  # if wrong password, resend otp again of which i do not want, not fixed pls fix
            print('resend')
            temp_details["Resend count"] += 1
            OTP = random.randint(100000, 999999)
            sql = "UPDATE otp SET otp =%s WHERE link =%s"
            val = (OTP, link)
            tupleCursor.execute(sql, val)
            db.commit()
            try:
                msg = Message("ASPJ Signup",
                              sender=os.environ['MAIL_USERNAME'],
                              recipients=[temp_details["Email"]])
                msg.body = "OTP for Sign Up"
                msg.html = render_template('otp_email.html', OTP=OTP, username=temp_details["Username"])
                mail.send(msg)
            except Exception as e:
                print(e)
                print("Error:", sys.exc_info()[0])
                print("goes into except")
            else:
                flash("Wrong OTP, please try again!", "warning")
                return redirect("/login/" + link)

        else:
            flash("You have failed OTP too many times. Please recheck your details before you submit the sign up form!",
                  'danger')
            return redirect("/signup")

    return render_template('otp.html', otpform=otpform)


temp_signup = {}


@app.route('/signup', methods=["GET", "POST"])
def signUp():
    global temp_signup
    signUpForm = Forms.SignUpForm(request.form)
    otpform = Forms.OTPForm(request.form)
    print(session)
    if request.method=="GET":
        session['csrf_token']= base64.b64encode(os.urandom(16))

    if request.method == "POST" and signUpForm.validate():
        print(signUpForm.csrf_token.data) #technically we translate the bytes to literally string
        print(type(signUpForm.csrf_token.data))
        print(session.get('csrf_token'))
        print(type(session.get('csrf_token')))
        if signUpForm.csrf_token.data!=str(session.get('csrf_token')):
            print('enter')
            return redirect(url_for('login'))
    if request.method == 'POST' and signUpForm.validate():
        temp_details = {}
        temp_details["Email"] = signUpForm.email.data
        temp_details["Username"] = signUpForm.username.data
        temp_details["Birthday"] = str(signUpForm.dob.data)
        temp_details["Status"] = signUpForm.status.data
        temp_details["Password"] = signUpForm.password.data
        temp_details["Resend count"] = 0
        OTP = random.randint(100000, 999999)
        link = secrets.token_urlsafe()
        temp_signup[link] = temp_details
        try:
            sql = "INSERT INTO otp (link, otp) VALUES (%s, %s)"
            val = (link, str(OTP))
            tupleCursor.execute(sql, val)
            db.commit()
        except mysql.connector.errors.OperationalError:
            abort(500)
        try:
            msg = Message("ASPJ Forum Signup",
                          sender=os.environ.get('MAIL_USERNAME'),
                          recipients=[temp_details["Email"]])
            msg.body = "OTP for Sign Up"
            msg.html = render_template('otp_email.html', OTP=OTP, username=temp_details["Username"])
            mail.send(msg)
        except Exception as e:
            print(e)
            print("Error:", sys.exc_info()[0])
            print("goes into except")
        else:
            flash('Please enter the OTP that was sent to your email.', 'warning')
            flash('The OTP will expire in 3 mins', 'warning')
            # return render_template('otp.html')
            return redirect('/login/' + str(link))

    return render_template('signup.html', currentPage='signUp', **session, signUpForm=signUpForm)

@app.route('/profile/<username>', methods=["GET", "POST"])
@custom_login_required
def profile(username):
    updateEmailForm = Forms.UpdateEmail(request.form)
    updateUsernameForm = Forms.UpdateUsername(request.form)
    updateStatusForm = Forms.UpdateStatus(request.form)
    updatePasswordForm = Forms.UpdatePassword(request.form)
    if request.method=="GET":
        session['csrf_token']= base64.b64encode(os.urandom(16))
    if request.method == "POST" and updateUsernameForm.validate():
        print(updateUsernameForm.csrf_token.data) #technically we translate the bytes to literally string
        print(type(updateUsernameForm.csrf_token.data))
        print(session.get('csrf_token'))
        if updateUsernameForm.csrf_token.data!=str(session.get('csrf_token')):
            # print('enter')
            return redirect(url_for('login'))
    sql = "SELECT Username, Status, Email FROM user WHERE user.Username=%s"
    val = (username,)
    dictCursor.execute(sql, val)
    userData = dictCursor.fetchone()
    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " WHERE user.Username=%s"
    sql += " ORDER BY post.DatetimePosted DESC"
    val = (str(username),)
    dictCursor.execute(sql, val)
    recentPosts = dictCursor.fetchall()
    userData['Credibility'] = 0
    if userData['Status'] == None or userData['Status'].replace(" ", "") == "":
        userData['Status'] = userData['Username'] + " is too lazy to add a status"
    print(userData)
    for post in recentPosts:
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        userData['Credibility'] += post['TotalVotes']
        post['Content'] = post['Content'][:200]

    if request.method == "POST" and updateEmailForm.validate():
        print('updateemailform')
        sql = "UPDATE user "
        sql += "SET Email = %s"
        sql += "WHERE UserID = %s"
        try:
            val = (updateEmailForm.email.data, str(session["userID"]))
            print(val,str(session["userID"]),'12222222222222222222222222222222222222222222222222222222222')
            tupleCursor.execute(sql, val, )
            db.commit()
        except KeyError as errorMsg:  # Prevent error-based sql attack
            abort(404)
        except mysql.connector.errors.IntegrityError as errorMsg:  # Prevent error-based sql attack
            errorMsg = str(errorMsg)
            if 'email' in errorMsg.lower():
                updateEmailForm.email.errors.append(
                    'The email has already been linked to another account. Please use a different email.')
                flash("This email has already been linked to another account. Please use a different email.", "success")
        else:
            try:
                msg = Message("ASPJ Forum",
                              sender=os.environ['MAIL_USERNAME'],
                              recipients=[userData["Email"]])
                msg.body = "Profile Update"
                msg.html = render_template('update_email.html', value="Email",
                                           url="http://127.0.0.1:5000/changePassword/" + userData["Username"],
                                           username=userData["Username"])
                mail.send(msg)
            except Exception as e:
                print(e)
                print("Error:", sys.exc_info()[0])
                print("goes into except")
            else:
                flash('Account successfully updated!', 'success')

                return redirect('/profile/' + session['username'])

    if request.method == "POST" and updateUsernameForm.validate():
        print("updateusernameofrm")
        sql = "UPDATE user "
        sql += "SET Username=%s"
        sql += "WHERE UserID=%s"
        try:
            val = (updateUsernameForm.username.data, str(session["userID"]))
            tupleCursor.execute(sql, val)
            db.commit()

        except mysql.connector.errors.IntegrityError as errorMsg:  # Prevent error-based sql attack
            errorMsg = str(errorMsg)
            if 'username' in errorMsg.lower():
                flash("This username is already taken!", "success")
                updateUsernameForm.username.errors.append('This username is already taken.')
        else:
            sql = "SELECT Username from user WHERE UserID=%s"
            val = (int(session["userID"]),)
            dictCursor.execute(sql, val)
            ret = dictCursor.fetchone()
            db.commit()
            session['username'] = ret['Username']

            try:
                msg = Message("Lorem Ipsum",
                              sender=os.environ['MAIL_USERNAME'],
                              recipients=[userData["Email"]])
                msg.body = "Profile Update"
                msg.html = render_template('update_email.html', value="Username",
                                           url="http://127.0.0.1:5000/changePassword/" + userData["Username"],
                                           username=userData["Username"])
                mail.send(msg)
            except Exception as e:
                print(e)
                print("Error:", sys.exc_info()[0])
                print("goes into except")
            else:
                flash('Account successfully updated! Your username now is %s.' % (session['username']), 'success')
                return redirect('/profile/' + session['username'])

    if request.method == "POST" and updateStatusForm.validate():
        print('updatestatusform')
        sql = "UPDATE user "
        sql += "SET Status=%s"
        sql += "WHERE UserID=%s"
        try:
            val = (updateStatusForm.status.data, str(session["userID"]))
            tupleCursor.execute(sql, val)

            db.commit()

        except mysql.connector.errors.IntegrityError as errorMsg:
            errorMsg = str(errorMsg)
            flash("An unexpected error has occurred!", "warning")
        else:
            flash('Account successfully updated!', 'success')

            return redirect('/profile/' + session['username'])

    # updating password in profile
    # if request.method == "POST" and updatePasswordForm.validate():
    #     print('updatepasswordform')
    #     sql = "UPDATE user "
    #     sql += "SET Password=%s"
    #     sql += "WHERE UserID=%s"
    #     try:
    #         val = (updatePasswordForm.status.data, str(session["userID"]))
    #         tupleCursor.execute(sql, val)
    #
    #         db.commit()
    #
    #     except mysql.connector.errors.IntegrityError as errorMsg:
    #         errorMsg = str(errorMsg)
    #         flash("An unexpected error has occurred!", "warning")
    #     else:
    #         flash('Account successfully updated!', 'success')
    #
    #         return redirect('/profile/' + session['username'])

    return render_template("profile.html", currentPage="myProfile", **session, userData=userData,
                           recentPosts=recentPosts,
                           updateEmailForm=updateEmailForm, updateUsernameForm=updateUsernameForm,
                           updateStatusForm=updateStatusForm)


@app.route('/forgetPasslogin/<link>', methods=["GET","POST"])
def otp2(link):
    global temp_resetpass
    otpform = Forms.OTPForm(request.form)
    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and otpform.validate():
        print(otpform.csrf_token.data)
        print(type(otpform.csrf_token.data))
        print(session.get('csrf_token'))
        if otpform.csrf_token.data != str(session.get('csrf_token')):
            return redirect(url_for('login'))

    sql = "SELECT otp, TIME_TO_SEC(TIMEDIFF(%s, Time_Created)) from otp WHERE link = %s"
    val = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), link)
    tupleCursor.execute(sql, val)
    otp = tupleCursor.fetchone()
    print(val)
    print(otp, 'otptuple')
    if otp is None:
        abort(404)
    print(otpform.validate())
    print(otpform.otp.data)
    if request.method == "POST" and otpform.validate():
        if otp[1] > 180:
            flash('Your OTP has expired. Please resubmit the form', 'danger')
            sql = "DELETE from otp where link =%s"
            val = (link,)
            tupleCursor.execute(sql, val)
            temp_resetpass.pop(link)
            db.commit()
            return redirect('/forgetPassword')
        print(otp, 'test')
        temp_details = temp_resetpass.get(link)
        print(otp[1], otp[0], otp, 'otp')
        if str(otp[0]) == otpform.otp.data:
            try:
                # sql = "UPDATE user SET Password =%s WHERE Username =%s"
                sql = "UPDATE user "
                sql += "SET Password=%s"
                sql += "WHERE Username=%s"
                val = (temp_details["Password"], temp_details["Username"])
                tupleCursor.execute(sql, val)
                db.commit()

            except mysql.connector.errors.IntegrityError as errorMsg:
                errorMsg = str(errorMsg)
                print('error here')
                if 'email' in errorMsg.lower():
                    otpform.otp.errors.append('The email has already been linked to another account. Please use a different email.')
                elif 'username' in errorMsg.lower():
                    otpform.otp.errors.append('This username is already taken.')

            else:
                print('pass')
                temp_resetpass.pop(link)
                sql = "DELETE from otp WHERE link =%s"
                val = (link,)
                tupleCursor.execute(sql, val)
                db.commit()
                sql = "SELECT UserID, Username FROM user WHERE Username=%s AND Password=%s"
                val = (temp_details['Username'], temp_details["Password"])
                tupleCursor.execute(sql, val)
                findUser = tupleCursor.fetchone()
                session['login'] = True
                session['userID'] = int(findUser[0])
                session['username'] = findUser[1]

                flash('Account password changed successfully! You are now logged in as %s.' % (session['username']), 'success')
                return redirect('/home')

        elif temp_details[
            "Resend count"] <3:
            print('resend')
            temp_details["Resend count"] += 1
            OTP = random.randint(100000, 999999)
            sql = "UPDATE otp SET otp =%s WHERE link =%s"
            val = (OTP, link)
            tupleCursor.execute(sql, val)
            db.commit()
            try:
                msg = Message("ASPJ Forget Password",
                              sender = os.environ["MAIL_USERNAME"],
                              recipients = [temp_details['Email']])
                msg.body = "OTP for Forget Password"
                msg.html = render_template('otp_email.html', OTP=OTP, username=temp_details["Username"])
                mail.send(msg)
            except Exception as e:
                print(e)
                print("Error:", sys.exc_info()[0])
                print("goes into except")
            else:
                flash("Wrong OTP, please try again!", "warning")
                return redirect("/forgetPasslogin/" + link)

        else:
            flash("You have failed OTP too many times. Please recheck your details before submitting the form!", 'danger')
            return redirect('/forgetPassword')
    return render_template('otp.html', otpform=otpform)


temp_resetpass = {}
# forget password feature
@app.route('/forgetpassword', methods=["GET", "POST"])
def resetpass():
    global temp_resetpass
    forgetPasswordForm = Forms.UpdatePassword(request.form)
    otpform = Forms.OTPForm(request.form)
    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and forgetPasswordForm.validate():
        print(forgetPasswordForm.csrf_token.data)
        print(type(forgetPasswordForm.data))
        print(session.get('csrf_token'))
        if forgetPasswordForm.csrf_token.data != str(session.get('csrf_token')):
            return redirect(url_for('login'))

    if request.method == "POST" and forgetPasswordForm.validate():
        temp_details = {}
        temp_details["Email"] = forgetPasswordForm.email.data
        temp_details["Username"] = forgetPasswordForm.username.data
        temp_details["Password"] = forgetPasswordForm.password.data
        # temp_details["ConfirmPassword"] = forgetPasswordForm.confirmPassword.data
        temp_details["Resend count"] = 0
        OTP = random.randint(100000, 999999)
        link = secrets.token_urlsafe()
        temp_resetpass[link] = temp_details
        sql = "INSERT INTO otp (link, otp) VALUES (%s, %s)"
        val = (link, str(OTP))
        tupleCursor.execute(sql, val)
        db.commit()
        try:
            msg = Message("ASPJ Forum Forget Password",
                          sender = os.environ.get('MAIL_USERNAME'),
                          recipients = [temp_details["Email"]])
            msg.body = "OTP for Forget Password"
            msg.html = render_template('otp_email.html', OTP=OTP, username=temp_details["Username"])
            mail.send(msg)
        except Exception as e:
            print(e)
            print("Error:", sys.exc_info()[0])
            print("goes into except")
        else:
            flash('Please enter the OTP that was sent to your email.', 'warning')
            flash('The OTP will expire in 3 mins', 'warning')
            return redirect("/forgetPasslogin/" + str(link))
    return render_template('forgetpassword.html', currentPage='forgetPassword', **session, forgetPasswordForm=forgetPasswordForm, otpform=otpform)


# if all fails work on this
# # for forget password
# @app.route('/enterUsername', methods=['GET', 'POST'])
# def getUsername():
#     usernameForm = Forms.enterUsernameForm(request.form)
#     if request.method == "POST" and usernameForm.validate():
#         sql = "SELECT UserID, Email, Username, Password FROM user WHERE Username = %s"
#         val = (usernameForm.enterUsername.data,)
#         dictCursor.execute(sql, val)
#         findUser = dictCursor.fetchone()
#         if findUser == None:
#             usernameForm.enterUsername.errors.append('Wrong username entered.')
#         else:
#             return redirect('/changePssword')
#     return render_template('enterUsername.html', usernameForm=usernameForm)
#
#
# # changing password after entering the username
# @app.route('/changePassword', methods=["GET", "POST"])
# def resetpassword():
#     changePasswordForm = Forms.UpdatePassword(request.form)
#     if request.method == "POST" and changePasswordForm.validate():
#         password = changePasswordForm.password.data
#         sql = "UPDATE user SET Password=%s WHERE Username=%s"
#         val = (str(password), username)
#         tupleCursor.execute(sql, val)
#         db.commit()
#         flash("Password has been successfully reset",'success')
#         return redirect("/login")
#     return render_template('forgetpassword.html', changePasswordForm=changePasswordForm)


# user_to_url = {}
#
#
# @app.route('/changePassword/<username>', methods=["GET"])
# def changePassword(username):
#     global user_to_url
#     url = secrets.token_urlsafe()
#     sql = "INSERT INTO password_url(Url) VALUES(%s)"
#     val = (url,)
#     tupleCursor.execute(sql, val)
#     db.commit()
#     user_to_url[url] = username
#     user_email = "SELECT Email FROM user WHERE user.username=%s"
#     val = (username,)
#     tupleCursor.execute(user_email, val)
#     user_email = tupleCursor.fetchone()
#     abs_url = "http://127.0.0.1:5000/reset/" + url
#     try:
#         msg = Message("ASPJ Forum",
#                       sender=os.environ['MAIL_USERNAME'],
#                       recipients=[user_email[0]])
#         msg.body = "Password Change"
#         msg.html = render_template('email.html', postID="change password", username=username, content=0, posted=0,
#                                    url=abs_url)
#         mail.send(msg)
#     except Exception as e:
#         print(e)
#         print("Error:", sys.exc_info()[0])
#         print("goes into except")
#     else:
#         flash('A change password link has been sent to your email. Use it to update your password.', 'success')
#         flash('The password link will expire in 10 mins', 'warning')
#         if session['isAdmin']:
#             return redirect('/adminProfile/' + str(username))
#         else:
#             return redirect('/profile/' + str(username))
#
#
# @app.route('/reset/<url>', methods=["GET", "POST"])
# def resetPassword(url):
#     global user_to_url
#     sql = "SELECT TIME_TO_SEC(TIMEDIFF(%s, Time_Created)) FROM password_url WHERE Url = %s"
#     val = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), url)
#     tupleCursor.execute(sql, val)
#     reset = tupleCursor.fetchone()
#     if reset[0] > 600:
#         sql = "DELETE FROM password_url WHERE Url = %s"
#         val = (url,)
#         flash("Your password reset link has expired, please try again!", "danger")
#         return redirect("/home")
#     else:
#         changePasswordForm = Forms.UpdatePassword(request.form)
#         if request.method == "POST" and changePasswordForm.validate():
#             username = user_to_url[url]
#             password = changePasswordForm.password.data
#             sql = "UPDATE user SET Password=%s WHERE Username=%s"
#             val = (str(password), username)
#             tupleCursor.execute(sql, val)
#             db.commit()
#             user_to_url.pop(url)
#             flash("Password has been successfully reset", 'success')
#             return redirect("/login")
#         return render_template("forgetpassword.html", changePasswordForm=changePasswordForm)


@app.route('/topics')
@custom_login_required
def topics():
    sql = "SELECT Content,TopicID FROM topic ORDER BY Content "
    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()

    return render_template('topics.html', currentPage='topics', **session, listOfTopics=listOfTopics)


@app.route('/indivTopic/<topicID>', methods=["GET", "POST"])
@custom_login_required
def indivTopic(topicID):
    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " WHERE topic.TopicID = %s "
    val = (topicID,)
    dictCursor.execute(sql, val)
    recentPosts = dictCursor.fetchall()
    for post in recentPosts:
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        post['Content'] = post['Content'][:200]
    topic = "SELECT Content FROM topic WHERE topic.TopicID=%s"
    val = (topicID,)
    tupleCursor.execute(topic, val)
    topic = tupleCursor.fetchone()
    return render_template('indivTopic.html', currentPage='indivTopic', **session, recentPosts=recentPosts,
                           topic=topic[0])


@app.route('/adminProfile/<username>', methods=["GET", "POST"])
# broken access control fix
@custom_login_required
def adminUserProfile(username):
    if not session['isAdmin']:
        flash("You are not give access to view this. Please login.", "warning")
        return redirect(url_for('login'))
    elif session['isAdmin']:
        updateEmailForm = Forms.UpdateEmail(request.form)
        updateUsernameForm = Forms.UpdateUsername(request.form)
        updateStatusForm = Forms.UpdateStatus(request.form)
        sql = "SELECT Username, Status, Email FROM user WHERE user.Username=%s"
        val = (username,)
        dictCursor.execute(sql, val)
        userData = dictCursor.fetchone()
        sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.TopicID, topic.Content AS Topic FROM post"
        sql += " INNER JOIN user ON post.UserID=user.UserID"
        sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
        sql += " WHERE user.Username=%s"
        sql += " ORDER BY post.DatetimePosted DESC"
        val = (str(username),)
        dictCursor.execute(sql, val)
        recentPosts = dictCursor.fetchall()
        userData['Credibility'] = 0
        if userData['Status'] == None or userData['Status'].replace(" ", "") == "":
            userData['Status'] = userData['Username'] + " is too lazy to add a status"
        for post in recentPosts:
            post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
            userData['Credibility'] += post['TotalVotes']
            post['Content'] = post['Content'][:200]
        sql = "SELECT AdminID FROM admin WHERE UserID=(SELECT UserID FROM user WHERE Username=%s)"
        val = (username,)
        dictCursor.execute(sql, val)
        user = dictCursor.fetchone()
        if user is not None:
            admin = True
        else:
            admin = False

        if request.method == "POST" and updateEmailForm.validate():
            sql = "UPDATE user "
            sql += "SET Email=%s"
            sql += "WHERE UserID=%s"
            try:
                val = (updateEmailForm.email.data, str(session["userID"]))
                tupleCursor.execute(sql, val)
                data = tupleCursor.fetchone()
                db.commit()

            except mysql.connector.errors.IntegrityError as errorMsg:  # Prevent error-based sql attack
                errorMsg = str(errorMsg)
                if 'email' in errorMsg.lower():
                    updateEmailForm.email.errors.append(
                        'The email has already been linked to another account. Please use a different email.')
                    flash("This email has already been linked to another account. Please use a different email.", "success")
            else:
                flash('Account successfully updated!', 'success')

                return redirect('/adminProfile/' + session['username'])

        if request.method == "POST" and updateUsernameForm.validate():
            sql = "UPDATE user "
            sql += "SET Username=%s"
            sql += "WHERE UserID=%s"
            try:
                val = (updateUsernameForm.username.data, str(session["userID"]))
                tupleCursor.execute(sql, val)
                db.commit()

            except mysql.connector.errors.IntegrityError as errorMsg:
                errorMsg = str(errorMsg)
                if 'username' in errorMsg.lower():
                    flash("This username is already taken!", "success")
                    updateUsernameForm.username.errors.append('This username is already taken.')
            else:
                sql = "SELECT Username from user WHERE UserID=%s"
                val = (str(session["userID"]),)
                dictCursor.execute(sql, val)
                data = dictCursor.fetchone()
                db.commit()
                session['username'] = data['Username']
                flash('Account successfully updated! Your username now is %s.' % (session['username']), 'success')
                return redirect('/adminProfile/' + session['username'])

        if request.method == "POST" and updateStatusForm.validate():
            sql = "UPDATE user "
            sql += "SET Status=%s"
            sql += "WHERE UserID=%s"
            try:
                val = (updateStatusForm.status.data, str(session["userID"]))
                tupleCursor.execute(sql, val)
                db.commit()

            except mysql.connector.errors.IntegrityError as errorMsg:
                errorMsg = str(errorMsg)
                flash("An unexpected error has occurred!", "warning")
            else:
                flash('Account successfully updated!', 'success')

                return redirect('/adminProfile/' + session['username'])

    return render_template("adminProfile.html", currentPage="myProfile", **session, userData=userData,
                           recentPosts=recentPosts, admin=admin,
                           updateEmailForm=updateEmailForm, updateUsernameForm=updateUsernameForm,
                           updateStatusForm=updateStatusForm)


@app.route('/adminHome', methods=["GET", "POST"])
@custom_login_required
# @admin_permission.require()
def adminHome():
    if not session['isAdmin']:
        flash("You are not give access to view this. Please login.", "warning")
        return redirect(url_for('login'))
    elif session['isAdmin']:
        searchBarForm = Forms.SearchBarForm(request.form)
        searchBarForm.topic.choices = get_all_topics('all')
        if request.method == 'POST' and searchBarForm.validate():
            return redirect(
                url_for('searchPosts', searchQuery=searchBarForm.searchQuery.data, topic=searchBarForm.topic.data))

        sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username,topic.TopicID, topic.Content AS Topic FROM post"
        sql += " INNER JOIN user ON post.UserID=user.UserID"
        sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
        sql += " ORDER BY post.Upvotes-post.Downvotes DESC LIMIT 6"

        dictCursor.execute(sql)
        recentPosts = dictCursor.fetchall()
        for post in recentPosts:
            currentVote = DatabaseManager.get_user_post_vote(str(session.get('userID')), str(post['PostID']))
            if currentVote == None:
                post['UserVote'] = 0
            else:
                post['UserVote'] = currentVote['Vote']

            post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
            post['Content'] = post['Content'][:200]

    return render_template('adminHome.html', currentPage='adminHome', **session, searchBarForm=searchBarForm,
                           recentPosts=recentPosts)


@app.route('/adminViewPost/<int:postID>/', methods=["GET", "POST"])
@custom_login_required
def adminViewPost(postID):
    if not session['isAdmin']:
        flash("You are not give access to view this. Please login.", "warning")
        return redirect(url_for('login'))
    elif session['isAdmin']:
        sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted,post.TopicID,post.PostID, user.Username, topic.Content AS Topic FROM post"
        sql += " INNER JOIN user ON post.UserID=user.UserID"
        sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
        sql += " WHERE PostID=%s"
        val = (postID,)
        dictCursor.execute(sql, val)
        post = dictCursor.fetchone()
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']

        currentVote = DatabaseManager.get_user_post_vote(str(session.get('userID')), str(postID))
        if currentVote == None:
            post['UserVote'] = 0
        else:
            post['UserVote'] = currentVote['Vote']

        sql = "SELECT comment.CommentID, comment.Content, comment.DatetimePosted, comment.Upvotes, comment.Downvotes, comment.DatetimePosted, user.Username, comment.FileName  FROM comment"
        sql += " INNER JOIN user ON comment.UserID=user.UserID"
        sql += " WHERE comment.PostID=%s"
        val = (postID,)
        dictCursor.execute(sql, val)
        commentList = dictCursor.fetchall()
        for comment in commentList:
            comment['TotalVotes'] = comment['Upvotes'] - comment['Downvotes']

            currentVote = DatabaseManager.get_user_comment_vote(str(session.get('userID')), str(comment['CommentID']))
            if currentVote == None:
                comment['UserVote'] = 0
            else:
                comment['UserVote'] = currentVote['Vote']

            sql = "SELECT reply.Content, reply.DatetimePosted, reply.DatetimePosted, user.Username FROM reply"
            sql += " INNER JOIN user ON reply.UserID=user.UserID"
            sql += " WHERE reply.CommentID=" + str(comment['CommentID'])
            dictCursor.execute(sql)
            replyList = dictCursor.fetchall()
            comment['ReplyList'] = replyList

        commentForm = Forms.CommentForm(request.form)
        commentForm.userID.data = session.get('userID')
        replyForm = Forms.ReplyForm(request.form)
        replyForm.userID.data = session.get('userID')

        if request.method == 'POST' and commentForm.validate():
            file = request.files['file']
            path = os.path.abspath(os.getcwd())
            path = os.path.join(path, 'static', 'uploads')

            filename = secure_filename(file.filename)

            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(file.stream):
                    abort(404)
                else:
                    file.save(os.path.join(path, secure_filename(file.filename)))


            dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
            sql = 'INSERT INTO comment (PostID, UserID, Content, DateTimePosted, Upvotes, Downvotes, FileName) VALUES (%s, %s, %s, %s, %s, %s, %s)'
            val = (postID, commentForm.userID.data, commentForm.comment.data, dateTime, 0, 0, file.filename,)
            tupleCursor.execute(sql, val)
            db.commit()
            flash('Comment posted!', 'success')
            return redirect('/adminViewPost/%d' % (postID))

        if request.method == 'POST' and replyForm.validate():
            dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
            sql = 'INSERT INTO reply (UserID, CommentID, Content, DateTimePosted) VALUES (%s, %s, %s, %s)'
            val = (replyForm.userID.data, replyForm.repliedID.data, replyForm.reply.data, dateTime)
            tupleCursor.execute(sql, val)
            db.commit()
            flash('Comment posted!', 'success')
            return redirect('/adminViewPost/%d' % (postID))

    print(session.get('userID'))
    return render_template('adminViewPost.html', currentPage='adminViewPost', **session, post=post,
                           commentList=commentList, commentForm=commentForm, replyForm=replyForm)


@app.route('/adminTopics')
@custom_login_required
def adminTopics():
    if not session['isAdmin']:
        flash("You are not give access to view this. Please login.", "warning")
        return redirect(url_for('login'))
    elif session['isAdmin']:
        sql = "SELECT Content,TopicID FROM topic ORDER BY Content "
        tupleCursor.execute(sql)
        listOfTopics = tupleCursor.fetchall()
    return render_template('adminTopics.html', currentPage='adminTopics', **session, listOfTopics=listOfTopics)


@app.route('/adminIndivTopic/<topicID>', methods=["GET", "POST"])
@custom_login_required
def adminIndivTopic(topicID):
    if not session['isAdmin']:
        flash("You are not give access to view this. Please login.", "warning")
        return redirect(url_for('login'))
    elif session['isAdmin']:
        sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
        sql += " INNER JOIN user ON post.UserID=user.UserID"
        sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
        sql += " WHERE topic.TopicID = " + str(topicID)

        dictCursor.execute(sql)
        recentPosts = dictCursor.fetchall()

        for post in recentPosts:
            post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
            post['Content'] = post['Content'][:200]
        topic = "SELECT Content FROM topic WHERE topic.TopicID=%s"
        val = (topicID,)
        tupleCursor.execute(topic, val)
        topic = tupleCursor.fetchone()
    return render_template('adminIndivTopic.html', currentPage='adminIndivTopic', **session, recentPosts=recentPosts,
                           topic=topic[0])


@app.route('/addTopic', methods=["GET", "POST"])
@custom_login_required
def addTopic():

    sql = "SELECT Content FROM topic ORDER BY Content"

    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()

    topicForm = Forms.TopicForm(request.form)
    topicForm.topic.choices = listOfTopics
    if request.method=="GET":
        session['csrf_token']= base64.b64encode(os.urandom(16))

    if request.method == "POST" and topicForm.validate():
        print(topicForm.csrf_token.data) #technically we translate the bytes to literally string
        print(type(topicForm.csrf_token.data))
        print(session.get('csrf_token'))
        if topicForm.csrf_token.data!=str(session.get('csrf_token')):
            # print('enter')
            return redirect(url_for('login'))
    if request.method == 'POST' and topicForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO topic ( UserID, Content, DateTimePosted) VALUES ( %s,%s, %s)'
        val = (session["userID"], topicForm.topic.data, dateTime)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Topic successfully created!', 'success')
        return redirect('/adminHome')

    return render_template('addTopic.html', currentPage='addTopic', **session, topicForm=topicForm)


@app.route('/adminUsers')
@custom_login_required
def adminUsers():
    if not session['isAdmin']:
        flash("You are not give access to view this. Please login.", "warning")
        return redirect(url_for('login'))
    elif session['isAdmin']:
        sql = "SELECT Username From user"
        tupleCursor.execute(sql)
        listOfUsernames = tupleCursor.fetchall()
    return render_template('adminUsers.html', currentPage='adminUsers', **session, listOfUsernames=listOfUsernames)


@app.route('/adminDeleteUser/<username>', methods=['POST'])
@custom_login_required
def deleteUser(username):
    if not session['isAdmin']:
        flash("You are not give access to view this. Please login.", "warning")
        return redirect(url_for('login'))
    elif session['isAdmin']:
        user_email = "SELECT Email FROM user WHERE user.username=%s"
        val = (username,)
        tupleCursor.execute(user_email, val)
        sql = "DELETE FROM user WHERE user.username=%s"
        val = (username,)
        tupleCursor.execute(sql, val)
        db.commit()
        try:
            msg = Message("Lorem Ipsum",
                          sender=os.environ['MAIL_USERNAME'],
                          recipients=[user_email[0]])
            msg.body = "Your account has been terminated"
            msg.html = render_template('email.html', postID="delete user", username=username, content=0, posted=0)
            mail.send(msg)
        except Exception as e:
            print(e)
            print("Error:", sys.exc_info()[0])
            print("goes into except")

    return redirect('/adminUsers')


@app.route('/adminDeletePost/<postID>', methods=['POST', 'GET'])
@custom_login_required
def deletePost(postID):
    if not session['isAdmin']:
        flash("You are not give access to view this. Please login.", "warning")
        return redirect(url_for('login'))
    elif session['isAdmin']:
        sql = "SELECT post.Content, post.DatetimePosted, post.postID, user.Username, user.email "
        sql += "FROM post"
        sql += " INNER JOIN user ON post.UserID = user.UserID"
        sql += " WHERE post.PostID = %s"
        val = (postID,)
        dictCursor.execute(sql, val)
        email_info = dictCursor.fetchall()

        sql = "DELETE FROM post WHERE post.PostID=%s"
        val = (postID,)
        dictCursor.execute(sql, val)
        db.commit()

    return redirect('/adminHome')


@app.route('/adminFeedback')
@custom_login_required
def adminFeedback():
    if not session['isAdmin']:
        flash("You are not give access to view this. Please login.", "warning")
        return redirect(url_for('login'))
    elif session['isAdmin']:
        sql = "SELECT feedback.Content, feedback.DatetimePosted, feedback.Reason,feedback.FeedbackID, user.Username, user.Email "
        sql += "FROM feedback"
        sql += " INNER JOIN user ON feedback.UserID = user.UserID"
        sql += " WHERE feedback.Resolved = 0"
        dictCursor.execute(sql)
        feedbackList = dictCursor.fetchall()
    return render_template('adminFeedback.html', currentPage='adminFeedback', **session, feedbackList=feedbackList)


@app.route('/replyFeedback/<feedbackID>', methods=["GET", "POST"])
@custom_login_required
def replyFeedback(feedbackID):
    sql = "SELECT feedback.Content, feedback.DatetimePosted, feedback.Reason,feedback.FeedbackID, user.Username, user.Email "
    sql += "FROM feedback"
    sql += " INNER JOIN user ON feedback.UserID = user.UserID"
    sql += " WHERE feedback.FeedbackID = %s"
    # sql += " AND feedback.Resolved = 0"
    val = (str(feedbackID),)
    dictCursor.execute(sql, val)
    feedbackList = dictCursor.fetchall()
    replyForm = Forms.ReplyFeedbackForm(request.form)
    # uncomment here
    if request.method == 'POST' and replyForm.validate():
        reply = replyForm.reply.data
        email = feedbackList[0]['Email']
        try:
            msg = Message("Lorem Ipsum",
                          sender=os.environ['MAIL_USERNAME'],
                          recipients=[email])
            msg.body = "We love your feedback!"
            msg.html = render_template('email.html', postID="feedback reply", username=feedbackList[0]['Username'],
                                       content=feedbackList[0]['Content'], posted=feedbackList[0]['DatetimePosted'],
                                       reply=reply)
            mail.send(msg)

        except Exception as e:
            print(e)
            print("Error:", sys.exc_info()[0])
            print("goes into except")
        sql = "UPDATE feedback "
        sql += " SET Resolved=1"
        sql += " WHERE FeedbackID = %s"
        val = (str(feedbackID),)
        tupleCursor.execute(sql, val)
        db.commit()
        return redirect('/adminFeedback')
    return render_template('replyFeedback.html', currentPage='replyFeedback', **session, replyForm=replyForm,
                           feedbackList=feedbackList)

@app.route('/replyFeedback/<feedbackID>', methods=["GET", "POST"])
@custom_login_required
def logfilesviewing():
    pass

# may not need this but i leave it here if ur need error 404
@app.errorhandler(404)
def error404(e):
    msg = 'Oops! Page not found. Head back to the home page'
    title = 'Error 404'
    # admin = session['isAdmin']
    return render_template('error.html', msg=msg, title=title)


@app.errorhandler(500)
def error500(e):
    msg = 'Oops! We seem to have encountered an error. Head back to the home page :)'
    title = 'Error 500'
    return render_template('error.html', msg=msg, title=title)

if __name__ == "__main__":
    app.run(debug=True,ssl_context='adhoc')
