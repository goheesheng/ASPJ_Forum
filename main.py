from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, send_from_directory
import mysql.connector, re
import Forms
from datetime import datetime
# Flask mail
import os
from flask_mail import Mail, Message
import sys
import asyncio
from threading import Thread
import DatabaseManager

db = mysql.connector.connect(
    host="localhost",
    user="ASPJuser",
    password="P@55w0rD",
    database="mydatabase"
)

tupleCursor = db.cursor(buffered=True)
dictCursor = db.cursor(buffered=True, dictionary=True)
tupleCursor.execute("SHOW TABLES")
print(tupleCursor)

app = Flask(__name__)

app.config.update(
    MAIL_SERVER= 'smtp.office365.com',
    MAIL_PORT= 587,
    MAIL_USE_TLS= True,
    MAIL_USE_SSL= False,
	MAIL_USERNAME = 'deloremipsumonlinestore@outlook.com',
	# MAIL_PASSWORD = os.environ["MAIL_PASSWORD"],
	MAIL_DEBUG = True,
	MAIL_SUPPRESS_SEND = False,
    MAIL_ASCII_ATTACHMENTS = True,
    # Directory for admins to refer files (Files)
    UPLOAD_FOLDER = "templates\Files"
	)
cursor = db.cursor()

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
mail = Mail(app)
""" For testing purposes only. To make it convenient cause I can't remember all the account names.
Uncomment the account that you would like to use. To run the program as not logged in, run the first one."""
sessionInfo = {'login': False, 'currentUserID': 0, 'username': '', 'isAdmin': 0}
# sessionInfo = {'login': True, 'currentUserID': 1, 'username': 'NotABot', 'isAdmin': 1}
# sessionInfo = {'login': True, 'currentUserID': 2, 'username': 'CoffeeGirl', 'isAdmin': 1}
# sessionInfo = {'login': True, 'currentUserID': 3, 'username': 'Mehxa', 'isAdmin': 1}
# sessionInfo = {'login': True, 'currentUserID': 4, 'username': 'Kobot', 'isAdmin': 1}
# sessionInfo = {'login': True, 'currentUserID': 5, 'username': 'MarySinceBirthButStillSingle', 'isAdmin': 0}
# sessionInfo = {'login': True, 'currentUserID': 6, 'username': 'theauthenticcoconut', 'isAdmin': 0}
# sessionInfo = {'login': True, 'currentUserID': 7, 'username': 'johnnyjohnny', 'isAdmin': 0}
# sessionInfo = {'login': True, 'currentUserID': 8, 'username': 'iamjeff', 'isAdmin': 0}
# sessionInfo = {'login': True, 'currentUserID': 9, 'username': 'hanbaobao', 'isAdmin': 0}

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
    searchBarForm = Forms.SearchBarForm(request.form)
    searchBarForm.topic.choices = get_all_topics('all')
    if request.method == 'POST' and searchBarForm.validate():
        return redirect(url_for('searchPosts', searchQuery = searchBarForm.searchQuery.data, topic = searchBarForm.topic.data))

    searchQuery = request.args.get('searchQuery', default='')
    searchBarForm.searchQuery.data = searchQuery

    searchTopic = request.args.get('topic', default='0')
    searchBarForm.topic.data = searchTopic

    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " WHERE post.Title LIKE '%" + searchQuery + "%'"

    if searchTopic!='0':
        sql += " AND topic.TopicID='" + searchTopic + "'"

    dictCursor.execute(sql)
    relatedPosts = dictCursor.fetchall()
    for post in relatedPosts:
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        post['Content'] = post['Content'][:200]

    return render_template('searchPost.html', currentPage='search', **sessionInfo, searchBarForm=searchBarForm, postList=relatedPosts)

