from typing import List, Union
import cv2 as cv
import numpy as np
from config.Config import ConfigStore
from config.VisionTypes import CameraPoseObservation, FiducialFrameObservation
from pipeline.CoordinateSystems import wpilib_translation_to_opencv, opencv_pose_to_wpilib
from wpimath.geometry import Pose3d, Translation3d, Rotation3d, Quaternion, Transform3d
from abc import ABC, abstractmethod

class CameraPoseEstimator(ABC):
    """
    Abstract base class for camera pose estimators.
    This class defines the interface for estimating camera poses based on fiducial frame observations.
    Subclasses must implement the method to solve the camera pose given a list of fiducial frame observations.
    
    Methods:
        solve_camera_pose(frame_observations: List[FiducialFrameObservation], config_store: ConfigStore) -> Union[CameraPoseObservation, None]:
            Estimates the camera pose based on the provided frame observations and configuration store.
            Returns a CameraPoseObservation if successful, or None if the pose cannot be estimated.
    
    This class is intended to be subclassed, and the method should be implemented
    to provide the actual functionality for solving the camera pose.
    Subclasses should ensure that they handle the specifics of the observations and configuration store they are working with.
    """

    @abstractmethod
    def solve_camera_pose(self, frame_observations: List[FiducialFrameObservation], config_store: ConfigStore) -> Union[CameraPoseObservation, None]:
        pass

    
class MultiTargetCameraPoseEstimator(CameraPoseEstimator):
    """
    MultiTargetCameraPoseEstimator is a concrete implementation of CameraPoseEstimator that estimates the camera pose
    based on multiple fiducial frame observations. It uses the OpenCV solvePnP function to compute the camera pose
    from the observed fiducial corners and their known positions in the field.
    This estimator is designed to work with a tag layout defined in the configuration store, and it handles both single-tag
    and multi-tag scenarios.
    
    Methods:
        solve_camera_pose(frame_observations: List[FiducialFrameObservation], config_store: ConfigStore) -> Union[CameraPoseObservation, None]:
            Estimates the camera pose based on the provided frame observations and configuration store.
            Returns a CameraPoseObservation if successful, or None if the pose cannot be estimated.
    This class is intended to be used when multiple fiducial tags are present in the field, allowing for robust camera pose estimation.
    """
    def __init__(self) -> None:
        pass

    def solve_camera_pose(self, frame_observations: List[FiducialFrameObservation], config_store: ConfigStore) -> Union[CameraPoseObservation, None]:
        # Exit if no tag layout available
        if config_store.remote_config.tag_layout == None:
            return None
        
        # Exit if no observations available
        if len(frame_observations) == 0:
            return None
        
        # Create set of object and image points
        fid_size = config_store.remote_config.fiducial_size_m
        object_points = []
        frame_points = []
        tag_ids = []
        tag_poses = []
        for observation in frame_observations:
            tag_pose = None
            for tag_data in config_store.remote_config.tag_layout["tags"]:
                # if the tag we see in the observation exists in our data of the tags on the field load the location of it into tag_pose
                if tag_data["ID"] == observation.tag_id:
                    tag_pose = Pose3d(
                        Translation3d(
                            tag_data["pose"]["translation"]["x"],
                            tag_data["pose"]["translation"]["y"],
                            tag_data["pose"]["translation"]["z"],
                        ),
                        Rotation3d(
                            Quaternion(
                                tag_data["pose"]["rotation"]["quaternion"]["W"],
                                tag_data["pose"]["rotation"]["quaternion"]["X"],
                                tag_data["pose"]["rotation"]["quaternion"]["Y"],
                                tag_data["pose"]["rotation"]["quaternion"]["Z"],
                            )
                        ),
                    )
                if tag_pose != None:
                    # Add object points by transforming from the tag center
                    # 3d corner points in tag's local space
                    # take global tag pose relative to field and add half of tag size to find each corner of the tag relative to the field
                    corner_0 = tag_pose + Transform3d(Translation3d(0, fid_size / 2.0, -fid_size / 2.0), Rotation3d())
                    corner_1 = tag_pose + Transform3d(Translation3d(0, -fid_size / 2.0, -fid_size / 2.0), Rotation3d())
                    corner_2 = tag_pose + Transform3d(Translation3d(0, -fid_size / 2.0, fid_size / 2.0), Rotation3d())
                    corner_3 = tag_pose + Transform3d(Translation3d(0, fid_size / 2.0, fid_size / 2.0), Rotation3d())
                    object_points += [
                        wpilib_translation_to_opencv(corner_0.translation()),
                        wpilib_translation_to_opencv(corner_1.translation()),
                        wpilib_translation_to_opencv(corner_2.translation()),
                        wpilib_translation_to_opencv(corner_3.translation()),
                    ]

                    # Add frame points from observation
                    # 2d positions of each detected corner in the image
                    frame_points += [
                        [observation.corners[0][0][0], observation.corners[0][0][1]],
                        [observation.corners[0][1][0], observation.corners[0][1][1]],
                        [observation.corners[0][2][0], observation.corners[0][2][1]],
                        [observation.corners[0][3][0], observation.corners[0][3][1]],
                    ]

                    # Add tag ID and pose
                    tag_ids.append(observation.tag_id)
                    tag_poses.append(tag_pose)

            # Single tag, return two poses
            if len(tag_ids) == 1:
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
                        np.array(frame_points),
                        config_store.local_config.camera_matrix,
                        config_store.local_config.distortion_coefficients,
                        flags=cv.SOLVEPNP_IPPE_SQUARE,
                    )
                except:
                    return None
                
                # Calculate WPILib camera poses
                field_to_tag_pose = tag_poses[0]
                camera_to_tag_pose_0 = opencv_pose_to_wpilib(tvecs[0], rvecs[0])
                camera_to_tag_pose_1 = opencv_pose_to_wpilib(tvecs[1], rvecs[1])
                camera_to_tag_0 = Transform3d(camera_to_tag_pose_0.translation(), camera_to_tag_pose_0.rotation())
                camera_to_tag_1 = Transform3d(camera_to_tag_pose_1.translation(), camera_to_tag_pose_1.rotation())
                field_to_camera_0 = field_to_tag_pose.transformBy(camera_to_tag_0.inverse())
                field_to_camera_1 = field_to_tag_pose.transformBy(camera_to_tag_1.inverse())
                field_to_camera_pose_0 = Pose3d(field_to_camera_0.translation(), field_to_camera_0.rotation())
                field_to_camera_pose_1 = Pose3d(field_to_camera_1.translation(), field_to_camera_1.rotation())

                # Return result
                return CameraPoseObservation(tag_ids, field_to_camera_pose_0, errors[0][0], field_to_camera_pose_1, errors[1][0])
            
            # Multi-tag, return one pose
            else:
                # Run SolvePNP with all tags
                try:
                    _, rvecs, tvecs, errors = cv.solvePnPGeneric(
                        np.array(object_points),
                        np.array(frame_points),
                        config_store.local_config.camera_matrix,
                        config_store.local_config.distortion_coefficients,
                        flags=cv.SOLVEPNP_SQPNP,
                    )
                except:
                    return None
                
                # Calculate WPILib camera pose
                camera_to_field_pose = opencv_pose_to_wpilib(tvecs[0], rvecs[0])
                camera_to_field = Transform3d(camera_to_field_pose.translation(), camera_to_field_pose.rotation())
                field_to_camera = camera_to_field.inverse()
                field_to_camera_pose = Pose3d(field_to_camera.translation(), field_to_camera.rotation())

                # Return result
                return CameraPoseObservation(tag_ids, field_to_camera_pose, errors[0][0], None, None)