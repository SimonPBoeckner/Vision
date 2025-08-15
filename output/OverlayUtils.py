import cv2 as cv
import numpy as np
from config.DataTypes import FiducialData, PoseData

camera_matrix = np.array([
    [920, 0, 640],
    [0, 920, 360],
    [0, 0, 1]
], dtype=np.float32)
dist_coeffs = np.zeros(5)

def draw_overlay(frame: cv.typing.MatLike, fiducial_data: FiducialData, pose_data: PoseData) -> None:
    cv.aruco.drawDetectedMarkers(frame, fiducial_data.corners, fiducial_data.ids)

    cv.drawFrameAxes(
        frame,
        camera_matrix,
        dist_coeffs,
        pose_data.rvec,
        pose_data.tvec,
        0.1651
    )