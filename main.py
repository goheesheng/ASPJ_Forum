from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, \
    send_from_directory, session, get_flashed_messages, abort
from flask_talisman import Talisman
import mysql.connector, re, random
import Forms
from datetime import datetime, timedelta  # for session timeout
# Flask mail
import os
import base64
import secrets  # for the otp token
from flask_mail import Mail, Message
import sys
import asyncio
from threading import Thread
import DatabaseManager
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin

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

app = Flask(__name__)
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
        'http://127.0.0.1:5000/templates/home.html'
        # 'http://127.0.0.1:5000/static/scripts/post-votes.js',
        # 'http://127.0.0.1:5000/static/bootstrap-4.3.1-dist/js/bootstrap.js',
        # 'http://127.0.0.1:5000/static/bootstrap-4.3.1-dist/js/bootstrap.min.js',
        # 'http://127.0.0.1:5000/static/bootstrap-4.3.1-dist/jquery-3.4.1.min.js'

    ]

}
talisman = Talisman(app, content_security_policy=csp, content_security_policy_nonce_in=['script-src'])
# # define flask-login configuration
# login_mgr = LoginManager()
# login_mgr.init_app(app)     # app is a flask object
# login_mgr.login_view = 'login'
# login_mgr.refresh_view = 'relogin'
# # login_mgr.needs_refresh_message = (u"Session timeout, please re-login")
# # login_mgr.needs_refresh_message_category = "info"

app.config.from_object(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '.login'

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
    UPLOAD_FOLDER="templates\Files"
)
cursor = db.cursor()

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
mail = Mail(app)


# app.permanent_session_lifetime = timedelta(seconds=5)
# # if 'Session timeout, please re-login.' not in get_flashed_messages() and (request.referrer != request.base_url+"/login?next=%2Flogout" or '/static/' not in request.path):
# #     print("entered")
# # flash('Session timeout, please re-login.','warning')

@login_manager.user_loader
def load_user(UserID):
    # sql = "SELECT UserID from user"
    # val = (UserID,)
    # dictCursor.excute(sql, val)
    # userData = dictCursor.fetchone()

    return User(UserID)  # fetch from the database


class User(UserMixin):
    def __init__(self, id):
        self.id = id


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


@app.route('/postVote', methods=["GET", "POST"])
def postVote():
    if not session['login']:
        flash('You must be logged in to vote.', 'warning')
        return make_response(jsonify({'message': 'Please log in to vote.'}), 401)

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


@app.route('/commentVote', methods=["GET", "POST"])
def commentVote():
    if not session['login']:
        flash('You must be logged in to vote.', 'warning')
        return make_response(jsonify({'message': 'Please log in to vote.'}), 401)

    data = request.get_json(force=True)
    print(data)
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
    # to check if the user exist or not
    # if not session.get("userID"):
    # if not there in the session then redirect to login page
    # return redirect("/home")
    # return render_template('home.html')
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
    print(session)
    searchBarForm = Forms.SearchBarForm(request.form)
    searchBarForm.topic.choices = get_all_topics('all')
    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and searchBarForm.validate():
        print(searchBarForm.csrf_token.data)  # technically we translate the bytes to literally string
        print(type(searchBarForm.csrf_token.data))
        print(session['csrf_token'])
        if searchBarForm.csrf_token.data != str((session['csrf_token'])):
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
    return render_template('home.html', currentPage='home', **session, searchBarForm=searchBarForm,
                           recentPosts=recentPosts)


@app.route('/searchPosts', methods=["GET", "POST"])
def searchPosts():
    session['prevPage'] = request.headers.get("Referer")

    searchBarForm = Forms.SearchBarForm(request.form)
    searchBarForm.topic.choices = get_all_topics('all')

    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and searchBarForm.validate():
        print(searchBarForm.csrf_token.data)  # technically we translate the bytes to literally string
        print(type(searchBarForm.csrf_token.data))
        print(session['csrf_token'])
        if searchBarForm.csrf_token.data != str((session['csrf_token'])):
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
        print(session['csrf_token'])
        if commentForm.csrf_token.data != str((session['csrf_token'])):
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


@app.route('/addPost', methods=["GET", "POST"])
def addPost():
    sql = "SELECT TopicID, Content FROM topic ORDER BY Content"
    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()

    postForm = Forms.PostForm(request.form)
    postForm.topic.choices = get_all_topics('default')
    postForm.userID.data = session.get('userID')
    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and postForm.validate():
        print(postForm.csrf_token.data)  # technically we translate the bytes to literally string
        print(type(postForm.csrf_token.data))
        print(session['csrf_token'])
        if postForm.csrf_token.data != str((session['csrf_token'])):
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


@app.route('/feedback', methods=["GET", "POST"])
def feedback():
    feedbackForm = Forms.FeedbackForm(request.form)
    feedbackForm.userID.data = session.get('userID')
    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and feedbackForm.validate():
        print(feedbackForm.csrf_token.data)  # technically we translate the bytes to literally string
        print(type(feedbackForm.csrf_token.data))
        print(session['csrf_token'])
        if feedbackForm.csrf_token.data != str((session['csrf_token'])):
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


