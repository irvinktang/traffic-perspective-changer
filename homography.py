import numpy as np
import cv2 
import imutils
import time
import os

def homography(input_video, outputdetect, outputgraph, yolo, pts_src):
    # load COCO class labels
    labelsPath = os.path.sep.join([yolo, "coco.names"])
    LABELS = open(labelsPath).read().strip().split("\n")

    # assigning random colors to represent classes
    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(LABELS), 3), dtype="uint8")

    weightsPath = os.path.sep.join([yolo, "yolov3.weights"])
    configPath = os.path.sep.join([yolo, "yolov3.cfg"])

    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
    layernames = net.getLayerNames()
    layernames = [layernames[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    # initialize video stream
    print("[INFO] loading file from disk...")
    cap = cv2.VideoCapture(input_video)
    writerdetect = None
    writergraph = None
    width, height = (None, None)

    # try to determine the total number of frames in the video file
    try:
        prop = cv2.cv.CV_CAP_PROP_FRAME_COUNT if imutils.is_cv2() \
            else cv2.CAP_PROP_FRAME_COUNT
        total = int(cap.get(prop))
        print("[INFO] {} total frames in video".format(total))
    # an error occurred while trying to determine the total
    # number of frames in the video file
    except:
        print("[INFO] could not determine # of frames in video")
        print("[INFO] no approx. completion time can be provided")
        total = -1


    if not cap.isOpened():
        print("[ERROR] could not open file")
    else:
        # get homography matrix 
        ret, frame = cap.read()

        # pass these in next time as a command line argument
        newsize = (3000,3000,3)
        size = (50,50,3) 

        im_dst = np.zeros(newsize, np.uint8)

        # points the source will get mapped to
        pts_dst = np.array([
            [newsize[0]/2-size[0]/2,newsize[0]/2-size[0]/2],
            [newsize[0]/2+size[0]/2,newsize[0]/2-size[0]/2],
            [newsize[0]/2+size[0]/2,newsize[0]/2+size[0]/2],
            [newsize[0]/2-size[0]/2,newsize[0]/2+size[0]/2],
        ], dtype=float)

        h, status = cv2.findHomography(pts_src, pts_dst)

        # get size of frame 
        frame_size = frame.shape
        
        original_corners = np.array([
            [0,0], [0, frame_size[0]], [frame_size[1], frame_size[0]], [frame_size[1], 0]
        ])
        new_corners = np.empty([0,2])

        for corner in original_corners:
            new_corner = np.dot(np.append(corner, [1]), h)
            new_corners = np.append(new_corners, np.ceil([new_corner[:2]]), axis=0)

        new_height = np.max(new_corners[:,1])-np.min(new_corners[:,1])
        new_width = np.max(new_corners[:,0])-np.min(new_corners[:,0])

        newsize = (int(new_width), int(new_height), 3)

        # translation matrix to get points within view
        # calculate this based on warped perspective next time
        t = np.array([
            [1,0,-np.abs(np.min(new_corners[:,0]))],
            [0,1,-np.abs(np.min(new_corners[:,1]))],
            [0,0,1]
        ])

        # total transformation matrix
        transform = np.dot(t,h)

        # looping over frames of video
        while True:
            # read next frame in video
            ret, frame = cap.read()

            # create black background to project points onto
            blackimage = np.full(newsize,[0,0,0],np.uint8)

            if not ret:
                break
            
            if width is None or height is None:
                height, width = frame.shape[:2]

            im_dst = cv2.warpPerspective(frame, transform, newsize[0:2])
            newimage = cv2.resize(im_dst, (width//2, height//2))

            # perform forward pass of YOLO object detector
            # gives bounding boxes and associate probabilities
            blob = cv2.dnn.blobFromImage(
                frame, 1/255.0, (416, 416), swapRB=True, crop=False)
            net.setInput(blob)
            start = time.time()
            layerOutputs = net.forward(layernames)
            end = time.time()

            # initialize lists of bounding boxes, confidences, class IDs, and centers
            boxes = []
            confidences = []
            classIDs = []
            centers = []

            for output in layerOutputs:
                for detection in output:
                    scores = detection[5:]
                    classID = np.argmax(scores)
                    confidence = scores[classID]

                    # filter out weak predictions
                    if confidence > 0.5:
                        # YOLO returns the center (x,y) coordinates of the bounding box
                        # followed by the boxes' width and height
                        box = detection[0:4] * np.array([width, height, width, height])
                        (centerX, centerY, boxW, boxH) = box.astype("int")

                        # calculate top left corner of bounding box
                        x = int(centerX - (boxW / 2))
                        y = int(centerY - (boxH / 2))

                        centers.append((centerX, centerY))

                        boxes.append([x, y, int(boxW), int(boxH)])
                        confidences.append(float(confidence))
                        classIDs.append(classID)

            # apply non-maxima suppression to suppress weak, overlapping bounding boxes
            # nms: basically a sort of filter
            idxs = cv2.dnn.NMSBoxes(
                boxes, confidences, 0.5, 0.3)

            # ensure at least one detection exists
            if len(idxs) > 0:
                for i in idxs.flatten():
                    # extract bounding box coordinates
                    x, y = (boxes[i][0], boxes[i][1])
                    w, h = (boxes[i][2], boxes[i][3])

                    # draw bounding box and label frame
                    color = [int(c) for c in COLORS[classIDs[i]]]
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    text = "{}: {:.4f}".format(LABELS[classIDs[i]], confidences[i])
                    cv2.putText(frame, text, (x, y-5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                    # apply homography on homogeneous center point
                    centerh = np.array([centers[i][0], centers[i][1], 1])
                    newcenter = np.dot(transform, centerh)
                    cv2.circle(blackimage, 
                        (np.ceil(newcenter[0]/newcenter[2]).astype(int), 
                        np.ceil(newcenter[1]/newcenter[2]).astype(int)), 15, color, -1)
            
            # resizing blackimage so that viewable area will fit on a screen
            newimage = cv2.resize(blackimage, (newsize[0]//3, newsize[1]//3))

            if writerdetect is None or writergraph is None:
                fourcc = cv2.VideoWriter_fourcc(*"MJPG")
                writerdetect = cv2.VideoWriter(outputdetect, fourcc, 30,
                    (frame.shape[1], frame.shape[0]), True)
                writergraph = cv2.VideoWriter(outputgraph, fourcc, 30,
                    (newimage.shape[1], newimage.shape[0]), True)
                print('/tmp/results/{}'.format(outputdetect))

                # some information on processing single frame
                if total > 0:
                    elap = (end - start)
                    print("[INFO] single frame took {:.4f} seconds".format(elap))
                    print("[INFO] estimated total time to finish: {:.4f}".format(
                        elap * total))

            # write output
            writerdetect.write(frame)
            writergraph.write(newimage)

    print("[INFO] cleaning up...")
    writerdetect.release()
    writergraph.release()
    cap.release()
