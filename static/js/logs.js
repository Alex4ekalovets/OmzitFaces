let socket;
const logs = document.getElementById("logs");

socket = new WebSocket(`ws://localhost:8000/ws`);
socket.onmessage = function(event) {
    logs.innerHTML += event.data + "<br>";
    logs.scrollTop = logs.scrollHeight;
};