from flask import Flask, request, jsonify  
# Import Flask (to create the web app), 
# request (to access data sent by the client),
# and jsonify (to return JSON responses easily).

from flask_cors import CORS  
# Import CORS (Cross-Origin Resource Sharing) so that a frontend on another domain/port can talk to this API.

app = Flask(__name__)  
# Create the Flask application object. 
# The __name__ variable helps Flask locate resources and know where the app is running from.

CORS(app)  # ✅ allow your frontend JS to talk to Flask  
# Enable CORS for the entire app, allowing JavaScript running in the browser to make requests to your Flask server.

# In-memory data store  
grades = {  
    "Alice": 95.0,  
    "Bob": 87.5,  
    "Charlie": 78.0  
}  
# A simple Python dictionary acting as a mock database.
# Keys are student names, values are their numeric grades.

@app.route("/grades", methods=["GET"])  
# Define a route (endpoint) for GET requests to "/grades".
# This will return all student grades.

def get_all_grades():  
    return jsonify(grades)  
# When someone visits /grades, return the entire 'grades' dictionary as JSON.

@app.route("/grades/<string:name>", methods=["GET"])  
# Define a route for GET requests to "/grades/<name>".
# The <string:name> part means Flask will treat that part of the URL as a variable.

def get_grade(name):  
    if name in grades:  
        return jsonify({name: grades[name]})  
    return jsonify({"error": "Student not found"}), 404  
# If the student exists in the dictionary, return their grade as JSON.
# If not, return an error message and HTTP status code 404 (Not Found).

@app.route("/grades", methods=["POST"])  
# Define a POST route to add a new student and grade to the dictionary.

def add_grade():  
    data = request.get_json()  
    # Parse the JSON data sent in the POST request body.

    name = data.get("name")  
    grade = data.get("grade")  
    # Extract the 'name' and 'grade' fields from the JSON.

    if not name or grade is None:  
        return jsonify({"error": "Invalid input"}), 400  
    # If 'name' is missing or 'grade' is None, return an error with HTTP 400 (Bad Request).

    grades[name] = grade  
    # Add the new student's name and grade to the dictionary.

    return jsonify({name: grade}), 201  
    # Return the newly added student info with HTTP 201 (Created).

@app.route("/grades/<string:name>", methods=["PUT"])  
# Define a PUT route to update an existing student's grade.

def update_grade(name):  
    if name not in grades:  
        return jsonify({"error": "Student not found"}), 404  
    # If the student does not exist, return 404.

    data = request.get_json()  
    grade = data.get("grade")  
    # Get the new grade value from the request body.

    grades[name] = grade  
    # Update the student's grade in the dictionary.

    return jsonify({name: grade})  
    # Return the updated student info as JSON.

@app.route("/grades/<string:name>", methods=["DELETE"])  
# Define a DELETE route to remove a student from the dictionary.

def delete_grade(name):  
    if name in grades:  
        deleted = grades.pop(name)  
        return jsonify({name: deleted})  
    # If the student exists, remove them from the dictionary and return their info.

    return jsonify({"error": "Student not found"}), 404  
    # If they don’t exist, return a 404 error.

if __name__ == "__main__":  
    app.run(debug=True)  
# This runs the Flask app only when this script is executed directly.
# debug=True enables hot reloading and detailed error messages — useful during development.
