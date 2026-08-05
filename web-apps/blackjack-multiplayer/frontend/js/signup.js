const MAX_PASSWORD_LENGTH = 72;

document.getElementById("btnSignup").addEventListener("click", async () => {
  const username = document.getElementById("username").value.trim();
  let password = document.getElementById("password").value;
  let passwordConfirm = document.getElementById("passwordConfirm").value;

  if (!username || !password || !passwordConfirm) {
    alert("All fields are required.");
    return;
  }

  if (password.length > MAX_PASSWORD_LENGTH) {
    alert(`Password too long. Max ${MAX_PASSWORD_LENGTH} characters.`);
    return;
  }

  if (password !== passwordConfirm) {
    alert("Passwords do not match.");
    return;
  }

  const res = await apiPost("/auth/signup", { username, password });

  if (res.detail || res.error) {
    alert(res.detail || res.error);
  } else {
    alert(res.message || "Account created successfully.");
    window.location = "login.html";
  }
});
