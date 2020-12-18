from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from cv2 import cv2
import base64
import numpy as np
import os
from homography import homography

app = Flask(__name__)
app.secret_key = '123141421sadqweqed'
UPLOAD_FOLDER = '/tmp/'
RESULTS_FOLDER = '/tmp/results/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

@app.route('/')
def home_page():
    return render_template('home.html')

# fix refresh problem later
@app.route('/transform', methods=['GET','POST'])
def transform_page():
    if request.method == 'POST':
        file = request.files['video']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        cap = cv2.VideoCapture(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        frame = cap.read()[1]
        frame_buff = cv2.imencode('.jpg', frame)[1]
        b64 = base64.b64encode(frame_buff)
        return render_template('getfourpoints.html', frame=b64, filename=filename)
        
    return render_template('transform.html')

@app.route('/transform_success', methods=['POST'])
def perform_homography():
    video = request.form['filename'][:-1]
    outputdetect = 'detect.avi'
    outputgraph = 'graph.avi'
    yolo = os.path.abspath('/home/irvin/Documents/code/darknet')
    pts_src = []
    points = [float(x) for x in request.form['points'].split(',')]
    for i in range(0, len(points),2):
        pt = [points[i], points[i+1]]
        pts_src.append(pt)
    pts_src = np.vstack(pts_src).astype(float)
    homography(video, outputdetect, outputgraph, yolo, pts_src)
    
    return render_template('results.html')