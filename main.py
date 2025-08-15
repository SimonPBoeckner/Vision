from pipeline.Capture import GStreamerCapture
from pipeline.Detector import ArucoDetector
from output.StreamServer import FlaskStreamServer
from pipeline.PoseEstimator import CameraPoseEstimator
from output.OverlayUtils import draw_overlay
import cv2 as cv
import threading

capture = GStreamerCapture()
detector = ArucoDetector(cv.aruco.DICT_APRILTAG_36H11)
estimator = CameraPoseEstimator()
streamer = FlaskStreamServer("192.168.4.90", 5000)

threading.Thread(target=streamer.run, daemon=True).start()

while True:
    frame_data = capture.get_frame()
    if frame_data is None or frame_data.frame is None or frame_data.frame.size == 0:
        continue

    # Try to detect tags
    fiducial_data = detector.detect_tag(frame_data)

    # If tags found, try to estimate pose & draw overlay
    if fiducial_data:
        pose_data = estimator.get_pose(fiducial_data)
        if pose_data:
            frame_data.frame = cv.cvtColor(frame_data.frame, cv.COLOR_GRAY2BGR)
            draw_overlay(frame_data.frame, fiducial_data, pose_data)

    streamer.send_frame(frame_data.frame)