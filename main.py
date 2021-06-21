from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, send_from_directory
import mysql.connector, re, random
import Forms
from datetime import datetime
# Flask mail
import os
import secrets #for the otp token
from flask_mail import Mail, Message
import sys
import asyncio
from threading import Thread
import DatabaseManager
#testcommit

#Do set this
# os.environ['DB_USERNAME'] = 'ASPJuser'
# os.environ['DB_PASSWORD'] = 'P@55w0rD'
#
# print(os.environ['DB_USERNAME'])
# print(os.environ.['DB_PASSWORD'])
# os.environ['DB_USERNAME'] = 'ASPJuser'
# os.environ['DB_PASSWORD'] = 'P@55w0rD'

db = mysql.connector.connect(
    host="localhost",
    user= os.environ['DB_USERNAME'], #do not want to leak the db username
    password= os.environ['DB_PASSWORD'], #do not want to leak the db password
    database="mydatabase"
)

tupleCursor = db.cursor(buffered=True)
dictCursor = db.cursor(buffered=True, dictionary=True)
tupleCursor.execute("SHOW TABLES")
print(tupleCursor)

app = Flask(__name__)
#Do set this, go discord and follow instructions
# os.environ['MAIL_USERNAME'] = 'appdevescip2003@gmail.com'
# os.environ['MAIL_PASSWORD'] = 'appdev7181'
#
# print(os.environ['MAIL_USERNAME'])
# print(os.environ['MAIL_PASSWORD'])


app.config.update(
    MAIL_SERVER= 'smtp.gmail.com',
    MAIL_PORT= 587,
    MAIL_USE_TLS= True,
    MAIL_USE_SSL= False,
	MAIL_USERNAME = os.environ['DB_USERNAME'],#do not want to leak the mail username
	MAIL_PASSWORD = os.environ["DB_PASSWORD"],#do not want to leak the mail password
	MAIL_DEBUG = True,
	MAIL_SUPPRESS_SEND = False,
    MAIL_ASCII_ATTACHMENTS = True,
    # Directory for admins to refer files (Files) #inside has session logs
    UPLOAD_FOLDER = "templates\Files"
	)
cursor = db.cursor()

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
mail = Mail(app)
""" For testing purposes only. To make it convenient cause I can't remember all the account names.
Uncomment the account that you would like to use. To run the program as not logged in, run the first one."""

global sessionID
sessionID = 0
sessions={}
sessionInfo = {'login': False, 'currentUserID': 0, 'username': '', 'isAdmin': 0}

sessionID += 1
sessionInfo['sessionID'] = sessionID #set the session id
sessions[sessionID] = sessionInfo #store the session id

def get_all_topics(option):
    sql = "SELECT TopicID, Content FROM topic ORDER BY Content"
    dictCursor.execute(sql)
    listOfTopics = dictCursor.fetchall()
    topicTuples = []
    for topic in listOfTopics:
        topicTuples.append((str(topic['TopicID']), topic['Content']))

    if option=='all':
        topicTuples.insert(0, ('0', 'All Topics'))
    return topicTuples

@app.route('/postVote', methods=["GET", "POST"])
def postVote():
    if not sessionInfo['login']:
        flash('You must be logged in to vote.', 'warning')
        return make_response(jsonify({'message': 'Please log in to vote.'}), 401)

    data = request.get_json(force=True)
    currentVote = DatabaseManager.get_user_post_vote(str(sessionInfo['currentUserID']), data['postID'])

    if currentVote==None:
        if data['voteValue']=='1':
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

        DatabaseManager.insert_post_vote(str(sessionInfo['currentUserID']), data['postID'], data['voteValue'])

    else: # If vote for post exists
        if currentVote['Vote']==1:
            upvoteChange = '-1'
            if data['voteValue']=='1':
                toggleUpvote = True
                toggleDownvote = False
                newVote = 0
                downvoteChange = '0'
            else:
                toggleUpvote = True
                toggleDownvote = True
                newVote = -1
                downvoteChange = '+1'

        else: # currentVote['Vote']==-1
            downvoteChange = '-1'
            if data['voteValue']=='1':
                toggleUpvote = True
                toggleDownvote = True
                newVote = 1
                upvoteChange = '+1'
            else:
                toggleUpvote = False
                toggleDownvote = True
                newVote = 0
                upvoteChange = '0'

        if newVote==0:
            DatabaseManager.delete_post_vote(str(sessionInfo['currentUserID']), data['postID'])
        else:
            DatabaseManager.update_post_vote(str(newVote), str(sessionInfo['currentUserID']), data['postID'])

    DatabaseManager.update_overall_post_vote(upvoteChange, downvoteChange, data['postID'])
    updatedVoteTotal = DatabaseManager.calculate_updated_post_votes(data['postID'])
    return make_response(jsonify({'toggleUpvote': toggleUpvote, 'toggleDownvote': toggleDownvote
    , 'newVote': newVote, 'updatedVoteTotal': updatedVoteTotal, 'postID': data['postID']}), 200)