@app.route('/viewPost/<int:postID>', methods=["GET", "POST"])
def viewPost(postID):
    if not sessionInfo['login']:
        return redirect('/login')

    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " WHERE PostID=" + str(postID)
    dictCursor.execute(sql)
    post = dictCursor.fetchone()
    post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
    currentVote = DatabaseManager.get_user_post_vote(str(sessionInfo['currentUserID']), str(post['PostID']))
    if currentVote==None:
        post['UserVote'] = 0
    else:
        post['UserVote'] = currentVote['Vote']

    sql = "SELECT comment.CommentID, comment.Content, comment.DatetimePosted, comment.Upvotes, comment.Downvotes, comment.DatetimePosted, user.Username FROM comment"
    sql += " INNER JOIN user ON comment.UserID=user.UserID"
    sql += " WHERE comment.PostID=" + str(postID)
    dictCursor.execute(sql)
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
    replyForm = Forms.ReplyForm(request.form)

    if request.method == 'POST' and commentForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO comment (PostID, UserID, Content, DateTimePosted, Upvotes, Downvotes) VALUES"
        sql += " ('" + str(postID) + "'"
        sql += " , '" + str(sessionInfo['currentUserID']) + "'"
        sql += " , '" + commentForm.comment.data + "'"
        sql += " , '" + dateTime + "'"
        sql += " , 0, 0)"
        tupleCursor.execute(sql)
        db.commit()
        flash('Comment posted!', 'success')
        return redirect('/viewPost/%d' %(postID))

    if request.method == 'POST' and replyForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO reply (UserID, CommentID, Content, DateTimePosted) VALUES"
        sql += " ('" + str(sessionInfo['currentUserID']) + "'"
        sql += " , '" + replyForm.repliedID.data + "'"
        sql += " , '" + replyForm.reply.data + "'"
        sql += " , '" + dateTime + "')"
        tupleCursor.execute(sql)
        db.commit()
        flash('Comment posted!', 'success')
        return redirect('/viewPost/%d' %(postID))

    return render_template('viewPost.html', currentPage='viewPost', **sessionInfo, commentForm = commentForm, replyForm = replyForm, post = post, commentList = commentList)

@app.route('/addPost', methods=["GET", "POST"])
def addPost():
    if not sessionInfo['login']:
        return redirect('/login')

    postForm = Forms.PostForm(request.form)
    postForm.topic.choices = get_all_topics('default')

    if request.method == 'POST' and postForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO post (TopicID, UserID, DateTimePosted, Title, Content, Upvotes, Downvotes) VALUES'
        sql += " ('" + str(postForm.topic.data)+ "'"
        sql += " , '" + str(postForm.userID.data) + "'"
        sql += " , '" + dateTime + "'"
        sql += " , '" + postForm.title.data + "'"
        sql += " , '" + postForm.content.data + "'"
        sql += " , 0, 0)"
        tupleCursor.execute(sql)
        db.commit()
        flash('Post successfully created!', 'success')
        return redirect('/home')

    return render_template('addPost.html', currentPage='addPost', **sessionInfo, postForm=postForm)

@app.route('/feedback', methods=["GET", "POST"])
def feedback():
    if not sessionInfo['login']:
        return redirect('/login')
    feedbackForm = Forms.FeedbackForm(request.form)

    if request.method == 'POST' and feedbackForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO feedback (UserID, Reason, Content, DateTimePosted) VALUES'
        sql += " ('" + str(feedbackForm.userID.data) + "'"
        sql += " , '" + feedbackForm.reason.data + "'"
        sql += " , '" + feedbackForm.comment.data + "'"
        sql += " , '" + dateTime + "')"
        tupleCursor.execute(sql)
        db.commit()
        flash('Feedback sent!', 'success')
        return redirect('/feedback')

    return render_template('feedback.html', currentPage='feedback', **sessionInfo, feedbackForm = feedbackForm)

