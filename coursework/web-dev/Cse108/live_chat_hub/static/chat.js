const socket = io();

socket.on("system_message", data => {
  document.getElementById("chat").innerHTML +=
    `<p class="system">${data.message}</p>`;
});

socket.on("receive_message", data => {
  document.getElementById("chat").innerHTML +=
    `<p class="message"><strong>${data.username}:</strong> ${data.message}</p>`;
});


function sendMessage() {
  const input = document.getElementById("message");
  socket.emit("send_message", { message: input.value });
  input.value = "";
}
