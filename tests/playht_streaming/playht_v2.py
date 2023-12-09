import os 
from dotenv import load_dotenv
from flask import Flask, Response, render_template, stream_with_context, request
import requests
import requests
import json

load_dotenv()
userid = os.getenv("PLAYHT_USERID")
apikey = os.getenv("PLAYHT_SECRET")

########################################################################

app = Flask(__name__)

@app.route('/audio/create')
def stream_page():
    return render_template('stream.html')

@app.route('/audio/stream-data')
def stream():

    text = request.args.get('text', 'Default text')  # Fallback to default text if not provided
    voice = request.args.get('voice', 'Default voice')  # Fallback to default voice if not provided

    def event_stream():
        url = "https://api.play.ht/api/v2/tts"
        payload = {
            "text": text,       # "Haunts",
            "voice": voice,     # "s3://voice-cloning-zero-shot/09b5c0cc-a8f4-4450-aaab-3657b9965d0b/podcaster/manifest.json",
            "output_format": "mp3",
            "voice_engine": "PlayHT2.0"
        }
        headers = {
            "accept": "text/event-stream",
            "content-type": "application/json",
            "Authorization": "Bearer " + apikey,
            "X-USER-ID": userid
        }
        with requests.post(url, stream=True, headers=headers, json=payload) as response:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    yield f"data: {decoded_line}\n\n"

    return Response(
        stream_with_context(event_stream()),
        content_type='text/event-stream'
        )

@app.route('/audio/stream-data/response', methods=['POST'])
def stream_response():
    body = request.get_json()
    print('Response from server: ', body)
    return render_template('stream.html', server_body=body)

if __name__ == '__main__':
    app.run(debug=True)