@app.route('/commentVote', methods=["GET", "POST"])
def commentVote():
    if not sessionInfo['login']:
        flash('You must be logged in to vote.', 'warning')
        return make_response(jsonify({'message': 'Please log in to vote.'}), 401)

    data = request.get_json(force=True)
    print(data)
    currentVote = DatabaseManager.get_user_comment_vote(str(sessionInfo['currentUserID']), data['commentID'])

    if currentVote==None:
        if data['voteValue']=='1':
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

        DatabaseManager.insert_comment_vote(str(sessionInfo['currentUserID']), data['commentID'], data['voteValue'])

    else: # If vote for post exists
        if currentVote['Vote']==1:
            upvoteChange = '-1'
            if data['voteValue']=='1':
                toggleUpvote = True
                toggleDownvote = False
                newVote = 0
                downvoteChange = '0'
            else:
                toggleUpvote = True
                toggleDownvote = True
                newVote = -1
                downvoteChange = '+1'

        else: # currentVote['Vote']==-1
            downvoteChange = '-1'
            if data['voteValue']=='1':
                toggleUpvote = True
                toggleDownvote = True
                newVote = 1
                upvoteChange = '+1'
            else:
                toggleUpvote = False
                toggleDownvote = True
                newVote = 0
                upvoteChange = '0'

        if newVote==0:
            DatabaseManager.delete_comment_vote(str(sessionInfo['currentUserID']), data['commentID'])
        else:
            DatabaseManager.update_comment_vote(str(newVote), str(sessionInfo['currentUserID']), data['commentID'])

    DatabaseManager.update_overall_comment_vote(upvoteChange, downvoteChange, data['commentID'])
    updatedCommentTotal = DatabaseManager.calculate_updated_comment_votes(data['commentID'])
    return make_response(jsonify({'toggleUpvote': toggleUpvote, 'toggleDownvote': toggleDownvote
    , 'newVote': newVote, 'updatedCommentTotal': updatedCommentTotal, 'commentID': data['commentID']}), 200)

@app.route('/')
def main():
    return redirect("/home")

@app.route('/home', methods=["GET", "POST"])
def home():
    searchBarForm = Forms.SearchBarForm(request.form)
    searchBarForm.topic.choices = get_all_topics('all')
    if request.method == 'POST' and searchBarForm.validate():
        return redirect(url_for('searchPosts', searchQuery = searchBarForm.searchQuery.data, topic = searchBarForm.topic.data))

    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, post.TopicID, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " ORDER BY post.PostID DESC LIMIT 6"

    dictCursor.execute(sql)
    recentPosts = dictCursor.fetchall()
    for post in recentPosts:
        if sessionInfo['login']:
            currentVote = DatabaseManager.get_user_post_vote(str(sessionInfo['currentUserID']), str(post['PostID']))
            if currentVote==None:
                post['UserVote'] = 0
            else:
                post['UserVote'] = currentVote['Vote']
        else:
            post['UserVote'] = 0
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        post['Content'] = post['Content'][:200]
    return render_template('home.html', currentPage='home', **sessionInfo, searchBarForm = searchBarForm, recentPosts = recentPosts)

