from abc import ABC, abstractmethod
from config.Config import ConfigStore
from pipeline.PoseEstimator import SquareTargetPoseEstimator
from config.VisionTypes import FiducialFrameObservation, FiducialPoseObservation, TagAngleObservation
from typing import Union
import cv2 as cv
import numpy as np
import math

class TagAngleCalculator(ABC):
    """
    Abstract base class for calculating tag angles.
    This class defines the interface for calculating angles of fiducial tags based on frame observations.
    Subclasses must implement the method to calculate tag angles given a fiducial frame observation.
    
    Methods:
        calculate_tag_angles(frame_observation: FiducialFrameObservation, config_store: ConfigStore) -> Union[TagAngleObservation, None]:
            Calculates the angles of the fiducial tag corners and returns a TagAngleObservation if successful,
            or None if the angles cannot be calculated.
    
    This class is intended to be subclassed, and the method should be implemented
    to provide the actual functionality for calculating tag angles.
    Subclasses should ensure that they handle the specifics of the observations and configuration store they are working with.
    """

    @abstractmethod
    def calculate_tag_angles(self, frame_observation: FiducialFrameObservation, config_store: ConfigStore) -> Union[TagAngleObservation, None]:
        pass
    

class CameraMatrixTagAngleCalculator(TagAngleCalculator):
    """
    CameraMatrixTagAngleCalculator is a concrete implementation of TagAngleCalculator that calculates the angles
    of fiducial tag corners based on the camera matrix and undistorted corners. It uses the OpenCV undistortPoints function
    to get the undistorted corners and then calculates the angles based on the camera matrix.
    
    Methods:
        calculate_tag_angles(frame_observation: FiducialFrameObservation, config_store: ConfigStore) -> Union[TagAngleObservation, None]:
            Calculates the angles of the fiducial tag corners and returns a TagAngleObservation if successful,
            or None if the angles cannot be calculated.
    """

    tag_pose_estimator = SquareTargetPoseEstimator()

    def __init__(self) -> None:
        pass

    def calculate_tag_angles(self, frame_observation: FiducialFrameObservation, config_store: ConfigStore) -> Union[TagAngleObservation, None]:
        # Undistort corners
        corners_undistorted = cv.undistortPoints(
            frame_observation.corners,
            config_store.local_config.camera_matrix,
            config_store.local_config.distortion_coefficients,
            None,
            config_store.local_config.camera_matrix
        )

        # Calculate angles
        corners = np.zeros((4, 2))
        for index, corner in enumerate(corners_undistorted):
            vec = np.linalg.inv(config_store.local_config.camera_matrix).dot(
                np.array([corner[0][0], corner[0][1], 1]).T
            )
            corners[index][0] = math.atan(vec[0])
            corners[index][1] = math.atan(vec[1])

        # Get distance
        pose_observation: FiducialPoseObservation = self.tag_pose_estimator.solve_fiducial_pose(
            frame_observation, config_store
        )
        if pose_observation == None:
            return None
        distance: float = 0
        if pose_observation.error_0 < pose_observation.error_1:
            distance = pose_observation.pose_0.translation().norm()
        else:
            distance = pose_observation.pose_1.translation().norm()

        # Publish result
        return TagAngleObservation(frame_observation.tag_id, corners, distance)