@app.route('/login', methods=["GET", "POST"])
def login():
    # # setting session timeout
    # session.permanent = True
    # app.permanent_session_lifetime = timedelta(minutes=1)
    # if form is submitted
    loginForm = Forms.LoginForm(request.form)

    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and loginForm.validate():
        print(loginForm.csrf_token.data)  # technically we translate the bytes to literally string
        print(type(loginForm.csrf_token.data))
        print(session['csrf_token'])
        if loginForm.csrf_token.data != str((session['csrf_token'])):
            # print('enter')
            return redirect(url_for('login'))

        sql = "SELECT UserID, Email, Username, Password FROM user WHERE Username = %s"
        val = (loginForm.username.data,)
        dictCursor.execute(sql, val)
        findUser = dictCursor.fetchone()
        if findUser == None:
            loginForm.password.errors.append('Wrong username or password.')
            tries.add_tries(1)

        elif loginForm.password.data != findUser["Password"]:

            loginForm.password.errors.append('Wrong username or password.')
            tries.add_tries(1)

        else:
            tries.reset_tries()
            # flask session timeout
            user = User(findUser['UserID'])
            login_user(user)

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
            if findAdmin != None:
                session['isAdmin'] = True
                return redirect('/adminHome')
            else:
                session['isAdmin'] = False
                return redirect('/home')

        render_template("login.html", loginForm=loginForm, tries=tries)
    return render_template("login.html", loginForm=loginForm, tries=tries)


@app.route('/logout')
@login_required  # flask session timeout
def logout():
    logout_user()
    # timed_out = request.args.get('timeout')
    # if request.args.get('timeout'):
    #     flash('Session timeout, please re-login.', 'warning')
    session["name"] = None
    session['login'] = False
    session['userID'] = 0
    session['username'] = ''
    return redirect("/home")
    # return render_template('home.html', timed_out=timed_out)


# flask_wtf is shit
# sign up final stage
@app.route('/login/<link>', methods=["GET", "POST"])
def otp(link):
    global temp_signup
    otpform = Forms.OTPForm(request.form)
    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and otpform.validate():
        print(otpform.csrf_token.data)  # technically we translate the bytes to literally string
        print(type(otpform.csrf_token.data))
        print(session['csrf_token'])
        if otpform.csrf_token.data != str((session['csrf_token'])):
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
    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and signUpForm.validate():
        print(signUpForm.csrf_token.data)  # technically we translate the bytes to literally string
        print(type(signUpForm.csrf_token.data))
        print(session['csrf_token'])
        if signUpForm.csrf_token.data != str((session['csrf_token'])):
            # print('enter')
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
        sql = "INSERT INTO otp (link, otp) VALUES (%s, %s)"
        val = (link, str(OTP))
        tupleCursor.execute(sql, val)
        db.commit()
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
def profile(username):
    updateEmailForm = Forms.UpdateEmail(request.form)
    updateUsernameForm = Forms.UpdateUsername(request.form)
    updateStatusForm = Forms.UpdateStatus(request.form)
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
            tupleCursor.execute(sql, val, )
            db.commit()

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

    return render_template("profile.html", currentPage="myProfile", **session, userData=userData,
                           recentPosts=recentPosts,
                           updateEmailForm=updateEmailForm, updateUsernameForm=updateUsernameForm,
                           updateStatusForm=updateStatusForm)


user_to_url = {}


@app.route('/changePassword/<username>', methods=["GET"])
def changePassword(username):
    global user_to_url
    url = secrets.token_urlsafe()
    sql = "INSERT INTO password_url(Url) VALUES(%s)"
    val = (url,)
    tupleCursor.execute(sql, val)
    db.commit()
    user_to_url[url] = username
    user_email = "SELECT Email FROM user WHERE user.username=%s"
    val = (username,)
    tupleCursor.execute(user_email, val)
    user_email = tupleCursor.fetchone()
    abs_url = "http://127.0.0.1:5000/reset/" + url
    try:
        msg = Message("ASPJ Forum",
                      sender=os.environ['MAIL_USERNAME'],
                      recipients=[user_email[0]])
        msg.body = "Password Change"
        msg.html = render_template('email.html', postID="change password", username=username, content=0, posted=0,
                                   url=abs_url)
        mail.send(msg)
    except Exception as e:
        print(e)
        print("Error:", sys.exc_info()[0])
        print("goes into except")
    else:
        flash('A change password link has been sent to your email. Use it to update your password.', 'success')
        flash('The password link will expire in 10 mins', 'warning')
        if session['isAdmin']:
            return redirect('/adminProfile/' + str(username))
        else:
            return redirect('/profile/' + str(username))