@app.route('/login', methods=["GET", "POST"])
def login():
    loginForm = Forms.LoginForm(request.form)
    if request.method == 'POST' and loginForm.validate():
        sql = "SELECT UserID, Username, isAdmin FROM user WHERE"
        sql += " Username='" + loginForm.username.data + "'"
        sql += " AND Password='" + loginForm.password.data + "'"
        dictCursor.execute(sql)
        findUser = dictCursor.fetchone()
        if findUser==None:
            # loginForm.password.errors.append('Wrong email or password.')
            sql = "SELECT Username FROM user u WHERE u.Username= '" + loginForm.username.data + "'"
            tupleCursor.execute(sql)
            username = tupleCursor.fetchone()
            sql = "SELECT Password FROM user u WHERE u.Password='" + loginForm.password.data + "'"
            tupleCursor.execute(sql)
            password = tupleCursor.fetchone()
            if not username and not password:
                loginForm.password.errors.append('Wrong email and password.')
            elif username==None:
                loginForm.password.errors.append('Wrong email or username.')

            elif password==None:
                loginForm.password.errors.append('Wrong password.')
        else:
            sessionInfo['login'] = True
            sessionInfo['currentUserID'] = int(findUser['UserID'])
            sessionInfo['username'] = findUser['Username']
            sessionInfo['isAdmin'] = findUser['isAdmin']
            sessionRecord = open("templates\Files\sessionRecord.txt","a")
            record = "%s signed in at %s\n" % (sessionInfo['username'], datetime.now())
            sessionRecord.write(record)
            sessionRecord.close()
            flash('Welcome! You are now logged in as %s.' %(sessionInfo['username']), 'success')
            if sessionInfo['isAdmin']:
                return redirect('/adminHome')
            else:
                return redirect('/home') # Change this later to redirect to profile page

    return render_template('login.html', currentPage='login', **sessionInfo, loginForm = loginForm)

@app.route('/logout')
def logout():
    sessionInfo['login'] = False
    sessionInfo['currentUser'] = 0
    sessionInfo['username'] = ''
    sessionRecord = open("templates\Files\sessionRecord.txt", "a")
    record = "%s signed out at %s \n" % (sessionInfo['username'], datetime.now())
    sessionRecord.close()
    return redirect('/home')

@app.route('/signup', methods=["GET", "POST"])
def signUp():
    signUpForm = Forms.SignUpForm(request.form)

    if request.method == 'POST' and signUpForm.validate():
        sql = "INSERT INTO user (Email, Username, Name, Birthday, Password, isAdmin) VALUES"
        sql += " ('" + signUpForm.email.data + "'"
        sql += " , '" + signUpForm.username.data + "'"
        sql += " , '" + signUpForm.name.data + "'"
        sql += " , '" + str(signUpForm.dob.data) + "'"
        sql += " , '" + signUpForm.password.data + "'"
        sql += " , '0')"
        try:
            tupleCursor.execute(sql)
            db.commit()

        except mysql.connector.errors.IntegrityError as errorMsg:
            errorMsg = str(errorMsg)
            if 'email' in errorMsg.lower():
                signUpForm.email.errors.append('The email has already been linked to another account. Please use a different email.')
            elif 'username' in errorMsg.lower():
                signUpForm.username.errors.append('This username is already taken.')

        else:
            sql = "SELECT UserID, Username FROM user WHERE"
            sql += " Username='" + signUpForm.username.data + "'"
            sql += " AND Password='" + signUpForm.password.data + "'"
            tupleCursor.execute(sql)
            findUser = tupleCursor.fetchone()
            sessionInfo['login'] = True
            sessionInfo['currentUserID'] = int(findUser[0])
            sessionInfo['username'] = findUser[1]
            sessionRecord = open("templates\Files\sessionRecord.txt", "a")
            record = "New account %s created at %s \n" % (sessionInfo['username'], datetime.now())
            sessionRecord.close()
            flash('Account successfully created! You are now logged in as %s.' %(sessionInfo['username']), 'success')
            return redirect('/home')

    return render_template('signup.html', currentPage='signUp', **sessionInfo, signUpForm = signUpForm)

