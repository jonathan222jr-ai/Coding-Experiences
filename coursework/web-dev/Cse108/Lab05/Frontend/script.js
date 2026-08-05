const API_BASE = "http://127.0.0.1:5000";
// The base URL of your Flask backend.
// All fetch() requests will start with this address.

// -------------------------------
// GET /grades/<student>
// -------------------------------
document.getElementById("getGradeBtn").addEventListener("click", async () => {
  // Add a click event listener to the button with ID "getGradeBtn".
  // When clicked, this asynchronous function runs.

  const name = document.getElementById("studentName").value.trim();
  // Get the student's name from the input field and remove extra spaces.

  const result = document.getElementById("gradeResult");
  // Get the element where the result or error message will be displayed.

  if (!name) return (result.textContent = "Enter a student name.");
  // If the input is empty, show a message and stop execution.

  try {
    const res = await fetch(`${API_BASE}/grades/${encodeURIComponent(name)}`);
    // Send a GET request to Flask, e.g. http://127.0.0.1:5000/grades/Alice
    // encodeURIComponent() ensures special characters in names don’t break the URL.

    const data = await res.json();
    // Convert the JSON response from the server into a JavaScript object.

    if (res.ok) {
      result.textContent = `${name}: ${data[name]}`;
      // If HTTP status is OK (200), display the student's name and grade.
    } else {
      result.textContent = data.error || "Student not found.";
      // If not OK (like 404), display the error message returned by Flask.
    }
  } catch (err) {
    result.textContent = "Error connecting to server.";
    // If fetch fails (e.g., server offline), show a connection error.
  }
});

// -------------------------------
// GET /grades
// -------------------------------
document.getElementById("getAllBtn").addEventListener("click", async () => {
  // When "Get All Grades" button is clicked, run this function.

  try {
    const res = await fetch(`${API_BASE}/grades`);
    // Send a GET request to the Flask route /grades to get all students.

    const data = await res.json();
    // Parse the JSON response from Flask.

    const tbody = document.querySelector("#gradesTable tbody");
    // Get the table body where all grades will be displayed.

    tbody.innerHTML = "";
    // Clear out any old table data.

    for (const [name, grade] of Object.entries(data)) {
      // Loop through each student in the response data.
      // Object.entries() turns {Alice: 95, Bob: 87} into [["Alice", 95], ["Bob", 87]].

      const row = `<tr><td>${name}</td><td>${grade}</td></tr>`;
      // Create a table row with the student's name and grade.

      tbody.insertAdjacentHTML("beforeend", row);
      // Add the new row to the table.
    }
  } catch (err) {
    alert("Error fetching grades");
    // If something goes wrong, show an alert to the user.
  }
});

// -------------------------------
// POST /grades
// -------------------------------
document.getElementById("addBtn").addEventListener("click", async () => {
  // Runs when the "Add Grade" button is clicked.

  const name = document.getElementById("newName").value.trim();
  const grade = parseFloat(document.getElementById("newGrade").value);
  // Get values from input fields and convert grade to a number.

  if (!name || isNaN(grade)) return alert("Enter a valid name and grade.");
  // Validate inputs — must have a name and a numeric grade.

  try {
    const res = await fetch(`${API_BASE}/grades`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, grade })
    });
    // Send a POST request to Flask to add a new grade.
    // The body contains the new student info in JSON format.

    const data = await res.json();
    // Parse Flask’s JSON response.

    alert(`Added: ${Object.keys(data)[0]} = ${Object.values(data)[0]}`);
    // Show an alert confirming what was added.
  } catch {
    alert("Error adding grade");
    // Handle connection or fetch errors.
  }
});

// -------------------------------
// PUT /grades/<name>
// -------------------------------
document.getElementById("editBtn").addEventListener("click", async () => {
  // Runs when the "Edit Grade" button is clicked.

  const name = document.getElementById("editName").value.trim();
  const grade = parseFloat(document.getElementById("editGrade").value);
  // Get inputs for the name and new grade.

  if (!name || isNaN(grade)) return alert("Enter a valid name and grade.");
  // Validate the inputs.

  try {
    const res = await fetch(`${API_BASE}/grades/${encodeURIComponent(name)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ grade })
    });
    // Send a PUT request to Flask to update a student's grade.

    const data = await res.json();
    // Parse Flask’s response.

    alert(res.ok
      ? `Updated: ${Object.keys(data)[0]} = ${Object.values(data)[0]}`
      : data.error);
    // If successful, alert the updated value; otherwise, show an error.
  } catch {
    alert("Error updating grade");
    // Show an alert if the server or network fails.
  }
});

// -------------------------------
// DELETE /grades/<name>
// -------------------------------
document.getElementById("deleteBtn").addEventListener("click", async () => {
  // Runs when the "Delete Grade" button is clicked.

  const name = document.getElementById("deleteName").value.trim();
  // Get the student name to delete.

  if (!name) return alert("Enter a name to delete.");
  // Stop if the input is empty.

  try {
    const res = await fetch(`${API_BASE}/grades/${encodeURIComponent(name)}`, {
      method: "DELETE"
    });
    // Send a DELETE request to Flask for that student.

    const data = await res.json();
    // Parse the JSON response.

    alert(res.ok ? `Deleted ${Object.keys(data)[0]}` : data.error);
    // If successful, show which student was deleted.
    // If not, show the error returned by Flask.
  } catch {
    alert("Error deleting grade");
    // Catch any fetch or network errors.
  }
});