@app.route('/searchPosts', methods=["GET", "POST"])
def searchPosts():
    sessionInfo['prevPage']= request.url_rule
    searchBarForm = Forms.SearchBarForm(request.form)
    searchBarForm.topic.choices = get_all_topics('all')
    if request.method == 'POST' and searchBarForm.validate():
        return redirect(url_for('searchPosts', searchQuery = searchBarForm.searchQuery.data, topic = searchBarForm.topic.data))

    searchQuery = request.args.get('searchQuery', default='')
    searchBarForm.searchQuery.data = searchQuery

    searchTopic = request.args.get('topic', default='0')
    searchBarForm.topic.data = int(searchTopic)

    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " WHERE post.Title LIKE %s"

    searchQuery = "%" + searchQuery + "%"

    if searchTopic!='0':
        sql += " AND topic.TopicID = %s" #if there is a topic
        val = (searchQuery, searchTopic)
    else:
        val = (searchQuery,) # escape values (Almost forgetten about this), It is crucial.

    dictCursor.execute(sql, val)
    relatedPosts = dictCursor.fetchall()
    for post in relatedPosts:
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        post['Content'] = post['Content'][:200]

    return render_template('searchPost.html', currentPage='search', **sessionInfo, searchBarForm=searchBarForm, postList=relatedPosts)

@app.route('/viewPost/<int:postID>/', methods=["GET", "POST"])
def viewPost(postID):
    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID = user.UserID"
    sql += " INNER JOIN topic ON post.TopicID = topic.TopicID"
    sql += " WHERE PostID = %s"
    val = (postID,)
    dictCursor.execute(sql, val)
    post = dictCursor.fetchone()
    post['TotalVotes'] = post['Upvotes'] - post['Downvotes']

    currentVote = DatabaseManager.get_user_post_vote(str(sessionInfo['currentUserID']), str(postID))
    if currentVote==None:
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

        currentVote = DatabaseManager.get_user_comment_vote(str(sessionInfo['currentUserID']), str(comment['CommentID']))
        if currentVote==None:
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
    commentForm.userID.data = sessionInfo['currentUserID']
    replyForm = Forms.ReplyForm(request.form)
    replyForm.userID.data = sessionInfo['currentUserID']

    if request.method == 'POST' and commentForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO comment (PostID, UserID, Content, DateTimePosted, Upvotes, Downvotes) VALUES (%s, %s, %s, %s, %s, %s)'
        val = (postID, commentForm.userID.data, commentForm.comment.data, dateTime, 0, 0)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Comment posted!', 'success')
        return redirect('/viewPost/%d/%d' %(postID,sessionInfo['sessionID']))

    if request.method == 'POST' and replyForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO reply (UserID, CommentID, Content, DateTimePosted) VALUES (%s, %s, %s, %s)'
        val = (replyForm.userID.data, replyForm.repliedID.data, replyForm.reply.data, dateTime)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Comment posted!', 'success')
        return redirect('/viewPost/%d/%d' %(postID, sessionInfo['sessionID']))

    return render_template('viewPost.html', currentPage='viewPost', **sessionInfo, commentForm = commentForm, replyForm = replyForm, post = post, commentList = commentList)

@app.route('/addPost', methods=["GET", "POST"])
def addPost():
    sql = "SELECT TopicID, Content FROM topic ORDER BY Content"
    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()

    postForm = Forms.PostForm(request.form)
    postForm.topic.choices = get_all_topics('default')
    postForm.userID.data = sessionInfo['currentUserID']

    if request.method == 'POST' and postForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO post (TopicID, UserID, DateTimePosted, Title, Content, Upvotes, Downvotes) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        val = (postForm.topic.data, postForm.userID.data, dateTime, postForm.title.data, postForm.content.data, 0, 0)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Post successfully created!', 'success')
        return redirect('/home')

    return render_template('addPost.html', currentPage='addPost', **sessionInfo, postForm=postForm)

