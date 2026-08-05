from app import app, db, User, Course, Enrollment
import random

with app.app_context():
    # ------------------
    # Reset DB
    # ------------------
    db.drop_all()
    db.create_all()

    # ------------------
    # Create users
    # ------------------
    students = [
        "Harry Potter", "Ron Weasley", "Hermione Granger", "Draco Malfoy",
        "Neville Longbottom", "Luna Lovegood", "Ginny Weasley", "Fred Weasley"
    ]
    teachers = ["Minerva McGonagall", "Rubeus Hagrid", "Severus Snape", "Pomona Sprout"]

    for name in students:
        u = User(username=name, role="student")
        u.set_password("password")
        db.session.add(u)

    for t in teachers:
        u = User(username=t, role="teacher")
        u.set_password("password")
        db.session.add(u)

    # Admin user
    admin = User(username="admin", role="admin")
    admin.set_password("admin")
    db.session.add(admin)
    db.session.commit()

    def get_user(name):
        return User.query.filter_by(username=name).first()

    # ------------------
    # Create courses
    # ------------------
    courses = [
        {"name": "Potions", "teacher": "Severus Snape", "time": "MWF 9:00-9:50 AM", "capacity": 8},
        {"name": "Transfiguration", "teacher": "Minerva McGonagall", "time": "TR 10:00-10:50 AM", "capacity": 8},
        {"name": "Herbology", "teacher": "Pomona Sprout", "time": "MWF 11:00-11:50 AM", "capacity": 8},
        {"name": "Care of Magical Creatures", "teacher": "Rubeus Hagrid", "time": "TR 1:00-1:50 PM", "capacity": 8},
        {"name": "Defense Against the Dark Arts", "teacher": "Remus Lupin", "time": "TR 2:00-2:50 PM", "capacity": 8},
        {"name": "Astronomy", "teacher": "Aurora Sinistra", "time": "MW 7:00-7:50 PM", "capacity": 8},
    ]

    course_objs = []
    for c in courses:
        course_objs.append(Course(
            name=c["name"],
            teacher=get_user(c["teacher"]),
            time=c["time"],
            capacity=c["capacity"]
        ))

    db.session.add_all(course_objs)
    db.session.commit()

    # ------------------
    # Enroll students with random courses and random grades
    # ------------------
    def enroll(student_name, course):
        student = get_user(student_name)
        grade = random.randint(60, 100)
        db.session.add(Enrollment(student_id=student.id, course_id=course.id, grade=grade))

    # Each student gets enrolled in 2 random courses
    for student_name in students:
        chosen_courses = random.sample(course_objs, 2)
        for course in chosen_courses:
            enroll(student_name, course)

    db.session.commit()
    print("Database populated successfully with Harry Potter students, teachers, and classes!")
