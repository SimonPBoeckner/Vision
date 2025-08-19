from typing import Union
from abc import ABC, abstractmethod

import cv2 as cv
import numpy as np

from pipeline.CoordinateSystems import opencv_pose_to_wpilib
from config.Config import ConfigStore
from config.VisionTypes import FiducialFrameObservation, FiducialPoseObservation


class PoseEstimator(ABC):
    """
    Abstract base class for pose estimators.
    This class defines the interface for estimating poses based on fiducial frame observations.
    Subclasses must implement the method to solve the pose given a fiducial frame observation.
    
    Methods:
        solve_fiducial_pose(frame_observation: FiducialFrameObservation, config_store: ConfigStore) -> Union[FiducialPoseObservation, None]:
            Estimates the pose based on the provided frame observation and configuration store.
            Returns a FiducialPoseObservation if successful, or None if the pose cannot be estimated.
    
    This class is intended to be subclassed, and the method should be implemented
    to provide the actual functionality for solving the pose.
    Subclasses should ensure that they handle the specifics of the observations and configuration store they are working with.
    """

    @abstractmethod
    def solve_fiducial_pose(self, frame_observation: FiducialFrameObservation, config_store: ConfigStore) -> Union[FiducialPoseObservation, None]:
        pass


class SquareTargetPoseEstimator(PoseEstimator):
    """
    SquareTargetPoseEstimator is a concrete implementation of PoseEstimator that estimates the pose
    based on a fiducial frame observation of a square target. It uses the OpenCV solvePnP function to compute the pose
    from the observed corners of the fiducial tag.
    
    Methods:
        solve_fiducial_pose(frame_observation: FiducialFrameObservation, config_store: ConfigStore) -> Union[FiducialPoseObservation, None]:
            Estimates the pose based on the provided frame observation and configuration store.
            Returns a FiducialPoseObservation if successful, or None if the pose cannot be estimated.
    """

    def __init__(self) -> None:
        pass

    def solve_fiducial_pose(self, frame_observation: FiducialFrameObservation, config_store: ConfigStore) -> Union[FiducialPoseObservation, None]:
        fid_size = config_store.remote_config.fiducial_size_m
        object_points = np.array(
            [
                [-fid_size / 2.0, fid_size / 2.0, 0.0],
                [fid_size / 2.0, fid_size / 2.0, 0.0],
                [fid_size / 2.0, -fid_size / 2.0, 0.0],
                [-fid_size / 2.0, -fid_size / 2.0, 0.0],
            ]
        )

        try:
            _, rvecs, tvecs, errors = cv.solvePnPGeneric(
                object_points,
                frame_observation.corners,
                config_store.local_config.camera_matrix,
                config_store.local_config.distortion_coefficients,
                flags=cv.SOLVEPNP_IPPE_SQUARE,
            )
        except:
            return None
        try:
            return FiducialPoseObservation(
                frame_observation.tag_id,
                opencv_pose_to_wpilib(tvecs[0], rvecs[0]),
                errors[0][0],
                opencv_pose_to_wpilib(tvecs[1], rvecs[1]),
                errors[1][0],
            )
        except:
            return None