@app.route('/profile/<username>', methods=["GET", "POST"])
def profile(username):
    updateProfileForm = Forms.SignUpForm(request.form)
    sql = "SELECT * FROM user WHERE user.Username='" + str(username) + "'"
    dictCursor.execute(sql)
    userData = dictCursor.fetchone()
    print(userData)
    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " WHERE user.Username='" + str(username) + "'"
    sql += " ORDER BY post.PostID DESC LIMIT 6"
    dictCursor.execute(sql)
    recentPosts = dictCursor.fetchall()
    userData['Credibility'] = 0
    if userData['Status'] == None:
        userData['Status'] = userData['Username'] + " is too lazy to add a status"
    for post in recentPosts:
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        userData['Credibility'] += post['TotalVotes']
        post['Content'] = post['Content'][:200]

    if request.method == "POST" and updateProfileForm.validate():
        oldUsername = username
        oldUserID = sessionInfo['currentUserID']
        sql = "UPDATE user "
        sql += "SET Username='" + updateProfileForm.username.data + "',"
        sql += "Password='" + updateProfileForm.password.data + "',"
        sql += "Name='" + updateProfileForm.name.data + "',"
        sql += "Email='" + updateProfileForm.email.data + "',"
        sql += "Status='" + updateProfileForm.status.data + "',"
        sql += "Birthday='" + str(updateProfileForm.dob.data) + "'"
        sql += "WHERE UserID='" + str(sessionInfo['currentUserID']) + "'"
        try:
            tupleCursor.execute(sql)
            db.commit()

        except mysql.connector.errors.IntegrityError as errorMsg:
            errorMsg = str(errorMsg)
            if 'email' in errorMsg.lower():
                updateProfileForm.email.errors.append('The email has already been linked to another account. Please use a different email.')
                flash("This email has already been linked to another account. Please use a different email.", "success")
            elif 'username' in errorMsg.lower():
                flash("This username is already taken!", "success")
                updateProfileForm.username.errors.append('This username is already taken.')
        else:
            sql = "SELECT UserID, Username FROM user WHERE"
            sql += " Username='" + updateProfileForm.username.data + "'"
            sql += " AND Password='" + updateProfileForm.password.data + "'"
            tupleCursor.execute(sql)
            findUser = tupleCursor.fetchone()
            sessionInfo['login'] = True
            sessionInfo['currentUserID'] = int(findUser[0])
            sessionInfo['username'] = findUser[1]
            sessionRecord = open("templates\Files\sessionRecord.txt", "a")
            if oldUsername == sessionInfo['username']:
                record = "Account %s updated at %s \n" % (sessionInfo['username'], datetime.now())
            else:
                record = "Account %s updated at %s, account's username is now %s\n" % (oldUsername,  datetime.now(), sessionInfo['username'])
            sessionRecord.close()

            if sessionInfo['currentUserID'] != oldUserID:
                flash('Account successfully updated! Your username now is %s.' %(sessionInfo['username']), 'success')
            else:
                flash('Account successfully updated!', 'success')

            return redirect('/profile/' + sessionInfo['username'])



    return render_template('profile.html', currentPage='myProfile', **sessionInfo, userData=userData, recentPosts=recentPosts, updateProfileForm=updateProfileForm)

@app.route('/topics')
def topics():
    # uncomment from here
    sql = "SELECT Content,TopicID FROM topic ORDER BY Content "
    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()
    return render_template('topics.html', currentPage='topics', **sessionInfo, listOfTopics=listOfTopics)

@app.route('/indivTopic/<topicID>', methods=["GET", "POST"])
def indivTopic(topicID):
    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " WHERE topic.TopicID = " + str(topicID)

    dictCursor.execute(sql)
    recentPosts = dictCursor.fetchall()
    for post in recentPosts:
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        post['Content'] = post['Content'][:200]
    topic = "SELECT Content FROM topic WHERE topic.TopicID=" + str(topicID)
    tupleCursor.execute(topic)
    topic=tupleCursor.fetchone()
    return render_template('indivTopic.html', currentPage='indivTopic', **sessionInfo, recentPosts=recentPosts, topic = topic[0])

