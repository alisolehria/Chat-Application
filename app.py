from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_socketio import SocketIO,emit,join_room,leave_room
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from sqlalchemy.sql.expression import func
from sqlalchemy import desc
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import datetime
from flask_wtf.file import FileField
from hashlib import md5


app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:pass123@localhost/netapps'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
currentRoom = None


RoomUsers = db.Table("roomUsers", db.Column("roomId",db.Integer,db.ForeignKey("room.roomID"), primary_key=True),
db.Column("userID",db.Integer,db.ForeignKey("user.id"), primary_key=True))


#this is friends middle table
Friend = db.Table("friend",
db.Column("username1",db.Integer,db.ForeignKey("user.id"),primary_key=True),
db.Column("username2",db.Integer,db.ForeignKey("user.id"),primary_key=True))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    firstName = db.Column(db.String(80),nullable=False)
    lastName = db.Column(db.String(80),nullable=False)
    DOB = db.Column(db.DateTime)
    gender = db.Column(db.Boolean)
    joinDate = db.Column(db.DateTime)
    access = db.Column(db.String(80))
    room = db.relationship("Room", uselist=False,backref="user")
    roomUsers = db.relationship("Room", secondary=RoomUsers)
    message = db.relationship("Message", uselist=False,backref="user")
    friends = db.relationship("User",secondary=Friend, primaryjoin=(Friend.c.username1 == id),secondaryjoin=(Friend.c.username2 == id))
    lastMessage = ""
    timestamp = ""

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
    userInfo = ""
#
#class Report(db.Model):
#    reoportID = db.Column(db.Integer,primary_key = True)
#    reporter = db.Column(db.Integer,db.ForeignKey("user.id"))
#    reported = db.Column(db.Integer,db.ForeignKey("user.id"))
#    number = db.Column(db.Integer,nullable=False)
#    reason = db.Column(db.String(80),nullable=False)
#

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    firstName = StringField('First Name', validators=[InputRequired(), Length(min=3, max=15)])
    lastName = StringField('Last Name', validators=[InputRequired(), Length(min=4, max=15)])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])

class GroupForm(FlaskForm):
    roomName = StringField('Group Name', validators=[InputRequired(), Length(min=4, max=15)])


@app.route('/')
def index():
   return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('chat'))

        return '<h1>Invalid username or password</h1>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password,firstName=form.firstName.data,lastName=form.lastName.data)
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New user has been created!</h1>'
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('signup.html', form=form)

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html',user=current_user,name=current_user.username)


@app.route('/friendList',methods=['GET','POST'])
@login_required
def friendList():
    #print("here")
    for friend in current_user.friends:
        #now get their room
        allRooms = Room.query.filter_by(group = False).all()
        current_room = None
        #print(friend.lastName)
        for room in allRooms:
            if room in current_user.roomUsers and room in friend.roomUsers:
                current_room = room
                lastMessage = Message.query.filter_by(roomID=current_room.roomID).order_by(desc(Message.messageID)).first()
                friend.lastMessage = lastMessage
                friend.timestamp = lastMessage.timestamp


        #sortedList = current_user.friends[0].lastMessage.messageID
    sortedList = sorted(current_user.friends, key=lambda friend: friend.lastMessage.messageID,reverse = True)
    print(sortedList)
    return render_template('friendList.html', name=current_user.username, friendList = sortedList)

@app.route('/logout')
@login_required
def logout():
    lastAccess = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    current_user.access = "Last Online: "+lastAccess
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))


@app.route('/getUsers', methods=['GET', 'POST'])
@login_required
def getUsers():
    users = User.query.filter(User.id != current_user.id).all()
    for user in users:
        if user in current_user.friends:
            users.remove(user)
    #print(users)
    return render_template("usersList.html",users = users)



