from flask import Flask, redirect, session, render_template, flash, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, LoginManager, login_required, current_user, logout_user, UserMixin
from datetime import datetime

app = Flask(__name__)

# Configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydb.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "ppppppppppppppppppp"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
db = SQLAlchemy(app)

# Define the User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    fname = db.Column(db.String(50), nullable=False)
    lname = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    profile_pic = db.Column(db.String(255), default="default.jpg")

    def __repr__(self):
        return f"<User {self.id}>"

# Define the Friendship model
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="pending")  # e.g., 'pending', 'accepted', 'rejected'

    user = db.relationship("User", foreign_keys=[user_id], backref="friends_1")
    friend = db.relationship("User", foreign_keys=[friend_id], backref="friends_2")

    def __repr__(self):
        return f"<Friendship {self.user_id} - {self.friend_id}>"

# Define the Message model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="received_messages")

    def __repr__(self):
        return f"<Message {self.id} from {self.sender_id} to {self.receiver_id}>"

# Ensure tables are created
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/users", methods=["GET"])
@login_required
def users():
    users = User.query.all()
    return render_template("users.html", users=users)

@app.route("/profile/<int:user_id>", methods=["GET"])
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        return render_template("profile.html", user=user, own_profile=True)
    else:
        return render_template("profile.html", user=user, own_profile=False)

@app.route("/", methods=["GET", "POST"])
def main():
    if current_user.is_authenticated:
        return redirect(url_for("users"))

    message = session.pop("message", None)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("users"))
        else:
            message = "Invalid email or password!"
    return render_template("home.html", message=message)

@app.route("/Create_new_account", methods=["POST", "GET"])
def Create_new_account():
    if current_user.is_authenticated:
        return redirect(url_for("users"))

    message = None
    if request.method == "POST":
        email = request.form.get("email")
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        password = request.form.get("password")
        if User.query.filter_by(email=email).first():
            message = "The email address is already registered. Please use a different email."
        else:
            user = User(email=email, fname=fname, lname=lname, password=password)
            db.session.add(user)
            db.session.commit()
            session["message"] = "Account created successfully!"
            return redirect('/')
    return render_template("Create_new_account.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("users"))

    message = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("users"))
        else:
            message = "Invalid email or password!"
    return render_template("login.html", message=message)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main"))

# Add Friend Route
@app.route("/add_friend/<int:user_id>", methods=["POST"])
@login_required
def add_friend(user_id):
    if user_id == current_user.id:
        flash("You cannot add yourself as a friend!", "error")
        return redirect(url_for("profile", user_id=user_id))

    # Check if they are already friends
    existing_friendship = Friendship.query.filter(
        (Friendship.user_id == current_user.id) & (Friendship.friend_id == user_id)
    ).first()

    if existing_friendship:
        flash("You are already friends!", "info")
    else:
        new_friendship = Friendship(user_id=current_user.id, friend_id=user_id, status="pending")
        db.session.add(new_friendship)
        db.session.commit()
        flash("Friend request sent!", "success")

    return redirect(url_for("profile", user_id=user_id))

# Accept Friend Request Route
@app.route("/accept_friend/<int:friendship_id>", methods=["POST"])
@login_required
def accept_friend(friendship_id):
    friendship = Friendship.query.get_or_404(friendship_id)

    if friendship.friend_id == current_user.id and friendship.status == "pending":
        friendship.status = "accepted"
        db.session.commit()
        flash("Friend request accepted!", "success")
    else:
        flash("You cannot accept this request.", "error")

    return redirect(url_for("users"))



# View Friends Route
@app.route("/friends")
@login_required
def friends():
    # Fetch accepted friendships for the current user
    friends = Friendship.query.filter(
        (Friendship.user_id == current_user.id) & (Friendship.status == "accepted")
    ).all()

    friend_list = []
    for friendship in friends:
        if friendship.user_id == current_user.id:
            friend_list.append(friendship.friend)
        else:
            friend_list.append(friendship.user)

    return render_template("friends.html", friends=friend_list)

# Send Message Route
@app.route("/send_message/<int:receiver_id>", methods=["POST"])
@login_required
def send_message(receiver_id):
    content = request.form.get("content")
    if not content:
        flash("Message cannot be empty.", "error")
        return redirect(url_for("profile", user_id=receiver_id))

    new_message = Message(sender_id=current_user.id, receiver_id=receiver_id, content=content)
    db.session.add(new_message)
    db.session.commit()
    flash("Message sent!", "success")

    return redirect(url_for("profile", user_id=receiver_id))

# View Messages Route
@app.route("/messages", methods=["GET"])
@login_required
def messages():
    received_messages = Message.query.filter_by(receiver_id=current_user.id).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).all()

    return render_template("messages.html", received_messages=received_messages, sent_messages=sent_messages)

if __name__ == "__main__":
    app.run(debug=True)