@app.route('/reset/<url>', methods=["GET", "POST"])
def resetPassword(url):
    global user_to_url
    sql = "SELECT TIME_TO_SEC(TIMEDIFF(%s, Time_Created)) FROM password_url WHERE Url = %s"
    val = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), url)
    tupleCursor.execute(sql, val)
    reset = tupleCursor.fetchone()
    if reset[0] > 600:
        sql = "DELETE FROM password_url WHERE Url = %s"
        val = (url,)
        flash("Your password reset link has expired, please try again!", "danger")
        return redirect("/home")
    else:
        changePasswordForm = Forms.UpdatePassword(request.form)
        if request.method == "POST" and changePasswordForm.validate():
            username = user_to_url[url]
            password = changePasswordForm.password.data
            sql = "UPDATE user SET Password=%s WHERE Username=%s"
            val = (str(password), username)
            tupleCursor.execute(sql, val)
            db.commit()
            user_to_url.pop(url)
            flash("Password has been successfully reset", 'success')
            return redirect("/login")
        return render_template("changePassword.html", changePasswordForm=changePasswordForm)


@app.route('/topics')
def topics():
    sql = "SELECT Content,TopicID FROM topic ORDER BY Content "
    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()

    return render_template('topics.html', currentPage='topics', **session, listOfTopics=listOfTopics)


@app.route('/indivTopic/<topicID>', methods=["GET", "POST"])
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
def adminUserProfile(username):
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
def adminHome():
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
def adminViewPost(postID):
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
        sql += " WHERE reply.CommentID=" + str(comment['CommentID'])
        dictCursor.execute(sql)
        replyList = dictCursor.fetchall()
        comment['ReplyList'] = replyList

    commentForm = Forms.CommentForm(request.form)
    commentForm.userID.data = session.get('userID')
    replyForm = Forms.ReplyForm(request.form)
    replyForm.userID.data = session.get('userID')

    if request.method == 'POST' and commentForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO comment (PostID, UserID, Content, DateTimePosted, Upvotes, Downvotes) VALUES (%s, %s, %s, %s, %s, %s)'
        val = (postID, commentForm.userID.data, commentForm.comment.data, dateTime, 0, 0)
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
def adminTopics():
    sql = "SELECT Content,TopicID FROM topic ORDER BY Content "
    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()
    return render_template('adminTopics.html', currentPage='adminTopics', **session, listOfTopics=listOfTopics)


@app.route('/adminIndivTopic/<topicID>', methods=["GET", "POST"])
def adminIndivTopic(topicID):
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
def addTopic():
    if not session['login']:
        return redirect('/login')

    sql = "SELECT Content FROM topic ORDER BY Content"

    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()

    topicForm = Forms.TopicForm(request.form)
    topicForm.topic.choices = listOfTopics
    if request.method == "GET":
        session['csrf_token'] = base64.b64encode(os.urandom(16))

    if request.method == "POST" and topicForm.validate():
        print(topicForm.csrf_token.data)  # technically we translate the bytes to literally string
        print(type(topicForm.csrf_token.data))
        print(session['csrf_token'])
        if topicForm.csrf_token.data != str((session['csrf_token'])):
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
def adminUsers():
    sql = "SELECT Username From user"
    tupleCursor.execute(sql)
    listOfUsernames = tupleCursor.fetchall()
    return render_template('adminUsers.html', currentPage='adminUsers', **session, listOfUsernames=listOfUsernames)


@app.route('/adminDeleteUser/<username>', methods=['POST'])
def deleteUser(username):
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
def deletePost(postID):
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
def adminFeedback():
    sql = "SELECT feedback.Content, feedback.DatetimePosted, feedback.Reason,feedback.FeedbackID, user.Username, user.Email "
    sql += "FROM feedback"
    sql += " INNER JOIN user ON feedback.UserID = user.UserID"
    sql += " WHERE feedback.Resolved = 0"
    dictCursor.execute(sql)
    feedbackList = dictCursor.fetchall()
    return render_template('adminFeedback.html', currentPage='adminFeedback', **session, feedbackList=feedbackList)


@app.route('/replyFeedback/<feedbackID>', methods=["GET", "POST"])
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


# flask session timeout
@app.before_request
def make_session_permanent():
    session_modified = True
    session_permanent = True
    app.permanent_session_lifetime = timedelta(seconds=3000)
    # flash('Session timeout, please re-login.', 'warning')     # flashing too many times


# may not need this but i leave it here if ur need error 404
@app.errorhandler(404)
def error404(e):
    msg = 'Oops! Page not found. Head back to the home page'
    title = 'Error 404'
    admin = session['isAdmin']
    return render_template('error.html', msg=msg, admin=admin, title=title)


# @app.errorhandler(500)
# def error500(e):
#     msg = 'Oops! We seem to have encountered an error. Head back to the home page :)'
#     createLog.log_error(request.path, 500, 'Internal Server Error')
#     title = 'Error 500'
#     admin = sessionInfo["isAdmin"]
#     return render_template('error.html', msg=msg, admin=admin, title=title)

if __name__ == "__main__":
    app.run(debug=True)