@app.route('/adminProfile/<username>', methods=["GET", "POST"])
def adminUserProfile(username):
    sql = "SELECT * FROM user WHERE user.Username='" + str(username) + "'"
    dictCursor.execute(sql)
    userData = dictCursor.fetchone()
    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username, topic.TopicID, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " WHERE user.Username='" + str(username) + "'"
    sql += " ORDER BY post.PostID DESC LIMIT 6"
    dictCursor.execute(sql)
    recentPosts = dictCursor.fetchall()
    userData['Credibility'] = 0
    if userData['Status'] == None:
        userData['Status'] = userData['Username'] + " is too lazy to add a status"
    for post in recentPosts:
        post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
        userData['Credibility'] += post['TotalVotes']
        post['Content'] = post['Content'][:200]
    sql = "SELECT UserID, Username, isAdmin FROM user WHERE"
    sql += " Username='" + str(username) + "'"
    dictCursor.execute(sql)
    user = dictCursor.fetchone()
    admin = user['isAdmin']
    updateProfileForm = Forms.SignUpForm(request.form)
    if request.method == "POST" and updateProfileForm.validate():
        oldUsername = username
        oldUserID = sessionInfo['currentUserID']
        sql = "UPDATE user "
        sql += "SET Username='" + updateProfileForm.username.data + "',"
        sql += "Password='" + updateProfileForm.password.data + "',"
        sql += "Name='" + updateProfileForm.name.data + "',"
        sql += "Email='" + updateProfileForm.email.data + "',"
        sql += "Status='" + updateProfileForm.status.data + "',"
        sql += "Birthday='" + str(updateProfileForm.dob.data) + "'"
        sql += "WHERE UserID='" + str(sessionInfo['currentUserID']) + "'"
        try:
            tupleCursor.execute(sql)
            db.commit()

        except mysql.connector.errors.IntegrityError as errorMsg:
            errorMsg = str(errorMsg)
            if 'email' in errorMsg.lower():
                updateProfileForm.email.errors.append('The email has already been linked to another account. Please use a different email.')
                flash("This email has already been linked to another account. Please use a different email.", "success")
            elif 'username' in errorMsg.lower():
                flash("This username is already taken!", "success")
                updateProfileForm.username.errors.append('This username is already taken.')
        else:
            sql = "SELECT UserID, Username FROM user WHERE"
            sql += " Username='" + updateProfileForm.username.data + "'"
            sql += " AND Password='" + updateProfileForm.password.data + "'"
            tupleCursor.execute(sql)
            findUser = tupleCursor.fetchone()
            sessionInfo['login'] = True
            sessionInfo['currentUserID'] = int(findUser[0])
            sessionInfo['username'] = findUser[1]
            sessionRecord = open("templates\Files\sessionRecord.txt", "a")
            if oldUsername == sessionInfo['username']:
                record = "Account %s updated at %s \n" % (sessionInfo['username'], datetime.now())
            else:
                record = "Account %s updated at %s, account's username is now %s\n" % (oldUsername,  datetime.now(), sessionInfo['username'])
            sessionRecord.close()

            if sessionInfo['currentUserID'] != oldUserID:
                flash('Account successfully updated! Your username now is %s.' %(sessionInfo['username']), 'success')
            else:
                flash('Account successfully updated!', 'success')

            return redirect('/adminProfile/' + sessionInfo['username'])

    return render_template("adminProfile.html", currentPage = "myProfile", **sessionInfo, userData = userData, recentPosts = recentPosts, admin=admin, updateProfileForm=updateProfileForm)



@app.route('/adminHome', methods=["GET", "POST"])
def adminHome():
    searchBarForm = Forms.SearchBarForm(request.form)
    searchBarForm.topic.choices = get_all_topics('all')
    if request.method == 'POST' and searchBarForm.validate():
        return redirect(url_for('searchPosts', searchQuery = searchBarForm.searchQuery.data, topic = searchBarForm.topic.data))

    sql = "SELECT post.PostID, post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted, user.Username,topic.TopicID, topic.Content AS Topic FROM post"
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

    return render_template('adminHome.html', currentPage='adminHome', **sessionInfo, searchBarForm = searchBarForm,recentPosts = recentPosts)