@app.route('/feedback', methods=["GET", "POST"])
def feedback():
    feedbackForm = Forms.FeedbackForm(request.form)
    feedbackForm.userID.data = sessionInfo['currentUserID']

    if request.method == 'POST' and feedbackForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO feedback (UserID, Reason, Content, DateTimePosted, Resolved) VALUES (%s, %s, %s, %s, %s)'
        val = (feedbackForm.userID.data, feedbackForm.reason.data, feedbackForm.comment.data, dateTime, 0)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Feedback sent!', 'success')
        return redirect('/feedback/%d' %sessionInfo['sessionID'])

    return render_template('feedback.html', currentPage='feedback', **sessionInfo, feedbackForm = feedbackForm)

@app.route('/login', methods=["GET", "POST"])
def login():
    loginForm = Forms.LoginForm(request.form)
    global sessionID
    if request.method == 'POST' and loginForm.validate():
        sql = "SELECT UserID, Username, Password, Active, LoginAttempts, Email FROM user WHERE Username = %s"
        val = (loginForm.username.data,)
        dictCursor.execute(sql, val)
        findUser = dictCursor.fetchone()
        if findUser==None:
            loginForm.password.errors.append('Wrong username or password.')

        else:
            sessionInfo['login'] = True
            sessionInfo['currentUserID'] = int(findUser['UserID']) #set to int for the app.route<int:id>
            sessionInfo['username'] = findUser['Username']
            sessionID += 1
            sessionInfo['sessionID'] = sessionID
            sessions[sessionID] = sessionInfo
            sql = "SELECT * FROM admin WHERE UserID=%s"
            val = (int(findUser['UserID']),)
            dictCursor.execute(sql, val)
            findAdmin = dictCursor.fetchone()
            sql = "UPDATE user SET LoginAttempts = %s WHERE Username = %s"
            val = (str(0), findUser['Username'])
            tupleCursor.execute(sql, val)
            db.commit()
            flash('Welcome! You are now logged in as %s.' %(sessionInfo['username']), 'success')
            if findAdmin != None:
                sessionInfo['isAdmin'] = True
                return redirect('/adminHome')
            else:
                sessionInfo['isAdmin'] = False

            return redirect('/home') # Change this later to redirect to profile page

    return render_template('login.html', currentPage='login', **sessionInfo, loginForm = loginForm)

@app.route('/logout')
def logout():
    global sessionID
    sessionInfo = sessions[sessionID]
    sessionInfo['login'] = False
    sessionInfo['currentUserID'] = 0
    sessionInfo['username'] = ''
    sessions.pop(sessionID)
    return redirect('/home')

#sign up final stage
@app.route('/login/<link>', methods=["GET", "POST"])
def otp(link):
    global sessionID
    global temp_signup
    otpform = Forms.OTPForm(request.form)
    sql = "SELECT otp, TIME_TO_SEC(TIMEDIFF(%s, Time_Created)) from otp WHERE link = %s" # set timer for opt 3 mins, time_created was created in db schema
    val = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), link) # retrieve current time
    tupleCursor.execute(sql, val)
    otp = tupleCursor.fetchone()
    print(val)
    print(otp,'otoptuple')
    if otp is None:
        abort(404)
    if request.method == "POST" and otpform.validate():
        if otp[1] > 180:
            flash('Your OTP has expired. Please resubmit the signup form','danger')
            sql = "DELETE from otp WHERE link =%s"
            val = (link,)
            tupleCursor.execute(sql,val)
            temp_signup.pop(link)
            db.commit()
            return redirect('/signup')
        temp_details = temp_signup[link]
        print(otp[1],otp[0],otp,'otp')
        if str(otp[0]) == otpform.otp.data:
            # try:
            sql = "INSERT INTO user (Email, Username, Birthday, Password) VALUES (%s, %s, %s, %s)"
            val = (temp_details["Email"], temp_details["Username"], temp_details["Birthday"], temp_details["Password"]) # insert the data only after OTP is successful
            tupleCursor.execute(sql, val)
            db.commit()
        #
        # except mysql.connector.errors.IntegrityError as errorMsg: #Prevent Error-based sql injection
        #     errorMsg = str(errorMsg)
        #     print('error here')
        #     if 'email' in errorMsg.lower():
        #         otpform.otp.errors.append('The email has already been linked to another account. Please use a different email.')
        #     elif 'username' in errorMsg.lower():
        #         otpform.otp.errors.append('This username is already taken.')

        # else:

            temp_signup.pop(link)
            sql = "DELETE from otp WHERE link =%s" #ensure otp with same link wont be exploited
            val = (link,)
            tupleCursor.execute(sql,val)
            db.commit()
            sql = "SELECT UserID, Username FROM user WHERE Username=%s AND Password=%s"
            val = (temp_details["Username"], temp_details["Password"])
            tupleCursor.execute(sql, val)
            findUser = tupleCursor.fetchone()
            sessionInfo['login'] = True
            sessionInfo['currentUserID'] = int(findUser[0])
            sessionInfo['username'] = findUser[1]
            sessionID += 1
            sessionInfo['sessionID'] = sessionID
            sessions[sessionID] = sessionInfo
            flash('Account successfully created! You are now logged in as %s.' %(sessionInfo['username']), 'success')
            return redirect('/home')

        elif temp_details["Resend count"] < 3: #if wrong password, resend otp again of which i do not want, not fixed pls fix
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
            flash("You have failed OTP too many times. Please recheck your details before you submit the sign up form!", 'danger')
            return redirect("/signup")

    return render_template('otp.html', otpform = otpform)
