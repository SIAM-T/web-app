from flask import Flask, redirect, session, render_template, flash, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, LoginManager, login_required, current_user, logout_user, UserMixin

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

if __name__ == "__main__":
    app.run(debug=True)
