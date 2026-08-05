const MAX_PASSWORD_LENGTH = 72;

document.getElementById("btnLogin").addEventListener("click", async () => {
  const username = document.getElementById("username").value.trim();
  let password = document.getElementById("password").value;

  if (!username || !password) {
    alert("Username and password are required.");
    return;
  }

  if (password.length > MAX_PASSWORD_LENGTH) {
    alert(`Password too long. Max ${MAX_PASSWORD_LENGTH} characters.`);
    return;
  }

  const res = await apiPost("/auth/login", { username, password });

  if (res.detail || res.error) {
    alert(res.detail || res.error);
  } else {
    alert(res.message || "Logged in successfully.");
    window.location = "lobby.html";
  }
});