temp_signup = {}
@app.route('/signup', methods=["GET", "POST"])
def signUp():
    global temp_signup
    signUpForm = Forms.SignUpForm(request.form)
    otpform = Forms.OTPForm(request.form)
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
                    sender= os.environ.get('MAIL_USERNAME'),
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

    return render_template('signup.html', currentPage='signUp', **sessionInfo, signUpForm = signUpForm)

@app.route('/profile/<username>', methods=["GET", "POST"])
def profile(username):
    # global sessionID
    sessionInfo = sessions[sessionID]
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
    if userData['Status'] == None:
        userData['Status'] = userData['Username'] + " is too lazy to add a status"
    for post in recentPosts:
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        userData['Credibility'] += post['TotalVotes']
        post['Content'] = post['Content'][:200]

    if request.method == "POST" and updateEmailForm.validate():
        sql = "UPDATE user "
        sql += "SET Email = %s"
        sql += "WHERE UserID = %s"
        try:
            val = (updateEmailForm.email.data, str(sessionInfo["currentUserID"]))
            tupleCursor.execute(sql, val)
            db.commit()

        except mysql.connector.errors.IntegrityError as errorMsg: # Prevent error-based sql attack
            errorMsg = str(errorMsg)
            if 'email' in errorMsg.lower():
                updateEmailForm.email.errors.append('The email has already been linked to another account. Please use a different email.')
                flash("This email has already been linked to another account. Please use a different email.", "success")
        else:
            try:
                msg = Message("ASPJ Forum",
                    sender = os.environ['MAIL_USERNAME'],
                    recipients = [userData["Email"]])
                msg.body = "Profile Update"
                msg.html = render_template('update_email.html', value="Email", url="http://127.0.0.1:5000/changePassword/" + userData["Username"], username=userData["Username"])
                mail.send(msg)
            except Exception as e:
                print(e)
                print("Error:", sys.exc_info()[0])
                print("goes into except")
            else:
                flash('Account successfully updated!', 'success')

                return redirect('/profile/' + sessionInfo['username'] + '/' +str(sessionID))

    if request.method == "POST" and updateUsernameForm.validate():
        sql = "UPDATE user "
        sql += "SET Username=%s"
        sql += "WHERE UserID=%s"
        try:
            val = (updateUsernameForm.username.data, str(sessionInfo["currentUserID"]))
            tupleCursor.execute(sql, val)
            db.commit()

        except mysql.connector.errors.IntegrityError as errorMsg: # Prevent error-based sql attack
            errorMsg = str(errorMsg)
            if 'username' in errorMsg.lower():
                flash("This username is already taken!", "success")
                updateUsernameForm.username.errors.append('This username is already taken.')
        else:
            sql = "SELECT Username WHERE UserID=%s"
            val = (str(sessionInfo["currentUserID"]),)
            dictCursor.execute(sql, val)
            db.commit()
            sessionInfo['username'] = dictCursor['Username']
            sessions[sessionID] = sessionInfo
            try:
                msg = Message("Lorem Ipsum",
                    sender= os.environ['MAIL_USERNAME'],
                    recipients=[userData["Email"]])
                msg.body = "Profile Update"
                msg.html = render_template('update_email.html', value="Username", url="http://127.0.0.1:5000/changePassword/" + userData["Username"], username=userData["Username"])
                mail.send(msg)
            except Exception as e:
                print(e)
                print("Error:", sys.exc_info()[0])
                print("goes into except")
            else:
                flash('Account successfully updated! Your username now is %s.' %(sessionInfo['username']), 'success')
                return redirect('/profile/' + sessionInfo['username'] + '/' +str(sessionID))

    return render_template("profile.html", currentPage = "myProfile", **sessionInfo, userData = userData, recentPosts = recentPosts,
    updateEmailForm=updateEmailForm, updateUsernameForm=updateUsernameForm, updateStatusForm=updateStatusForm)

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
            sender= os.environ['MAIL_USERNAME'],
            recipients=[user_email[0]])
        msg.body = "Password Change"
        msg.html = render_template('email.html', postID="change password", username=username, content=0, posted=0, url=abs_url)
        mail.send(msg)
    except Exception as e:
        print(e)
        print("Error:", sys.exc_info()[0])
        print("goes into except")
    else:
        flash('A change password link has been sent to your email. Use it to update your password.', 'success')
        flash('The password link will expire in 10 mins', 'warning')
        if sessionInfo['isAdmin']:
            return redirect('/adminProfile/' + str(username))
        else:
            return redirect('/profile/' + str(username))

