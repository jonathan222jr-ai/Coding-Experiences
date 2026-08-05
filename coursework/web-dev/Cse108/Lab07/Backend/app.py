from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

# ------------------------------------------------
# Setup Flask + CORS
# ------------------------------------------------
app = Flask(__name__, static_folder="../Frontend", static_url_path="/")
CORS(app)

# ------------------------------------------------
# Database configuration
# ------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "grades.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ------------------------------------------------
# Database model
# ------------------------------------------------
class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    grade = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {self.name: self.grade}


# Create the database if it doesn’t exist
with app.app_context():
    db.create_all()


# ------------------------------------------------
# Routes for REST API
# ------------------------------------------------

# 1️⃣ GET /grades → Return all students/grades
@app.route("/grades", methods=["GET"])
def get_all_grades():
    all_grades = Grade.query.all()
    return jsonify({g.name: g.grade for g in all_grades})


# 2️⃣ GET /grades/<student> → Return one student's grade
@app.route("/grades/<student>", methods=["GET"])
def get_grade(student):
    student = student.strip()
    g = Grade.query.filter_by(name=student).first()
    if g:
        return jsonify(g.to_dict())
    return jsonify({"error": f"Student '{student}' not found."}), 404


# 3️⃣ POST /grades → Add a new student + grade
@app.route("/grades", methods=["POST"])
def add_grade():
    data = request.get_json()
    name = data.get("name", "").strip()
    grade = data.get("grade")

    if not name or grade is None:
        return jsonify({"error": "Missing name or grade"}), 400

    if Grade.query.filter_by(name=name).first():
        return jsonify({"error": f"Student '{name}' already exists."}), 400

    new_grade = Grade(name=name, grade=float(grade))
    db.session.add(new_grade)
    db.session.commit()
    return jsonify(new_grade.to_dict()), 201


# 4️⃣ PUT /grades/<student> → Edit an existing grade
@app.route("/grades/<student>", methods=["PUT"])
def update_grade(student):
    student = student.strip()
    data = request.get_json()
    grade = data.get("grade")

    if grade is None:
        return jsonify({"error": "Missing grade"}), 400

    g = Grade.query.filter_by(name=student).first()
    if not g:
        return jsonify({"error": f"Student '{student}' not found."}), 404

    g.grade = float(grade)
    db.session.commit()
    return jsonify(g.to_dict())


# 5️⃣ DELETE /grades/<student> → Delete a student
@app.route("/grades/<student>", methods=["DELETE"])
def delete_grade(student):
    student = student.strip()
    g = Grade.query.filter_by(name=student).first()
    if not g:
        return jsonify({"error": f"Student '{student}' not found."}), 404

    db.session.delete(g)
    db.session.commit()
    return jsonify({student: "deleted"})


# ------------------------------------------------
# Serve the Frontend
# ------------------------------------------------
@app.route("/")
def serve_frontend():
    return send_from_directory("../Frontend", "index.html")


# ------------------------------------------------
# Run the server
# ------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