@app.route('/adminViewPost/<int:postID>', methods=["GET", "POST"])
def adminViewPost(postID):
    commentForm = Forms.CommentForm(request.form)
    replyForm = Forms.ReplyForm(request.form)

    sql = "SELECT post.Title, post.Content, post.Upvotes, post.Downvotes, post.DatetimePosted,post.TopicID,post.PostID, user.Username, topic.Content AS Topic FROM post"
    sql += " INNER JOIN user ON post.UserID=user.UserID"
    sql += " INNER JOIN topic ON post.TopicID=topic.TopicID"
    sql += " WHERE PostID=" + str(postID)
    dictCursor.execute(sql)
    post = dictCursor.fetchone()
    post['TotalVotes'] = post['Upvotes'] - post['Downvotes']
    currentVote = DatabaseManager.get_user_post_vote(str(sessionInfo['currentUserID']), str(post['PostID']))
    if currentVote==None:
        post['UserVote'] = 0
    else:
        post['UserVote'] = currentVote['Vote']

    sql = "SELECT comment.CommentID, comment.Content, comment.DatetimePosted, comment.Upvotes, comment.Downvotes, comment.DatetimePosted, user.Username FROM comment"
    sql += " INNER JOIN user ON comment.UserID=user.UserID"
    sql += " WHERE comment.PostID=" + str(postID)
    dictCursor.execute(sql)
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

    if request.method == 'POST' and commentForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO comment (PostID, UserID, Content, DateTimePosted, Upvotes, Downvotes) VALUES"
        sql += " ('" + str(postID) + "'"
        sql += " , '" + str(sessionInfo['currentUserID']) + "'"
        sql += " , '" + commentForm.comment.data + "'"
        sql += " , '" + dateTime + "'"
        sql += " , 0, 0)"
        tupleCursor.execute(sql)
        db.commit()
        flash('Comment posted!', 'success')
        return redirect('/adminViewPost/%d' %(postID))

    if request.method == 'POST' and replyForm.validate():
        dateTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO reply (UserID, CommentID, Content, DateTimePosted) VALUES"
        sql += " ('" + str(sessionInfo['currentUserID']) + "'"
        sql += " , '" + replyForm.repliedID.data + "'"
        sql += " , '" + replyForm.reply.data + "'"
        sql += " , '" + dateTime + "')"
        tupleCursor.execute(sql)
        db.commit()
        flash('Comment posted!', 'success')
        return redirect('/adminViewPost/%d' %(postID))

    return render_template('adminViewPost.html', currentPage='adminViewPost', **sessionInfo, commentForm = commentForm, replyForm = replyForm, post = post, commentList = commentList)

@app.route('/adminTopics')
def adminTopics():
    sql = "SELECT Content,TopicID FROM topic ORDER BY Content "
    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()
    return render_template('adminTopics.html', currentPage='adminTopics', **sessionInfo, listOfTopics=listOfTopics)

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
    topic = "SELECT Content FROM topic WHERE topic.TopicID=" + str(topicID)
    tupleCursor.execute(topic)
    topic=tupleCursor.fetchone()
    return render_template('adminIndivTopic.html', currentPage='adminIndivTopic', **sessionInfo, recentPosts=recentPosts, topic=topic[0])

@app.route('/addTopic', methods=["GET", "POST"])
def addTopic():
    if not sessionInfo['login']:
        return redirect('/login')
    sql = "SELECT Content FROM topic ORDER BY Content"

    tupleCursor.execute(sql)
    listOfTopics = tupleCursor.fetchall()

    topicForm = Forms.TopicForm(request.form)
    if request.method == 'POST' and topicForm.validate():
        topicTuple = (topicForm.topic.data,)
        if topicTuple in listOfTopics:
            print("Duplicate caught")
            flash("Topic already exists!", "danger")
            return redirect('/addTopic')
        else:
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
    sql = "SELECT Username From user"
    tupleCursor.execute(sql)
    listOfUsernames = tupleCursor.fetchall()
    print(listOfUsernames)
    return render_template('adminUsers.html', currentPage='adminUsers', **sessionInfo, listOfUsernames = listOfUsernames)

