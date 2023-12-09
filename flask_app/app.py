from flask import Flask, render_template, request
from  sqlalchemy.sql.expression import func
from werkzeug.utils import secure_filename
from db_model.db import DataEntry, Audio, get_session, init_db  # Import from db.py
from utils.s3 import s3, s3_get_image_sounds, s3_get_mp4_files
from utils.playht import generate_voice
from utils.sadtalker import create_video
import json
import pandas as pd

app = Flask(__name__)
app.secret_key = 'super secret key'

init_db() # Initialize the database

s3_client = s3 # Initialize the s3 client
BUCKET_NAME = 'iitg-mvp' # Replace with your bucket name

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/view1')
def view1():
    return render_template('view1/view1.html')

@app.route('/view1/audio/table', methods=['GET', 'POST'])
def audio_table():
    row_id = request.form['row_id']
    session = get_session()
    # Query to join DataEntry and Audio
    query = session.query(DataEntry, Audio).join(Audio, DataEntry.id == Audio.data_entry_id).filter(DataEntry.id == row_id)
    data_dict = []
    # Execute the query and process results
    for data_entry, audio in query.all():
        # add to data_dict
        data_dict.append({
            'text_content': data_entry.text_content,
            'audio_url': audio.audio_url
        })
        # print(f"Text Content: {data_entry.text_content}, Audio URL: {audio.audio_url}")
    print('data_dict:', data_dict)
    session.close()
    return render_template(
        'view1/audio_table_modal.html', 
        data_dict=data_dict,
    )

@app.route('/view1/form', methods=['GET'])
def view_form_audio():
    return render_template('view1/create_text_modal.html')

@app.route('/view1/image_upload_form', methods=['GET'])
def image_upload_form():
    return render_template('view1/create_image_modal.html')

@app.route('/view1/text/upload', methods=['POST'])
def submit_audio():
    text_input = request.form['text_input']
    print('text inputted:', text_input)
    session = get_session()
    data_entry = DataEntry(
        user_id='mvp_001',
        data_type='Text', 
        text_content=text_input, 
        data_url=''
    )
    try:
        session.add(data_entry)
        session.commit()
    except:
        session.rollback()
        raise
    session.close()
    print('data entry added to database')
    return render_template('view1/submitted_modal.html', data=text_input)

@app.route('/view1/audio/input', methods=['GET', 'POST'])
def create_audio():
    row_id = request.form['row_id']
    print('row_id:', row_id)
    session = get_session()
    data_entry = session.query(DataEntry).filter(DataEntry.id == row_id).first()
    print('Data entry: ', data_entry)
    return render_template(
        'view1/create_audio_modal.html',
        data=data_entry
        )

@app.route('/view1/audio/create', methods=['POST'])
def submit_audio_file():
    row_id = request.form['row_id']
    speaker_type = request.form['speaker_type']
    print('Server received: row_id:', row_id, 'speaker_type:', speaker_type)
    session = get_session()
    data_entry = session.query(DataEntry).filter(DataEntry.id == row_id).first()
    text_content = data_entry.text_content
    playht_audio_url = generate_voice(speaker_type, text_content)  ## send to playht
    print('playht_audio_url:', playht_audio_url)
    # ## upload to s3
    # audio_url = s3_upload_sound(row_id, playht_audio_url)
    # ## add s3 url path to audio_url
    # audio_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{audio_url}"
    ## save to database in Audio table, providing the row_id as the data_entry_id
    try:
        new_audio = Audio(audio_url=playht_audio_url, data_entry_id=row_id)
        session.add(new_audio)
        session.commit()
        session.close()
    except:
        session.rollback()
        raise
    print('audio saved to database')
    return render_template('view1/submitted_modal.html', data=playht_audio_url)