@app.route('/reset/<url>', methods=["GET", "POST"])
def resetPassword(url):
    global user_to_url
    sql = "SELECT TIME_TO_SEC(TIMEDIFF(%s, Time_Created)) FROM password_url WHERE Url = %s"
    val = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),url)
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
            flash("Password has been successfully reset",'success')
            return redirect("/login")
        return render_template("changePassword.html", changePasswordForm=changePasswordForm)

@app.route('/topics')
def topics():

    sql = "SELECT Content,TopicID FROM topic ORDER BY Content "
    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()
    return render_template('topics.html', currentPage='topics', **sessionInfo, listOfTopics=listOfTopics)

@app.route('/indivTopic/<topicID>', methods=["GET", "POST"])
def indivTopic(topicID):
    sessionInfo = sessions[sessionID]
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
    topic=tupleCursor.fetchone()
    return render_template('indivTopic.html', currentPage='indivTopic', **sessionInfo, recentPosts=recentPosts, topic = topic[0])

@app.route('/adminProfile/<username>', methods=["GET", "POST"])
def adminUserProfile(username):
    sessionInfo = sessions[sessionID]
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
    if userData['Status'] == None:
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
            val = (updateEmailForm.email.data, str(sessionInfo["currentUserID"]))
            tupleCursor.execute(sql, val)
            db.commit()

        except mysql.connector.errors.IntegrityError as errorMsg: #Prevent error-based sql attack
            errorMsg = str(errorMsg)
            if 'email' in errorMsg.lower():
                updateEmailForm.email.errors.append('The email has already been linked to another account. Please use a different email.')
                flash("This email has already been linked to another account. Please use a different email.", "success")
        else:
            flash('Account successfully updated!', 'success')

            return redirect('/adminProfile/' + sessionInfo['username'])

    if request.method == "POST" and updateUsernameForm.validate():
        sql = "UPDATE user "
        sql += "SET Username=%s"
        sql += "WHERE UserID=%s"
        try:
            val = (updateUsernameForm.username.data, str(sessionInfo["currentUserID"]))
            tupleCursor.execute(sql, val)
            db.commit()

        except mysql.connector.errors.IntegrityError as errorMsg:
            errorMsg = str(errorMsg)
            if 'username' in errorMsg.lower():
                flash("This username is already taken!", "success")
                updateUsernameForm.username.errors.append('This username is already taken.')
        else:
            sql = "SELECT Username WHERE UserID=%s"
            val = (str(sessionInfo["currentUserID"]),)
            dictCursor.execute(sql, val)
            db.commit()
            sessionInfo['username'] = dictCursor['Username']
            sessions[sessionID] = sessionInfo
            flash('Account successfully updated! Your username now is %s.' %(sessionInfo['username']), 'success')
            return redirect('/adminProfile/' + sessionInfo['username'])

    if request.method == "POST" and updateStatusForm.validate():
        sql = "UPDATE user "
        sql += "SET Status=%s"
        sql += "WHERE UserID=%s"
        try:
            val = (updateStatusForm.status.data, str(sessionInfo["currentUserID"]))
            tupleCursor.execute(sql, val)
            db.commit()

        except mysql.connector.errors.IntegrityError as errorMsg:
            errorMsg = str(errorMsg)
            flash("An unexpected error has occurred!", "warning")
        else:
            flash('Account successfully updated!', 'success')

            return redirect('/adminProfile/' + sessionInfo['username'])


    return render_template("adminProfile.html", currentPage = "myProfile", **sessionInfo, userData = userData, recentPosts = recentPosts, admin=admin,
    updateEmailForm=updateEmailForm, updateUsernameForm=updateUsernameForm, updateStatusForm=updateStatusForm)



