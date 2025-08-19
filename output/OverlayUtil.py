import cv2 as cv
import numpy as np
from config.Config import ConfigStore
from config.VisionTypes import FiducialFrameObservation, FiducialPoseObservation

def overlay_frame_observation(frame: cv.Mat, observation: FiducialFrameObservation) -> None:
    cv.aruco.drawDetectedMarkers(frame, np.array([observation.corners]), np.array([observation.tag_id]))

def overlay_pose_observation(frame: cv.Mat, config_store: ConfigStore, observation: FiducialPoseObservation) -> None:
    cv.drawFrameAxes(
        frame,
        config_store.local_config.camera_matrix,
        config_store.local_config.distortion_coefficients,
        observation.rvec_0,
        observation.tvec_0,
        config_store.remote_config.fiducial_size_m / 2,
    )
    cv.drawFrameAxes(
        frame,
        config_store.local_config.camera_matrix,
        config_store.local_config.distortion_coefficients,
        observation.rvec_0,
        observation.tvec_1,
        config_store.remote_config.fiducial_size_m / 2,
    )