@app.route('/adminDeleteUser/<username>', methods=['POST'])
def deleteUser(username):
    user_email = "SELECT Email FROM user WHERE user.username='"+username+"'"
    tupleCursor.execute(user_email)
    sql = "DELETE FROM user WHERE user.username= '"+username+"'"
    tupleCursor.execute(sql)
    try:
        msg = Message("Lorem Ipsum",
            sender="deloremipsumonlinestore@outlook.com",
            recipients=[user_email[0]])
        msg.body = "Your account has been terminated"
        msg.html = render_template('email.html', postID="delete user", username=username, content=0, posted=0)
        mail.send(msg)
        print("\n\n\nMAIL SENT\n\n\n")
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
    sql += " WHERE post.PostID = " + str(postID)
    dictCursor.execute(sql)
    email_info = dictCursor.fetchall()
    print(email_info)
    sql = "DELETE FROM post WHERE post.PostID= '"+postID+"'"
    tupleCursor.execute(sql)
    db.commit()
    try:
        msg = Message("Lorem Ipsum",
            sender="deloremipsumonlinestore@outlook.com",
            recipients=[email_info[0]['email']])
        msg.body = "Your post has been deleted"
        for info in email_info:
            msg.html = render_template('email.html', postID=postID, username=info['Username'], content=info['Content'], posted=info['DatetimePosted'])
            mail.send(msg)
        print("\n\n\nMAIL SENT\n\n\n")
    except Exception as e:
        print(e)
        print("Error:", sys.exc_info()[0])
        print("goes into except")

    return redirect('/adminHome')

@app.route('/adminFeedback')
def adminFeedback():
    sql = "SELECT feedback.Content, feedback.DatetimePosted, feedback.Reason,feedback.FeedbackID, user.Username, user.Email "
    sql += "FROM feedback"
    sql+= " INNER JOIN user ON feedback.UserID = user.UserID"
    dictCursor.execute(sql)
    feedbackList = dictCursor.fetchall()
    print(feedbackList)
    return render_template('adminFeedback.html', currentPage='adminFeedback', **sessionInfo, feedbackList=feedbackList)

@app.route('/replyFeedback/<feedbackID>',methods=["GET","POST"])
def replyFeedback(feedbackID):
    sql = "SELECT feedback.Content, feedback.DatetimePosted, feedback.Reason,feedback.FeedbackID, user.Username, user.Email "
    sql += "FROM feedback"
    sql+= " INNER JOIN user ON feedback.UserID = user.UserID"
    sql += " WHERE feedback.FeedbackID = " + str(feedbackID)
    dictCursor.execute(sql)
    feedbackList = dictCursor.fetchall()
    print(feedbackList)
    replyForm = Forms.ReplyFeedbackForm(request.form)
    # uncomment here
    if request.method == 'POST' and replyForm.validate():
        reply=replyForm.reply.data
        email=feedbackList[0]['Email']
        print(email)
        try:
            msg = Message("Lorem Ipsum",
                sender="deloremipsumonlinestore@outlook.com",
                recipients=[email])
            msg.body = "We love your feedback!"
            msg.html = render_template('email.html', postID="feedback reply", username=feedbackList[0]['Username'], content=feedbackList[0]['Content'], posted=feedbackList[0]['DatetimePosted'], reply=reply)
            mail.send(msg)
            print("\n\n\nMAIL SENT\n\n\n")
        except Exception as e:
            print(e)
            print("Error:", sys.exc_info()[0])
            print("goes into except")
        return redirect('/adminFeedback')
    return render_template('replyFeedback.html', currentPage='replyFeedback', **sessionInfo,replyForm=replyForm, feedbackList=feedbackList)

@app.route('/adminFiles')
def list_files():
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(path):
            files.append(filename)
    print(files)
    return render_template('adminFiles.html', files=files, **sessionInfo)

@app.route('/adminFiles/<path:path>')
def download(path):
    return send_from_directory(directory=app.config['UPLOAD_FOLDER'], filename=path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
