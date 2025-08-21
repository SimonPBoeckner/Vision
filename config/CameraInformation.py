from typing import Dict, Any, List
from abc import ABC, abstractmethod
import subprocess
import re
import json

import ntcore

from config.Config import ConfigStore

class CameraInformation(ABC):
    """"""

    @staticmethod
    def run_cmd(cmd: str) -> str:
        """Run a shell command and return decoded stdout."""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()

    @abstractmethod
    def get_device_data(self, device: str) -> Dict[str, str]:
        pass

    @abstractmethod
    def get_device_formats(self, device: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_controls(self, device: str) -> List[Dict[str, Any]]:
        pass


class v4l2CameraInformation(CameraInformation):
    """"""
    
    def get_device_data(self, device: str) -> Dict[str, str]:
        """Get device details with v4l2-ctl -D."""
        output = self.run_cmd(f"v4l2-ctl -d {device} -D")
        info: Dict[str, str] = {}
        for line in output.splitlines():
            line = line.strip()
            if ":" in line:
                key, value = [p.strip() for p in line.split(":", 1)]
                info[key.lower().replace(" ", "_")] = value
        return info
    
    def get_device_formats(self, device: str) -> List[Dict[str, Any]]:
        """Get supported formats, resolutions, and framerates using v4l2-ctl."""
        output = self.run_cmd(f"v4l2-ctl -d {device} --list-formats-ext")
        formats: List[Dict[str, Any]] = []
        current_fmt: Dict[str, Any] | None = None

        for line in output.splitlines():
            line = line.strip()
            fmt_match = re.match(r"\[\d+\]: '(\w+)' \((.+)\)", line)
            if fmt_match:
                current_fmt = {"fourcc": fmt_match.group(1),
                            "description": fmt_match.group(2),
                            "resolutions": []}
                formats.append(current_fmt)
            res_match = re.match(r"Size: Discrete (\d+)x(\d+)", line)
            if res_match and current_fmt:
                resolution = {"width": int(res_match.group(1)),
                            "height": int(res_match.group(2)),
                            "framerates": []}
                current_fmt["resolutions"].append(resolution)
            fps_match = re.match(r"Interval: Discrete (\d+)\/(\d+)s", line)
            if fps_match and current_fmt and current_fmt["resolutions"]:
                num, denom = map(int, fps_match.groups())
                fps = denom / num if num else 0
                current_fmt["resolutions"][-1]["framerates"].append(fps)
        return formats
    
    def get_controls(self, device: str) -> List[Dict[str, Any]]:
        """Get available camera controls and their properties."""
        output = self.run_cmd(f"v4l2-ctl -d {device} --list-ctrls-menus")
        controls: List[Dict[str, Any]] = []
        for line in output.splitlines():
            line = line.strip()
            ctrl_match = re.match(
                r"(\w[\w-]+)\s+0x[0-9a-f]+ \((\w+)\)\s*:\s*min=(-?\d+)\s+max=(-?\d+)\s+step=(\d+)\s+default=(-?\d+)\s+value=(-?\d+)",
                line)
            if ctrl_match:
                name, ctype, minv, maxv, step, default, value = ctrl_match.groups()
                controls.append({
                    "name": name,
                    "type": ctype,
                    "min": int(minv),
                    "max": int(maxv),
                    "step": int(step),
                    "default": int(default),
                    "current": int(value)
                })
        return controls
    
    def get_info(self) -> None:
        """Print camera information for all /dev/video* devices."""
        devices: List[str] = [f"/dev/video{i}" for i in range(3)]
        results: Dict[str, Dict[str, Any]] = {}

        for device in devices:
            try:
                info = self.get_device_data(device)
                formats = self.get_device_formats(device)
                controls = self.get_controls(device)
                results[device] = {
                    "info": info,
                    "formats": formats,
                    "controls": controls
                }
            except Exception as e:
                results[device] = {"error": str(e)}

        print(json.dumps(results, indent=2))

    def send_info(self, data: Dict[str, Any], config_store: ConfigStore) -> None:
        """Publish camera info JSON to a NetworkTable."""
        inst = ntcore.NetworkTableInstance.getDefault()
        table = inst.getTable("/" + config_store.local_config.device_id + "/camera_info")
        inst.startClient4("camera_info_publisher")
        inst.setServer(config_store.local_config.server_ip)

        table.putString("data", json.dumps(data, indent=2))