@app.route('/addFriend', methods=['GET', 'POST'])
@login_required
def addFriend():
    userid = request.form['friends']
    print(userid)
    new_friend = User.query.filter_by(id = userid).first()
    print(current_user.friends)
    current_user.friends.append(new_friend)
    new_friend.friends.append(current_user)
    #once added as friend create their personal room
    roomName = current_user.lastName + "/" + new_friend.lastName
    new_room = Room(roomName=roomName,group = False)
    current_user.roomUsers.append(new_room)
    new_friend.roomUsers.append(new_room)
    db.session.commit()
    return ""

@app.route('/chatBox', methods=['GET', 'POST'])
@login_required
def chatBox():
    friendId = request.form["id"]
    friend = User.query.filter_by(id = friendId).first()


    #now get their room
    allRooms = Room.query.filter_by(group = False).all()
    current_room = None
    for room in allRooms:
        if room in current_user.roomUsers and room in friend.roomUsers:
            current_room = room

    #retrive previous messages of this room
    messages = Message.query.filter_by(roomID=current_room.roomID).all()

    print(messages)
    return render_template("chatbox.html", friend = friend,room=current_room,user=current_user,messages=messages)


@app.route('/browseGroups', methods=['GET', 'POST'])
@login_required
def browseGroups():
    groups = Room.query.filter_by(group=True).all()
    for group in groups:
        if group in current_user.roomUsers:
            groups.remove(group)
    return render_template("browseGroups.html",groups = groups)


@app.route('/createGroup', methods=['GET', 'POST'])
@login_required
def createGroup():
    form = GroupForm()
    if form.validate_on_submit():
        roomName = form.roomName.data
        new_room = Room(roomName=roomName,admin = current_user.id, group = True)
        current_user.roomUsers.append(new_room)
        db.session.commit()

    return render_template("createGroup.html",form=form)


@app.route('/myGroups', methods=['GET', 'POST'])
@login_required
def myGroups():
    groups = Room.query.filter_by(group=True).all()
    myGroups = []
    for group in groups:
        if group in current_user.roomUsers:
            myGroups.append(group)
    return render_template("myGroups.html",groups = myGroups)


@app.route('/status',methods=['GET','POST'])
@login_required
def status():
    friend = request.form['id']
    access = User.query.filter_by(id=friend).first()
    #print(access.lastName)
    response = {}
    response['access'] = access.access
    return jsonify(response)

@app.route('/groupChat', methods=['GET', 'POST'])
@login_required
def groupChat():

    roomId = request.form["id"]
    #now get their room
    print(roomId)
    current_room = Room.query.filter_by(roomID = roomId).first()
    print(current_room)
    #retrive previous messages of this room
    messages = Message.query.filter_by(roomID=current_room.roomID).all()
    for message in messages:
        userInfo = User.query.filter_by(id=message.username).first()
        message.userInfo = userInfo
    print(messages)
    return render_template("groupChat.html",room=current_room,user=current_user,messages=messages,name=current_user.username)


#socketio functions
@socketio.on('connect')
@login_required
def client_connect():
    print("Client Conncected")
    current_user.access = "Online"
    db.session.commit()
    emit('server_response',{"data":"Connected to Server"})

@socketio.on('join')
@login_required
def join(message):
    join_room(message['room'])
    print("Entered: "+message['room'])
    return ""

@socketio.on('message_client')
@login_required
def handle_client_message(json):
    message = json['message']
    print("Message for room: "+json['room'])

    message_user =json['user']
    room=json['room']
    sender = User.query.filter_by(id=message_user).first()
    currentTime = datetime.datetime.now()
    new_message = Message(message=message,username=message_user,roomID=room,timestamp=currentTime)
    db.session.add(new_message)
    db.session.commit()
    emit('message_received',{"data":message,"user":current_user.id,"sender":sender.username},room=room)


@socketio.on('disconnect')
def test_disconnect():
    lastAccess = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    current_user.access = "Last Online: "+lastAccess
    db.session.commit()
    print('Client disconnected')

if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SESSION_PERMANENT'] = False
    socketio.run(app, debug=True, host='0.0.0.0')
    #app.run(debug=True)