@app.route('/adminHome', methods=["GET", "POST"])
def adminHome():
    sessionInfo = sessions[sessionID]
    searchBarForm = Forms.SearchBarForm(request.form)
    searchBarForm.topic.choices = get_all_topics('all')
    if request.method == 'POST' and searchBarForm.validate():
        return redirect(url_for('searchPosts', searchQuery = searchBarForm.searchQuery.data, topic = searchBarForm.topic.data))

    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username,topic.TopicID, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " ORDER BY post.Upvotes-post.Downvotes DESC LIMIT 6"

    dictCursor.execute(sql)
    recentPosts = dictCursor.fetchall()
    for post in recentPosts:
        currentVote = DatabaseManager.get_user_post_vote(str(sessionInfo['currentUserID']), str(post['PostID']))
        if currentVote==None:
            post['UserVote'] = 0
        else:
            post['UserVote'] = currentVote['Vote']

        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        post['Content'] = post['Content'][:200]

    return render_template('adminHome.html', currentPage='adminHome', **sessionInfo, searchBarForm = searchBarForm,recentPosts = recentPosts)

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

    currentVote = DatabaseManager.get_user_post_vote(str(sessionInfo['currentUserID']), str(postID))
    if currentVote==None:
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

        currentVote = DatabaseManager.get_user_comment_vote(str(sessionInfo['currentUserID']), str(comment['CommentID']))
        if currentVote==None:
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
    commentForm.userID.data = sessionInfo['currentUserID']
    replyForm = Forms.ReplyForm(request.form)
    replyForm.userID.data = sessionInfo['currentUserID']

    if request.method == 'POST' and commentForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO comment (PostID, UserID, Content, DateTimePosted, Upvotes, Downvotes) VALUES (%s, %s, %s, %s, %s, %s)'
        val = (postID, commentForm.userID.data, commentForm.comment.data, dateTime, 0, 0)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Comment posted!', 'success')
        return redirect('/adminViewPost/%d' %(postID))

    if request.method == 'POST' and replyForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO reply (UserID, CommentID, Content, DateTimePosted) VALUES (%s, %s, %s, %s)'
        val = (replyForm.userID.data, replyForm.repliedID.data, replyForm.reply.data, dateTime)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Comment posted!', 'success')
        return redirect('/adminViewPost/%d' %(postID))

    return render_template('adminViewPost.html', currentPage='adminViewPost', **sessionInfo, post = post, commentList = commentList, commentForm=commentForm, replyForm=replyForm)

@app.route('/adminTopics')
def adminTopics():
    sessionInfo  = sessions[sessionID]
    sql = "SELECT Content,TopicID FROM topic ORDER BY Content "
    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()
    return render_template('adminTopics.html', currentPage='adminTopics', **sessionInfo, listOfTopics=listOfTopics)

