import os
from flask import Flask, request, jsonify
from pyrogram import Client

app = Flask(__name__)

# Public API Credentials
API_ID = int(os.environ.get("API_ID", 2040))
API_HASH = os.environ.get("API_HASH", "b18441a1ff607e10a989891a5462e627")
SESSION_STRING = os.environ.get("SESSION_STRING")  # Session string user account login ke liye
CHANNEL_ID = os.environ.get("CHANNEL_ID", "me")

@app.route("/", methods=["GET"])
def home():
    return "Telegram 2GB Client Worker is Running Successfully!"

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    filename = file.filename
    file_path = os.path.join("/tmp", filename)
    file.save(file_path)

    # Pyrogram Client (User API / 2GB Support)
    client = Client(
        "uploader_session",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
        in_memory=True
    )

    try:
        client.start()
        
        # 2GB tak ki file upload karne ke liye send_document
        sent_message = client.send_document(
            chat_id=CHANNEL_ID,
            document=file_path,
            caption=f"Uploaded via Cloudin: {filename}"
        )
        
        file_id = sent_message.document.file_id
        client.stop()

        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({
            "status": "success",
            "file_name": filename,
            "file_id": file_id,
            "message": "File successfully uploaded via Telegram User API!"
        })

    except Exception as e:
        if client.is_connected:
            client.stop()
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
