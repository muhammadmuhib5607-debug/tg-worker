import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

TELEGRAM_BOT_TOKEN = "8778173164:AAHYdfF33Pv2VwolQ2ynltEk2N3j1c8djh0"
TELEGRAM_CHAT_ID = "-1004358868963"

@app.route('/upload', methods=['POST'])
def upload_chunk():
    try:
        upload_id = request.form.get('upload_id')
        file_name = request.form.get('file_name')
        chunk_index = int(request.form.get('chunk_index', 0))
        total_chunks = int(request.form.get('total_chunks', 1))
        username = request.form.get('username', 'user')
        callback_url = request.form.get('callback_url')
        
        file_chunk = request.files.get('file_chunk')
        if not file_chunk:
            return jsonify({'status': 'error', 'message': 'No chunk provided'}), 400

        temp_dir = f"/tmp/chunks_{upload_id}"
        os.makedirs(temp_dir, exist_ok=True)
        chunk_path = os.path.join(temp_dir, f"chunk_{chunk_index}")
        file_chunk.save(chunk_path)

        if chunk_index + 1 == total_chunks:
            merged_path = os.path.join(temp_dir, f"merged_{file_name}")
            with open(merged_path, 'wb') as outfile:
                for i in range(total_chunks):
                    c_path = os.path.join(temp_dir, f"chunk_{i}")
                    if os.path.exists(c_path):
                        with open(c_path, 'rb') as infile:
                            outfile.write(infile.read())
                        os.remove(c_path)

            file_size_bytes = os.path.getsize(merged_path)
            if file_size_bytes < 1024:
                formatted_size = f"{file_size_bytes} B"
            elif file_size_bytes < 1048576:
                formatted_size = f"{round(file_size_bytes / 1024, 2)} KB"
            else:
                formatted_size = f"{round(file_size_bytes / 1048576, 2)} MB"

            ext = file_name.split('.')[-1].lower()
            is_video = ext in ['mp4', 'mkv', 'webm', 'avi', 'mov', '3gp']
            tg_method = "sendVideo" if is_video else "sendDocument"
            field_name = "video" if is_video else "document"

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{tg_method}"
            with open(merged_path, 'rb') as f:
                files = {field_name: (file_name, f)}
                data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': file_name}
                # Timeout extended to 1200 seconds for heavy 500MB videos
                response = requests.post(url, data=data, files=files, timeout=1200)

            if os.path.exists(merged_path):
                os.remove(merged_path)
            
            res_json = response.json()
            if res_json.get('ok'):
                result_data = res_json['result']
                file_id = result_data.get('document', {}).get('file_id') or result_data.get('video', {}).get('file_id') or result_data.get('audio', {}).get('file_id')
                
                if callback_url and file_id:
                    try:
                        requests.post(callback_url, data={
                            'sync_secret': 'MuhibSecretPassKey2026',
                            'username': username,
                            'file_name': file_name,
                            'ext': ext,
                            'size': formatted_size,
                            'file_id': file_id
                        }, timeout=20)
                    except Exception as cb_err:
                        pass

                return jsonify({'status': 'success', 'file_id': file_id})
            else:
                return jsonify({'status': 'error', 'message': res_json.get('description', 'Telegram error')}), 400

        return jsonify({'status': 'next_chunk'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