@app.route('/adminIndivTopic/<topicID>', methods=["GET", "POST"])
def adminIndivTopic(topicID):
    sessionInfo = sessions[sessionID]
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
    topic=tupleCursor.fetchone()
    return render_template('adminIndivTopic.html', currentPage='adminIndivTopic', **sessionInfo, recentPosts=recentPosts, topic=topic[0])

@app.route('/addTopic', methods=["GET", "POST"])
def addTopic():
    sessionInfo = sessions[sessionID]

    if not sessionInfo['login']:
        return redirect('/login')

    sql = "SELECT Content FROM topic ORDER BY Content"

    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()

    topicForm = Forms.TopicForm(request.form)
    topicForm.topic.choices = listOfTopics
    if request.method == 'POST' and topicForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO topic ( UserID, Content, DateTimePosted) VALUES ( %s,%s, %s)'
        val = (sessionInfo["currentUserID"],topicForm.topic.data, dateTime)
        tupleCursor.execute(sql, val)
        db.commit()
        flash('Topic successfully created!', 'success')
        return redirect('/adminHome')



    return render_template('addTopic.html', currentPage='addTopic', **sessionInfo, topicForm=topicForm)

@app.route('/adminUsers')
def adminUsers():
    sessionInfo = sessions[sessionID]
    sql = "SELECT Username From user"
    tupleCursor.execute(sql)
    listOfUsernames = tupleCursor.fetchall()
    return render_template('adminUsers.html', currentPage='adminUsers', **sessionInfo, listOfUsernames = listOfUsernames)

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
            sender= os.environ['MAIL_USERNAME'],
            recipients=[user_email[0]])
        msg.body = "Your account has been terminated"
        msg.html = render_template('email.html', postID="delete user", username=username, content=0, posted=0)
        mail.send(msg)
    except Exception as e:
        print(e)
        print("Error:", sys.exc_info()[0])
        print("goes into except")

    return redirect('/adminUsers')

@app.route('/adminDeletePost/<postID>', methods=['POST','GET'])
def deletePost(postID):
    sql = "SELECT post.Content, post.DatetimePosted, post.postID, user.Username, user.email "
    sql += "FROM post"
    sql+= " INNER JOIN user ON post.UserID = user.UserID"
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
    sessionInfo = sessions[sessionID]
    sql = "SELECT feedback.Content, feedback.DatetimePosted, feedback.Reason,feedback.FeedbackID, user.Username, user.Email "
    sql += "FROM feedback"
    sql+= " INNER JOIN user ON feedback.UserID = user.UserID"
    sql += " WHERE feedback.Resolved = 0"
    dictCursor.execute(sql)
    feedbackList = dictCursor.fetchall()
    return render_template('adminFeedback.html', currentPage='adminFeedback', **sessionInfo, feedbackList=feedbackList)

@app.route('/replyFeedback/<feedbackID>',methods=["GET","POST"])
def replyFeedback(feedbackID):
    sessionInfo = sessions[sessionID]
    sql = "SELECT feedback.Content, feedback.DatetimePosted, feedback.Reason,feedback.FeedbackID, user.Username, user.Email "
    sql += "FROM feedback"
    sql+= " INNER JOIN user ON feedback.UserID = user.UserID"
    sql += " WHERE feedback.FeedbackID = %s"
    # sql += " AND feedback.Resolved = 0"
    val = (str(feedbackID),)
    dictCursor.execute(sql, val)
    feedbackList = dictCursor.fetchall()
    replyForm = Forms.ReplyFeedbackForm(request.form)
    # uncomment here
    if request.method == 'POST' and replyForm.validate():
        reply=replyForm.reply.data
        email=feedbackList[0]['Email']
        try:
            msg = Message("Lorem Ipsum",
                sender= os.environ['MAIL_USERNAME'],
                recipients=[email])
            msg.body = "We love your feedback!"
            msg.html = render_template('email.html', postID="feedback reply", username=feedbackList[0]['Username'], content=feedbackList[0]['Content'], posted=feedbackList[0]['DatetimePosted'], reply=reply)
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
    return render_template('replyFeedback.html', currentPage='replyFeedback', **sessionInfo,replyForm=replyForm, feedbackList=feedbackList)


if __name__ == "__main__":
    app.run(debug=True)
