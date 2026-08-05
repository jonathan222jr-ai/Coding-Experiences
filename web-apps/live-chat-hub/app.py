from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

app = Flask(__name__)
# Supply a real secret via the environment when running anywhere but locally.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# --------------------
# Models
# --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --------------------
# Prompt
# --------------------
PROMPTS = [
    "What's a hot take you'll defend forever?",
    "What's something you learned the hard way?",
    "What's your current obsession?",
    "What's a small win you had recently?",
    "What's something people misunderstand about you?"
]

current_prompt = None

# --------------------
# Routes
# --------------------
@app.route("/")
def index():
    if "username" in session:
        return redirect("/chat")
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("An account with that username already exists.")
            return redirect(url_for("register"))

        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        session["username"] = username
        return redirect(url_for("chat"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("No account found with that username.")
            return redirect(url_for("login"))

        if not user.check_password(password):
            flash("Incorrect password.")
            return redirect(url_for("login"))

        session["username"] = username
        return redirect(url_for("chat"))

    return render_template("login.html")


@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect("/login")
    return render_template("chat.html")

# --------------------
# Socket.IO
# --------------------
@socketio.on("connect")
def on_connect():
    global current_prompt
    if current_prompt is None:
        current_prompt = random.choice(PROMPTS)
    emit("system_message", {"message": f"Chat prompt: {current_prompt}"})

@socketio.on("send_message")
def send_message(data):
    emit("receive_message", {
        "username": session["username"],
        "message": data["message"]
    }, broadcast=True)

@socketio.on("disconnect")
def handle_disconnect():
    username = session.get("username")
    if username:
        emit(
            "system_message",
            {"message": f"{username} left the chat"},
            broadcast=True
        )


# --------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
