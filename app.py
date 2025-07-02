from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    from math import ceil
    page = request.args.get('page', 1, type=int)
    per_page = 12
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    images = [f for f in files if f.split('.')[-1].lower() in ['png', 'jpg', 'jpeg', 'gif']]
    videos = [f for f in files if f.split('.')[-1].lower() in ['mp4', 'mov', 'avi']]
    images.sort(reverse=True)
    total = len(images)
    pages = ceil(total / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    images_paginated = images[start:end]
    return render_template('index.html', images=images_paginated, videos=videos, page=page, pages=pages)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index'))
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