@app.route('/view1/image/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        data = {'status': '400', 'message': 'No file part'}
        return render_template('view1/submitted_modal.html', data=data)

    file = request.files['file']
    if file.filename == '':
        data = {'status': '400', 'message': 'No selected file'}
        return render_template('view1/submitted_modal.html', data=data)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        s3_client.upload_fileobj(file, BUCKET_NAME, filename)
        # Construct the file URL
        file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
        # Save the file URL to the database along with meta data
        session = get_session() # Get a new session
        data_entry = DataEntry(
            user_id='mvp_001',
            data_type='Photo', 
            text_content='Photo from User X', 
            data_url=file_url
        )
        try:
            session.add(data_entry)
            session.commit()
        except:
            session.rollback()
            raise
        session.close()
        print('file uploaded successfully to database and s3')
        data = {
            'status': '200', 
            'message': 'File successfully uploaded',
            'file_url': file_url
            }
        return render_template('view1/submitted_modal.html', data=data)
    
    else:
        data = {'status': '400', 'message': 'File type not allowed'}
        return render_template('view1/submitted_modal.html', data=data)


@app.route('/view1/text/delete', methods=['POST'])
def delete_text():
    row_id = request.form['row_id']
    print('row_id:', row_id)
    session = get_session()
    try:
        session.query(DataEntry).filter(DataEntry.id == row_id).delete()
        session.commit()
    except:
        session.rollback()
        raise
    session.close()
    print({
            'status': '200', 
            'message': 'Text successfully deleted',
            'row_id': row_id
        })
    return render_template('view1/view1.html')

@app.route('/view1/image/delete', methods=['POST'])
def delete_file():
    file_url = request.form['data_url']
    file_name = file_url.split('/')[-1]
    print('file_url:', file_name)
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=file_name)
    session = get_session()
    try:
        session.query(DataEntry).filter(DataEntry.data_url == file_url).delete()
        session.commit()
    except:
        session.rollback()
        raise
    session.close()
    print({
            'status': '200', 
            'message': 'File successfully deleted',
            'file_url': file_url
        })
    return render_template('view1/view1.html')



@app.route('/view2', methods=['GET', 'POST'])
def view2():
    session = get_session()  # Get a new session

    all_data = session.query(DataEntry).all()
    text_data = [(item.text_content, item.data_url) for item in all_data if item.data_type == 'Text']
    photo_data = [(item.text_content, item.data_url) for item in all_data if item.data_type == 'Photo']
    
    # Query to join DataEntry and Audio
    query = session.query(DataEntry, Audio).join(Audio, DataEntry.id == Audio.data_entry_id)
    data_dict = []
    # Execute the query and process results
    for data_entry, audio in query.all():
        # add to data_dict
        data_dict.append({
            'text_content': data_entry.text_content,
            'audio_url': audio.audio_url
        })
        # print(f"Text Content: {data_entry.text_content}, Audio URL: {audio.audio_url}")
    print('data_dict:', data_dict)
    session.close()  # Don't forget to close the session

    return render_template(
        'view2/view2.html', 
        data_dict=data_dict,
        text_data=text_data, 
        photo_data=photo_data
    )

@app.route('/view2/submit', methods=['POST'])
def submit():
    print(request.form)
    # data = json.dumps(request.form)

    audio_selection = request.form['audio_selection']
    photo_selection = request.form['photo_selection']

    print('audio_selection:', audio_selection)
    print('photo_selection:', photo_selection)

    ## create video 
    results = create_video(photo_selection, audio_selection)

    return render_template('view2/submitted_modal.html', data=results)

@app.route('/view3')
def view3():
    s3_video_urls = s3_get_mp4_files()
    print('s3_video_urls:', s3_video_urls)
    return render_template(
        'view3/view3.html'
        , s3_video_urls=s3_video_urls
    )


@app.route('/data/view1', methods=['GET'])
def data():
    if request.headers.get('HX-Request'):

        session = get_session() # Get a new session
        # data = session.query(DataEntry).order_by(func.random()).limit(5).all()
        data = session.query(DataEntry).all()
        session.close() # Don't forget to close the session

        ## get s3 image and sound urls
        s3_image_urls, s3_sound_urls = s3_get_image_sounds()
        print('s3_image_urls:', s3_image_urls)
        print('s3_sound_urls:', s3_sound_urls)

        return render_template('view1/data_table.html', data=data)
    else:
        return render_template('view1.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
