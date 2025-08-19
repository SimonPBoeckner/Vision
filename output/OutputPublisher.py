from abc import ABC, abstractmethod
from config.Config import ConfigStore
from config.VisionTypes import CameraPoseObservation, FiducialPoseObservation, TagAngleObservation
from typing import SupportsFloat, Union, List
import ntcore
import math

class OutputPublisher(ABC):
    """
    Abstract base class for output publishers.
    This class defines the interface for sending observations and FPS data.
    Subclasses must implement the methods to send data to the desired output medium.
    It is designed to be extended for different output mechanisms, such as NetworkTables.
    The methods are expected to handle the specifics of the output format and transmission.

    Methods:
        send_apriltag_fps(config_store: ConfigStore, timestamp: float, fps: int) -> None:
            Sends the frames per second (FPS) of AprilTag detection.
        
        send_apriltag_observation(
            config_store: ConfigStore,
            timestamp: float,
            observation: Union[CameraPoseObservation, None],
            tag_angles: List[TagAngleObservation]
        ) -> None:
            Sends an AprilTag observation along with associated tag angles.

    This class is intended to be subclassed, and the methods should be implemented
    to provide the actual functionality for sending data.
    Subclasses should ensure that they handle the specifics of the output medium they are targeting.
    """

    @abstractmethod
    def send_apriltag_fps(self, config_store: ConfigStore, timestamp: float, fps: int) -> None:
        pass

    @abstractmethod
    def send_apriltag_observation(
        self,
        config_store: ConfigStore,
        timestamp: float,
        observation: Union[CameraPoseObservation, None],
        tag_angles: List[TagAngleObservation],
        demo_observation: Union[FiducialPoseObservation, None],
    ) -> None:
        pass

    
class NTOutputPublisher(OutputPublisher):
    """
    NTOutputPublisher is a concrete implementation of OutputPublisher that uses NetworkTables
    to publish AprilTag observations and FPS data. It initializes publishers for observations and FPS
    on the first call to check_init, ensuring that the publishers are set up correctly before sending data.
    """
    init_complete: bool = False
    observations_pub: ntcore.DoubleArrayPublisher
    demo_observations_pub: ntcore.DoubleArrayPublisher
    apriltags_fps_pub: ntcore.IntegerPublisher

    def check_init(self, config: ConfigStore):
        # Initialize publishers on first call
        if not self.init_complete:
            self.init_complete = True
            nt_table = ntcore.NetworkTableInstance.getDefault().getTable(
                "/" + config.local_config.device_id + "/output"
            )
            self.observations_pub = nt_table.getDoubleArrayTopic("observations").publish(
                ntcore.PubSubOptions(periodic=0.01, sendAll=True, keepDuplicates=True)
            )
            self.demo_observations_pub = nt_table.getDoubleArrayTopic("demo_observations").publish(
                ntcore.PubSubOptions(periodic=0.01, sendAll=True, keepDuplicates=True)
            )
            self.apriltags_fps_pub = nt_table.getIntegerTopic("fps_apriltags").publish()

    def send_apriltag_fps(self, config_store: ConfigStore, timestamp: float, fps: int) -> None:
        self.check_init(config_store)
        self.apriltags_fps_pub.set(fps)

    def send_apriltag_observation(
        self,
        config_store: ConfigStore,
        timestamp: float,
        observation: Union[CameraPoseObservation, None],
        tag_angles: List[TagAngleObservation],
        demo_observation: Union[FiducialPoseObservation, None],
    ) -> None:
        self.check_init(config_store)

        # Send data
        observation_data: List[SupportsFloat] = [0]
        if observation != None:
            observation_data[0] = 1
            observation_data.append(observation.error_0)
            observation_data.append(observation.pose_0.translation().X())
            observation_data.append(observation.pose_0.translation().Y())
            observation_data.append(observation.pose_0.translation().Z())
            observation_data.append(observation.pose_0.rotation().getQuaternion().W())
            observation_data.append(observation.pose_0.rotation().getQuaternion().X())
            observation_data.append(observation.pose_0.rotation().getQuaternion().Y())
            observation_data.append(observation.pose_0.rotation().getQuaternion().Z())
            if observation.error_1 != None and observation.pose_1 != None:
                observation_data[0] = 2
                observation_data.append(observation.error_1)
                observation_data.append(observation.pose_1.translation().X())
                observation_data.append(observation.pose_1.translation().Y())
                observation_data.append(observation.pose_1.translation().Z())
                observation_data.append(observation.pose_1.rotation().getQuaternion().W())
                observation_data.append(observation.pose_1.rotation().getQuaternion().X())
                observation_data.append(observation.pose_1.rotation().getQuaternion().Y())
                observation_data.append(observation.pose_1.rotation().getQuaternion().Z())
        for tag_angle_observation in tag_angles:
            observation_data.append(tag_angle_observation.tag_id)
            for angle in tag_angle_observation.corners.ravel():
                observation_data.append(angle)
            observation_data.append(tag_angle_observation.distance)

        demo_observation_data: List[SupportsFloat] = []
        if demo_observation != None:
            demo_observation_data.append(demo_observation.error_0)
            demo_observation_data.append(demo_observation.pose_0.translation().X())
            demo_observation_data.append(demo_observation.pose_0.translation().Y())
            demo_observation_data.append(demo_observation.pose_0.translation().Z())
            demo_observation_data.append(demo_observation.pose_0.rotation().getQuaternion().W())
            demo_observation_data.append(demo_observation.pose_0.rotation().getQuaternion().X())
            demo_observation_data.append(demo_observation.pose_0.rotation().getQuaternion().Y())
            demo_observation_data.append(demo_observation.pose_0.rotation().getQuaternion().Z())
            demo_observation_data.append(demo_observation.error_1)
            demo_observation_data.append(demo_observation.pose_1.translation().X())
            demo_observation_data.append(demo_observation.pose_1.translation().Y())
            demo_observation_data.append(demo_observation.pose_1.translation().Z())
            demo_observation_data.append(demo_observation.pose_1.rotation().getQuaternion().W())
            demo_observation_data.append(demo_observation.pose_1.rotation().getQuaternion().X())
            demo_observation_data.append(demo_observation.pose_1.rotation().getQuaternion().Y())
            demo_observation_data.append(demo_observation.pose_1.rotation().getQuaternion().Z())

        self.observations_pub.set(observation_data, math.floor(timestamp * 1000000))
        self.demo_observations_pub.set(demo_observation_data, math.floor(timestamp * 1000000))
