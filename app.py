from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_socketio import SocketIO,emit
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:pass123@localhost/netapps'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


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
    access = db.Column(db.DateTime)
    room = db.relationship("Room", uselist=False,backref="user")
    roomUsers = db.relationship("Room", secondary=RoomUsers)
    message = db.relationship("Message", uselist=False,backref="user")
    friends = db.relationship("User",secondary=Friend, primaryjoin=(Friend.c.username1 == id),secondaryjoin=(Friend.c.username2 == id))
#    reporter = db.relationship("Report",  primaryjoin=(Report.c.reporter == id),secondaryjoin=(Report.c.reported == id), uselist=False,backref="user")
#    reported = db.relationship("Report",primaryjoin=(Report.c.reported == id),secondaryjoin=(Report.c.reporter == id),  uselist=False,backref="user")

#the room table
class Room(db.Model):
    roomID = db.Column(db.Integer,primary_key = True)
    roomName = db.Column(db.String(80), unique=True, nullable=False)
    admin = db.Column(db.Integer,db.ForeignKey("user.id"))
    messageRoom = db.relationship("Message")

#the message table
class Message(db.Model):
    messageID = db.Column(db.Integer,primary_key = True)
    message = db.Column(db.String(80),nullable=False)
    username = db.Column(db.Integer,db.ForeignKey("user.id"))
    roomID = db.Column(db.Integer,db.ForeignKey("room.roomID"))
    timestamp = db.Column(db.DateTime,nullable=False)
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

    return render_template('chat.html', name=current_user.username, friendList = current_user.friends)

@app.route('/logout')
@login_required
def logout():
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
    db.session.commit()
    return ""


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    socketio.run(app, debug=True)
    #app.run(debug=True)
