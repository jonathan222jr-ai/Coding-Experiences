const urlParams = new URLSearchParams(window.location.search);
const gameId = urlParams.get("gameId");
const socket = new WebSocket(`ws://127.0.0.1:5000/ws/game`);

let state = null;

socket.onopen = () => console.log("WebSocket connected");

socket.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  if (msg.type === "game_state") {
    state = msg.data;
    renderState();
  } else if (msg.type === "chat") {
    appendChat(`${msg.user}: ${msg.text}`);
  } else if (msg.type === "error") {
    alert(msg.message);
  }
};

function appendChat(txt) {
  const box = document.getElementById("chatBox");
  const el = document.createElement("div");
  el.innerText = txt;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
}

function sendAction(action, extra = {}) {
  socket.send(JSON.stringify({ action, gameId: parseInt(gameId), ...extra }));
}

document.getElementById("btnSend").addEventListener("click", () => {
  const text = document.getElementById("chatInput").value;
  if (!text) return;
  sendAction("chat", { text });
  document.getElementById("chatInput").value = "";
});

document.getElementById("btnBet").addEventListener("click", () => {
  const amount = parseInt(document.getElementById("betAmount").value || "0");
  sendAction("place_bet", { amount });
});

document.getElementById("btnReady").addEventListener("click", () => sendAction("player_ready"));
document.getElementById("btnStart").addEventListener("click", () => sendAction("start_game"));
document.getElementById("btnHit").addEventListener("click", () => sendAction("hit"));
document.getElementById("btnStand").addEventListener("click", () => sendAction("stand"));

function cardLabel(c) {
  if (!c) return "";
  return `${c.r}${c.s}`;
}

function renderState() {
  document.getElementById("roomTitle").innerText = `Game Room #${gameId} — ${state?.status || ""}`;

  const list = document.getElementById("playerList");
  list.innerHTML = "";
  for (const [pid, p] of Object.entries(state?.players || {})) {
    const li = document.createElement("li");
    li.className = "player-item";
    const name = document.createElement("div");
    name.innerHTML = `<strong>${p.username}</strong> <small class="muted">[${p.status}]</small>`;
    const right = document.createElement("div");
    right.innerHTML = `Bet: ${p.bet || 0} <br/>Bal: ${p.balance || "-"}`;
    const hand = document.createElement("div");
    hand.className = "card-row";
    (p.hand || []).forEach(c => {
      const cd = document.createElement("div");
      cd.className = "card";
      cd.innerText = cardLabel(c);
      hand.appendChild(cd);
    });
    const wrap = document.createElement("div");
    wrap.appendChild(name);
    wrap.appendChild(hand);
    wrap.appendChild(right);
    li.appendChild(wrap);
    list.appendChild(li);
  }

  const drow = document.getElementById("dealerCards");
  drow.innerHTML = "";
  (state?.dealer?.hand || []).forEach(c => {
    const cd = document.createElement("div");
    cd.className = "card";
    cd.innerText = cardLabel(c);
    drow.appendChild(cd);
  });

  const chatBox = document.getElementById("chatBox");
  chatBox.innerHTML = "";
  (state?.chat || []).forEach(m => appendChat(`${m.user}: ${m.text}`));
}
