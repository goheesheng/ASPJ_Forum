import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="ASPJuser",
    password="P@55w0rD",
    database="mydatabase"
)

tupleCursor = db.cursor(buffered=True)
dictCursor = db.cursor(buffered=True, dictionary=True)

# Posts
def insert_post_vote(userID, postID, vote):
    sql = 'INSERT INTO post_votes (UserID, PostID, Vote) VALUES'
    sql += " ('" + userID + "'"
    sql += " , '" + postID + "'"
    sql += " , '" + vote + "')"
    tupleCursor.execute(sql)
    db.commit()

def delete_post_vote(userID, postID):
    sql = "DELETE FROM post_votes"
    sql += " WHERE UserID='" + userID + "'"
    sql += " AND PostID='" + postID + "'"
    tupleCursor.execute(sql)
    db.commit()

def update_post_vote(newVote, userID, postID):
    sql = "UPDATE post_votes SET"
    sql += " Vote='" + newVote + "'"
    sql += " WHERE UserID='" + userID + "'"
    sql += " AND PostID='" + postID + "'"
    tupleCursor.execute(sql)
    db.commit()

def update_overall_post_vote(upvoteChange, downvoteChange, postID):
    sql = "UPDATE post SET"
    sql += " Upvotes= Upvotes + " + upvoteChange
    sql += ", Downvotes= Downvotes + " + downvoteChange
    sql += " WHERE PostID='" + postID + "'"
    tupleCursor.execute(sql)
    db.commit()

def calculate_updated_post_votes(postID):
    sql = "SELECT Upvotes, Downvotes FROM post"
    sql += " WHERE PostID='" + postID + "'"
    dictCursor.execute(sql)
    postVotes = dictCursor.fetchone()
    db.commit()
    return postVotes['Upvotes'] - postVotes['Downvotes']

def get_user_post_vote(userID, postID):
    sql = "SELECT Vote FROM post_votes WHERE "
    sql += " UserID = '" + userID + "'"
    sql += " AND PostID = '" + postID + "'"
    dictCursor.execute(sql)
    currentVote = dictCursor.fetchone()
    return currentVote

# Comments
def insert_comment_vote(userID, commentID, vote):
    sql = 'INSERT INTO comment_votes (UserID, CommentID, Vote) VALUES'
    sql += " ('" + userID + "'"
    sql += " , '" + commentID + "'"
    sql += " , '" + vote + "')"
    tupleCursor.execute(sql)
    db.commit()

def delete_comment_vote(userID, commentID):
    sql = "DELETE FROM comment_votes"
    sql += " WHERE UserID='" + userID + "'"
    sql += " AND CommentID='" + commentID + "'"
    tupleCursor.execute(sql)
    db.commit()

def update_comment_vote(newVote, userID, commentID):
    sql = "UPDATE comment_votes SET"
    sql += " Vote='" + newVote + "'"
    sql += " WHERE UserID='" + userID + "'"
    sql += " AND CommentID='" + commentID + "'"
    tupleCursor.execute(sql)
    db.commit()

def update_overall_comment_vote(upvoteChange, downvoteChange, commentID):
    sql = "UPDATE comment SET"
    sql += " Upvotes= Upvotes + " + upvoteChange
    sql += ", Downvotes= Downvotes + " + downvoteChange
    sql += " WHERE CommentID='" + commentID + "'"
    tupleCursor.execute(sql)
    db.commit()

def calculate_updated_comment_votes(commentID):
    sql = "SELECT Upvotes, Downvotes FROM comment"
    sql += " WHERE CommentID='" + commentID + "'"
    dictCursor.execute(sql)
    commentVotes = dictCursor.fetchone()
    db.commit()
    return commentVotes['Upvotes'] - commentVotes['Downvotes']

def get_user_comment_vote(userID, commentID):
    sql = "SELECT Vote FROM comment_votes WHERE "
    sql += " UserID = '" + userID + "'"
    sql += " AND CommentID = '" + commentID + "'"
    dictCursor.execute(sql)
    currentVote = dictCursor.fetchone()
    return currentVote
