from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="sql12231151",
    password="iNNxRJnZLM",
    hostname="sql12.freemysqlhosting.net",
    databasename="sql12231151",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:pass123@localhost/netapps'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://aliaschat:courseworkdb@aliaschat.mysql.pythonanywhere-services.com/netapps'
db = SQLAlchemy(app)

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
    DOB = db.Column(db.Date)
    gender = db.Column(db.Boolean)
    joinDate = db.Column(db.DateTime)
    access = db.Column(db.String(80))
    room = db.relationship("Room", uselist=False,backref="user")
    roomUsers = db.relationship("Room", secondary=RoomUsers)
    message = db.relationship("Message", uselist=False,backref="user")
    friends = db.relationship("User",secondary=Friend, primaryjoin=(Friend.c.username1 == id),secondaryjoin=(Friend.c.username2 == id))
    count = ""


    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    #'https://www.gravatar.com/avatar/97d6961ceb3d48624c4ea08ef2733d85'
#    reporter = db.relationship("Report",  primaryjoin=(Report.c.reporter == id),secondaryjoin=(Report.c.reported == id), uselist=False,backref="user")
#    reported = db.relationship("Report",primaryjoin=(Report.c.reported == id),secondaryjoin=(Report.c.reporter == id),  uselist=False,backref="user")

#the room table
class Room(db.Model):
    roomID = db.Column(db.Integer,primary_key = True)
    roomName = db.Column(db.String(80), unique=True, nullable=False)
    admin = db.Column(db.Integer,db.ForeignKey("user.id"))
    group = db.Column(db.Boolean)
    messageRoom = db.relationship("Message")

#the message table
class Message(db.Model):
    messageID = db.Column(db.Integer,primary_key = True)
    message = db.Column(db.String(80),nullable=False)
    username = db.Column(db.Integer,db.ForeignKey("user.id"))
    roomID = db.Column(db.Integer,db.ForeignKey("room.roomID"))
    timestamp = db.Column(db.DateTime,nullable=False)
    seen = db.Column(db.Boolean)
    userInfo = ""

db.create_all()
