from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from cv2 import cv2
import base64
import numpy as np
import os
from homography import homography

app = Flask(__name__)
app.secret_key = '123141421sadqweqed'
UPLOAD_FOLDER = 'tmp/input/'
RESULTS_FOLDER = 'tmp/output/'
YOLO_FOLDER = 'yolo/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['YOLO_FOLDER'] = YOLO_FOLDER

@app.route('/')
def home_page():
    return render_template('home.html')

# fix refresh problem later
@app.route('/transform', methods=['GET','POST'])
def transform_page():
    if request.method == 'POST':
        file = request.files['video']
        filename = secure_filename(file.filename)
        print(filename)
        filepath = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print("file saved")
        cap = cv2.VideoCapture(filepath)
        frame = cap.read()[1]
        frame_buff = cv2.imencode('.jpg', frame)[1]
        b64 = base64.b64encode(frame_buff)
        return render_template('getfourpoints.html', frame=b64, filename=filename)
        
    return render_template('transform.html')

@app.route('/transform_success', methods=['POST'])
def perform_homography():
    filename = request.form['filename'][:-1]
    resultspath = os.path.join(app.root_path, app.config['RESULTS_FOLDER'])
    video = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename)
    yolo = os.path.join(app.root_path, app.config['YOLO_FOLDER'])
    outputdetect = os.path.join(resultspath,'detect.avi')
    outputgraph = os.path.join(resultspath,'graph.avi')
    pts_src = []
    points = [float(x) for x in request.form['points'].split(',')]
    for i in range(0, len(points),2):
        pt = [points[i], points[i+1]]
        pts_src.append(pt)
    pts_src = np.vstack(pts_src).astype(float)
    homography(video, outputdetect, outputgraph, yolo, pts_src)
    
    return render_template('results.html', detect='detect.avi', graph='graph.avi')

@app.route('/download/<path:filename>')
def get_videos(filename):
    path = os.path.join(app.root_path, app.config['RESULTS_FOLDER'])
    return send_from_directory(path, filename, as_attachment=True)
