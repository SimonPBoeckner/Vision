from abc import ABC, abstractmethod
from config.DataTypes import FiducialData, PoseData
from config.Config import ConfigStore
from typing import Optional, List
import numpy as np
import cv2 as cv
from wpimath.geometry import Pose3d, Translation3d, Rotation3d, Quaternion, Transform3d

from pipeline.CoordinateSystems import opencv_pose_to_wpilib, wpilib_translation_to_opencv

class PoseEstimator(ABC):
    """"""

    @abstractmethod
    def get_pose(self, fiducial_data: List[FiducialData], config_store: ConfigStore) -> Optional[PoseData]:
        pass

class CameraPoseEstimator(PoseEstimator):
    """"""

    def __init__(self) -> None:
        pass

    def get_pose(self, fiducial_data: List[FiducialData], config_store: ConfigStore) -> Optional[PoseData]:
        # Exit if no tag layout available
        if config_store.remote_config.tag_layout is None:
            return None
        
        # Exit if no observations available
        if fiducial_data is None:
            return None
        
        # Create set of object and image points
        fid_size = config_store.remote_config.fiducial_size_m
        object_points = []
        frame_points = []
        tag_ids = []
        tag_poses = []
        for fiducial in fiducial_data:
            tag_pose = None
            for tag_data in config_store.remote_config.tag_layout["tags"]:
                # if the tag we see in the frame exists in our data of the tags on the field load the location of it into tag_pose which is then added to tag_poses
                if tag_data["ID"] == fiducial.id:
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
                    # take global tag pose relative to field and add half of tag size to find each of the tag relative to the field
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
                        [fiducial.corners[0][0][0], fiducial.corners[0][0][1]],
                        [fiducial.corners[0][1][0], fiducial.corners[0][1][1]],
                        [fiducial.corners[0][2][0], fiducial.corners[0][2][1]],
                        [fiducial.corners[0][3][0], fiducial.corners[0][3][1]],
                    ]

                    # Add tag ID and pose
                    tag_ids.append(fiducial.id)
                    tag_poses.append(tag_pose)

            # Single tag, return two poses
            if len(tag_ids) == 1:
                object_points =  np.array(
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

                #Return result
                if errors[0][0] > errors[1][0]:
                    return PoseData(tag_ids, field_to_camera_pose_0, errors[0][0], fiducial.timestamp)
                else:
                    return PoseData(tag_ids, field_to_camera_pose_1, errors[1][0], fiducial.timestamp)

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
                return PoseData(tag_ids, field_to_camera_pose, errors[0][0], fiducial.timestamp)