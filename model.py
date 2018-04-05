from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:pass123@localhost/netapps'
db = SQLAlchemy(app)

#this is the middle table for users and rooms
RoomUsers = db.Table("roomUsers", db.Column("roomId",db.Integer,db.ForeignKey("room.roomID"), primary_key=True),
db.Column("userID",db.Integer,db.ForeignKey("user.id"), primary_key=True))


#this is friends middle table
Friend = db.Table("friend",
db.Column("username1",db.Integer,db.ForeignKey("user.id"),primary_key=True),
db.Column("username2",db.Integer,db.ForeignKey("user.id"),primary_key=True))

class User(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    firstName = db.Column(db.String(80),nullable=False)
    lastName = db.Column(db.String(80),nullable=False)
    DOB = db.Column(db.DateTime)
    gender = db.Column(db.Boolean)
    joinDate = db.Column(db.DateTime)
    access = db.Column(db.DateTime)
    room = db.relationship("Room", uselist=False,backref="user")
    roomUsers = db.relationship("Room", secondary=RoomUsers)
    message = db.relationship("Message", uselist=False,backref="user")
    friends = db.relationship("User",secondary=Friend, primaryjoin=(Friend.c.username1 == id),secondaryjoin=(Friend.c.username2 == id))
    reporter = db.relationship("Report", uselist=False,backref="user")
    reported = db.relationship("Report", uselist=False,backref="user")

#the room table
class Room(db.Model):
    roomID = db.Column(db.Integer,primary_key = True)
    roomName = db.Column(db.String(80), unique=True, nullable=False)
    admin = db.Column(db.Integer,db.ForeignKey("user.id"))
    group = db.Column(db.Boolean)
    messageRoom = db.relationship("Message", uselist=False,backref="user")

#the message table
class Message(db.Model):
    messageID = db.Column(db.Integer,primary_key = True)
    message = db.Column(db.String(80),nullable=False)
    username = db.Column(db.Integer,db.ForeignKey("user.id"))
    roomID = db.Column(db.Integer,db.ForeignKey("room.roomID"))
    timestamp = db.Column(db.DateTime,nullable=False)

class Report(db.Model):
    reoportID = db.Column(db.Integer,primary_key = True)
    reporter = db.Column(db.Integer,db.ForeignKey("user.id"))
    reported = db.Column(db.Integer,db.ForeignKey("user.id"))
    number = db.Column(db.Integer,nullable=False)
    reason = db.Column(db.String(80),nullable=False)


db.create_all()
