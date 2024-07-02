import os
import tempfile
import requests
from flask import Flask, request, jsonify
from pyrogram import Client

app = Flask(__name__)

API_ID = 2929398
API_HASH = "9b0761e56d3d0f89d14563a7e1d29779"
BOT_TOKEN = "5875384990:AAEtsupz8Ln4QCPxi6Dah6Uhjyx4uIS7dUQ"
CHAT_ID = 1218619440
telegram = Client("betabot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
telegram.start()
@app.route('/release', methods=['POST'])
def handle_release():
    data = request.json
    release_notes = data.get('release_notes')
    download_url = data.get('download_url')
    uploaded_at = data.get('uploaded_at')
    version = data.get('version')

    if not all([release_notes, download_url, uploaded_at]):
        return jsonify({"error": "Missing required fields"}), 400

    caption = f"🚀 New Release {version}!!\n\n📝 Release Notes:\n{release_notes}\n\n⏰ Uploaded at: {uploaded_at}"

    try:
        send_telegram_message(download_url, caption)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def send_telegram_message(file_url, caption):
    with tempfile.NamedTemporaryFile(suffix='.apk', delete=False) as temp_file:
        try:
            # Send initial message
            initial_message = telegram.send_message(CHAT_ID, "Beta received, downloading and uploading..")
            
            # Download the file
            response = requests.get(file_url)
            response.raise_for_status()
            temp_file.write(response.content)
            temp_file.flush()

            # Send the file
            telegram.send_document(
                chat_id=CHAT_ID,
                document=temp_file.name,
                file_name="app.apk",
                caption=caption
            )
            
            # Delete the initial message
            telegram.delete_messages(CHAT_ID, initial_message.id)
        except requests.RequestException as e:
            raise Exception(f"Failed to download file: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to send file: {str(e)}")
        finally:
            # Close and remove the temporary file
            temp_file.close()
            os.unlink(temp_file.name)
            telegram.stop()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
