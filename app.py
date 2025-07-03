
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import os
from werkzeug.utils import secure_filename
import json
from datetime import datetime

USERNAME = 'admin'
PASSWORD = '123456'

EVENTS_FILE = 'static/events.json'

app = Flask(__name__)
app.secret_key = 'mustshow-2025-07-02-unique-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['DESC_FILE'] = 'static/uploads/descriptions.json'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webm'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_albums():
    base = app.config['UPLOAD_FOLDER']
    return [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]

def get_files_in_album(album):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], album)
    if not os.path.exists(folder):
        return []
    return [f for f in os.listdir(folder) if allowed_file(f)]

def get_images_in_album(album):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], album)
    if not os.path.exists(folder):
        return []
    return [f for f in os.listdir(folder) if f.split('.')[-1].lower() in ['png', 'jpg', 'jpeg', 'gif']]

def get_videos_in_album(album):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], album)
    if not os.path.exists(folder):
        return []
    return [f for f in os.listdir(folder) if f.split('.')[-1].lower() in ['mp4', 'mov', 'avi', 'webm']]

def load_descriptions():
    desc_file = app.config['DESC_FILE']
    if os.path.exists(desc_file):
        with open(desc_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_descriptions(desc):
    desc_file = app.config['DESC_FILE']
    with open(desc_file, 'w', encoding='utf-8') as f:
        json.dump(desc, f, ensure_ascii=False, indent=2)

def load_events():
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_events(events):
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)        

@app.route('/')
@login_required
def index():
    albums = get_albums()
    album_covers = {}
    photo_albums = []
    video_albums = []
    for album in albums:
        files = get_files_in_album(album)
        if files:
            cover = f"/static/uploads/{album}/{files[0]}"
            album_covers[album] = cover
            ext = files[0].rsplit('.', 1)[-1].lower()
            if ext in ['mp4', 'mov', 'avi', 'webm']:
                video_albums.append(album)
            else:
                photo_albums.append(album)
        else:
            album_covers[album] = None
    events = load_events()  # 新增
    return render_template(
        'index.html',
        photo_albums=photo_albums,
        video_albums=video_albums,
        album_covers=album_covers,
        events=events  # 新增
    )

@app.route('/upload_photo', methods=['GET', 'POST'])
@login_required
def upload_photo():
    albums = get_albums()
    album_covers = {}
    for album in albums:
        files = get_files_in_album(album)
        if files:
            album_covers[album] = f"/static/uploads/{album}/{files[0]}"
        else:
            album_covers[album] = None

    if request.method == 'POST':
        album = request.form.get('album') or '光影留痕'
        new_album = request.form.get('new_album', '').strip()
        if new_album:
            album = new_album
        album_folder = os.path.join(app.config['UPLOAD_FOLDER'], album)
        os.makedirs(album_folder, exist_ok=True)
        desc_text = request.form.get('desc', '').strip()

        # 支持批量上传和单张上传
        files = request.files.getlist('file')
        if not files or (len(files) == 1 and files[0].filename == ''):
            return redirect(request.url)

        desc = load_descriptions()
        for file in files:
            if file and file.filename and file.filename.rsplit('.', 1)[-1].lower() in ['png', 'jpg', 'jpeg', 'gif']:
                filename = secure_filename(file.filename)
                save_path = os.path.join(album_folder, filename)
                # 防止同名覆盖
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(save_path):
                    filename = f"{base}_{counter}{ext}"
                    save_path = os.path.join(album_folder, filename)
                    counter += 1
                file.save(save_path)
                if desc_text:
                    desc[f"{album}/{filename}"] = desc_text
        save_descriptions(desc)
        return redirect(url_for('album_view', album=album))

    # 只传递图片相册用于下拉
    photo_albums = [a for a in albums if any(
        img.rsplit('.', 1)[-1].lower() not in ['mp4', 'mov', 'avi', 'webm']
        for img in get_files_in_album(a)
    )]
    return render_template(
        'upload_photo.html',
        photo_albums=photo_albums,
        album_covers=album_covers
    )

@app.route('/upload_video', methods=['GET', 'POST'])
@login_required
def upload_video():
    albums = get_albums()
    album_covers = {}
    for album in albums:
        files = get_files_in_album(album)
        if files:
            album_covers[album] = f"/static/uploads/{album}/{files[0]}"
        else:
            album_covers[album] = None
    if request.method == 'POST':
        album = request.form.get('album') or '师生映像馆'
        new_album = request.form.get('new_album', '').strip()
        if new_album:
            album = new_album
        album_folder = os.path.join(app.config['UPLOAD_FOLDER'], album)
        os.makedirs(album_folder, exist_ok=True)
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        desc_text = request.form.get('desc', '').strip()
        if file.filename == '':
            return redirect(request.url)
        # 只允许视频
        if file and file.filename.rsplit('.', 1)[-1].lower() in ['mp4', 'mov', 'avi', 'webm']:
            filename = secure_filename(file.filename)
            file.save(os.path.join(album_folder, filename))
            if desc_text:
                desc = load_descriptions()
                desc[f"{album}/{filename}"] = desc_text
                save_descriptions(desc)
            return redirect(url_for('album_view', album=album))
    # 只传递视频相册用于下拉
    video_albums = [a for a in albums if any(
        img.rsplit('.', 1)[-1].lower() in ['mp4', 'mov', 'avi', 'webm']
        for img in get_files_in_album(a)
    )]
    return render_template(
        'upload_video.html',
        video_albums=video_albums,
        album_covers=album_covers
    )

@app.route('/album/<album>')
@login_required
def album_view(album):
    images = get_files_in_album(album)
    desc = load_descriptions()
    image_desc = {img: desc.get(f"{album}/{img}", "") for img in images}
    return render_template('album.html', album=album, images=images, image_desc=image_desc)

@app.route('/desc/<album>/<img>', methods=['POST'])
@login_required
def update_desc(album, img):
    desc = load_descriptions()
    text = request.form.get('desc', '')
    desc[f"{album}/{img}"] = text
    save_descriptions(desc)
    return '', 204

@app.route('/delete/<album>/<filename>', methods=['POST'])
@login_required
def delete_file(album, filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], album, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    # 删除描述
    desc = load_descriptions()
    desc.pop(f"{album}/{filename}", None)
    save_descriptions(desc)
    return redirect(url_for('album_view', album=album))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('已退出登录', 'info')
    return redirect(url_for('login'))


@app.route('/events', methods=['GET', 'POST'])
@login_required
def events():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if title and content:
            events = load_events()
            events.insert(0, {'title': title, 'content': content, 'date': datetime.now().strftime('%Y-%m-%d')})
            save_events(events)
    events = load_events()
    return render_template('events.html', events=events)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    events = load_events()
    if 0 <= event_id < len(events):
        events.pop(event_id)
        save_events(events)
    return redirect(url_for('events'))

@app.route('/event/<int:event_id>', endpoint='view_event')
@login_required
def view_event(event_id):
    events = load_events()
    if 0 <= event_id < len(events):
        event = events[event_id]
        return render_template('event_view.html', event=event)
    else:
        flash('未找到该记事', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5023)