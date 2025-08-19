from abc import ABC, abstractmethod

class CameraInformation(ABC):
    """"""

    @abstractmethod
    def get_info(self) -> None:
        pass

class v4l2CameraInformation(CameraInformation):
    """"""
    
    def get_info(self) -> None:
        pass
