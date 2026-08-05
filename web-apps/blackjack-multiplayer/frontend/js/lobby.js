async function renderGames() {
  const data = await apiGet("/api/games");
  const list = document.getElementById("gamesList");
  list.innerHTML = "";

  if (!data.games || data.games.length === 0) {
    list.innerText = "No games available.";
    return;
  }

  data.games.forEach(g => {
    const div = document.createElement("div");
    div.className = "panel";
    div.innerHTML = `
      <strong>${g.name}</strong> <small class="muted">${g.created_at}</small>
      <div>Players: ${g.players.map(p => p.username).join(", ")}</div>
      <div style="margin-top:8px;">
        <button onclick="join(${g.id})">Join</button>
      </div>
    `;
    list.appendChild(div);
  });
}

function join(gameId) {
  window.location = `game.html?gameId=${gameId}`;
}

document.getElementById("btnCreate").addEventListener("click", async () => {
  const name = document.getElementById("gameName").value || "Game Room";
  await apiPost("/api/games", { name });
  await renderGames();
});

document.getElementById("btnRefresh").addEventListener("click", renderGames);

document.getElementById("btnLogout").addEventListener("click", async () => {
  await apiPost("/auth/logout", {});
  window.location = "login.html";
});

renderGames();
