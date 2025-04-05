from flask import Flask, request
import pyttsx3
import cv2
import threading
import queue
import random
import os
from playsound import playsound  # Only needed if using mp3 playback

app = Flask(__name__)

# Initialize pyttsx3 and TTS queue
engine = pyttsx3.init()
tts_queue = queue.Queue()

def tts_worker():
    while True:
        text = tts_queue.get()
        if text is None:
            break
        engine.say(text)
        engine.runAndWait()
        tts_queue.task_done()

# Start background TTS thread
threading.Thread(target=tts_worker, daemon=True).start()

@app.route('/emergency', methods=['POST'])
def emergency():
    data = request.json
    action_type = data.get("type", "")
    location = data.get("location", "Unknown")

    print("📦 Received POST from ESP32")
    print(f"🔘 Type: {action_type}")
    print(f"📍 Location: {location}")

    if action_type == "VOICE":
        print("🔊 Queuing voice message...")
        tts_queue.put("Hello, I am your Sahayak assistant. How can I help you?")

    elif action_type == "MEDICINE":
        print("💊 Medication reminder activated.")
        tts_queue.put("It is time to take your medicine. Please don't forget.")

    elif action_type == "CAMERA":
        print("📷 Opening webcam (press 'q' to close)...")
        threading.Thread(target=open_camera).start()

    elif action_type == "QUOTE":
        quote = get_daily_quote()
        print("📖 Daily Quote:", quote)
        tts_queue.put(quote)

    elif action_type == "HANUMAN_CHALISA":
        print("🙏 Playing Hanuman Chalisa MP3...")
        audio_path = r"C:\Users\skand\OneDrive\Desktop\rotract_hack\hanuman-chalisa-42629.mp3"
        threading.Thread(target=play_audio, args=(audio_path,)).start()

    else:
        print("⚠️ Unknown type received.")

    return {"status": "received"}

def get_daily_quote():
    quotes = [
        "You are never too old to set another goal or to dream a new dream.",
        "Health is the greatest gift. Peace is the ultimate wealth.",
        "Smile, and let the world wonder why.",
        "Every day is a new beginning. Make it count.",
        "This moment is all you truly have. Enjoy it."
    ]
    return random.choice(quotes)

def open_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not access webcam.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("ESP32 Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("📷 Camera closed.")

# Final: Unified audio player function
def play_audio(file_path):
    try:
        playsound(file_path)
    except Exception as e:
        print("⚠️ Could not play audio file:", e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
