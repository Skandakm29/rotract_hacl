from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
from collections import deque
import threading
import queue

app = Flask(__name__)

# Store last 5 actions
history = deque(maxlen=5)
button_counts = {"VOICE": 0, "MEDICINE": 0, "CAMERA": 0, "MUSIC": 0, "HANUMAN_CHALISA": 0}

# TTS message queue
action_queue = queue.Queue()

def action_worker():
    while True:
        msg = action_queue.get()
        print("🔊 Action:", msg)
        action_queue.task_done()

threading.Thread(target=action_worker, daemon=True).start()

@app.route('/')
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sahayak Button Dashboard</title>
        <style>
            body { font-family: Arial; padding: 2rem; background: #f9f9f9; }
            .box { border: 1px solid #ccc; padding: 1rem; border-radius: 10px; width: 350px; background: white; margin-bottom: 1rem; }
            .type { font-weight: bold; color: #0077cc; }
            .log { margin-top: 2rem; }
            .history { font-family: monospace; background: #f3f3f3; padding: 1rem; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>🧓 Sahayak Button Dashboard</h1>

        <div class="box">
            <h3>📍 Latest Action</h3>
            <p><strong>Type:</strong> <span id="type">-</span></p>
            <p><strong>Message:</strong> <span id="message">-</span></p>
            <p><strong>Timestamp:</strong> <span id="time">-</span></p>
        </div>

        <div class="box">
            <h3>📊 Button Count</h3>
            <ul>
                <li>🔊 VOICE: <span id="VOICE">0</span></li>
                <li>💊 MEDICINE: <span id="MEDICINE">0</span></li>
                <li>📷 CAMERA: <span id="CAMERA">0</span></li>
                <li>🎶 MUSIC: <span id="MUSIC">0</span></li>
                <li>🙏 HANUMAN_CHALISA: <span id="HANUMAN_CHALISA">0</span></li>
            </ul>
        </div>

        <div class="box log">
            <h3>📝 Last 5 Button Presses</h3>
            <div class="history" id="history"></div>
        </div>

        <audio id="chalisaAudio" src="/static/hanuman-chalisa.mp3"></audio>

        <script>
            let lastSpokenMessage = "";

            function speak(message) {
                const synth = window.speechSynthesis;
                const utterance = new SpeechSynthesisUtterance(message);
                synth.cancel();
                synth.speak(utterance);
            }

            function getMessageFromType(type) {
                switch (type) {
                    case "VOICE": return "Hello from the computer. I am your assistant.";
                    case "MEDICINE": return "Reminder. It's time to take your medicine.";
                    case "CAMERA": return "Camera button pressed. Opening the camera.";
                    case "MUSIC": return "Playing your favorite relaxing music.";
                    case "HANUMAN_CHALISA": return "PLAY_AUDIO";
                    default: return "Unknown action.";
                }
            }

            function updateDashboard() {
                fetch('/latest')
                    .then(res => res.json())
                    .then(data => {
                        const { type, message, timestamp } = data.latest;

                        document.getElementById('type').innerText = type;
                        document.getElementById('message').innerText = message;
                        document.getElementById('time').innerText = timestamp;

                        for (const key in data.counts) {
                            document.getElementById(key).innerText = data.counts[key];
                        }

                        let logHTML = "";
                        data.history.slice().reverse().forEach(item => {
                            logHTML += `🟢 [${item.timestamp}] ${item.type}<br>`;
                        });
                        document.getElementById('history').innerHTML = logHTML;

                        if (message !== lastSpokenMessage) {
                            const textToSpeak = getMessageFromType(type);
                            if (textToSpeak === "PLAY_AUDIO") {
                                const audio = document.getElementById("chalisaAudio");
                                audio.currentTime = 0;
                                audio.play().catch(err => console.error("🔇 Audio error:", err));
                            } else {
                                speak(textToSpeak);
                            }
                            lastSpokenMessage = message;
                        }
                    });
            }

            setInterval(updateDashboard, 2000);
            updateDashboard();
        </script>
    </body>
    </html>
    """)

@app.route('/emergency', methods=['POST'])
def emergency():
    data = request.json
    action_type = data.get("type", "")
    timestamp = datetime.now().isoformat()

    message = f"{action_type} button pressed on ESP32"
    new_action = {"type": action_type, "message": message, "timestamp": timestamp}

    history.append(new_action)
    if action_type in button_counts:
        button_counts[action_type] += 1

    # Log action (for debug)
    action_queue.put(f"Triggered: {action_type}")

    return {"status": "received"}

@app.route('/latest')
def latest():
    latest_action = history[-1] if history else {"type": "-", "message": "-", "timestamp": "-"}
    return jsonify({
        "latest": latest_action,
        "counts": button_counts,
        "history": list(history)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
