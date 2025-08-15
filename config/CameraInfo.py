from abc import ABC, abstractmethod
import json
import subprocess
import os
import glob
import re

class CameraInfo(ABC):
    """"""

    @abstractmethod
    def get_info(self) -> None:
        pass

class V4L2CameraInfo(CameraInfo):
    """"""

    def is_webcam_device(self, device):
        try:
            output = subprocess.check_output(
                ["v4l2-ctl", "-d", device, "--info"],
                text=True,
                stderr=subprocess.DEVNULL
            )
            for line in output.splitlines():
                if line.startswith("Driver name:"):
                    driver = line.split(":", 1)[1].strip()
                    # Accept common webcam drivers; extend this list as needed
                    if driver in ("uvcvideo", "bttv", "v4l2_common", "gspca_main"):
                        return True
                    else:
                        return False
            return False
        except subprocess.CalledProcessError:
            return False

    def parse_controls(self, output: str) -> dict:
        controls = {}
        current_control = None

        for line in output.splitlines():
            line = line.strip()
            if not line:
                current_control = None
                continue

            # Control header line, e.g.:
            # brightness (int)    : min=-64 max=64 step=1 default=0 value=0
            m = re.match(r"^([\w\s\-]+)\s+\((\w+)\)\s*:\s*(.*)$", line)
            if m:
                name, ctype, rest = m.groups()
                name = name.strip()
                props = {}

                # parse properties like min=..., max=..., step=..., default=..., value=...
                for part in rest.split():
                    if "=" in part:
                        k,v = part.split("=",1)
                        # try convert to int or float
                        try:
                            if '.' in v:
                                v = float(v)
                            else:
                                v = int(v)
                        except ValueError:
                            pass
                        props[k] = v

                controls[name] = {
                    "type": ctype,
                    "properties": props
                }
                current_control = name
                # Initialize menu dict if menu type
                if ctype == "menu":
                    controls[name]["menu"] = {}

            # Menu items line, e.g.:
            #     0: Auto
            #     1: Manual
            elif current_control and controls[current_control]["type"] == "menu":
                mm = re.match(r"^(\d+):\s*(.+)$", line)
                if mm:
                    idx, label = mm.groups()
                    controls[current_control]["menu"][int(idx)] = label

        return controls
    
    def parse_formats(self, output: str) -> list:
        formats = []
        current_format = None

        for line in output.splitlines():
            line = line.strip()
            # Format line: [0]: 'YUYV' (YUYV 4:2:2)
            m = re.match(r"^\[\d+\]:\s+'(\w+)'", line)
            if m:
                current_format = {"format": m.group(1), "resolutions": []}
                formats.append(current_format)
                continue

            # Resolution line: Size: Discrete 640x480
            m = re.match(r"Size:\s+Discrete\s+(\d+)x(\d+)", line)
            if m and current_format:
                width, height = int(m.group(1)), int(m.group(2))
                resolution = {"width": width, "height": height, "framerates": []}
                current_format["resolutions"].append(resolution)
                continue

            # Frame interval line: Interval: Discrete 1/30
            m = re.match(r"Interval:\s+Discrete\s+(\d+)/(\d+)", line)
            if m and current_format and current_format["resolutions"]:
                num, den = int(m.group(1)), int(m.group(2))
                fps = round(den / num, 2) if num != 0 else 0.0
                current_format["resolutions"][-1]["framerates"].append(fps)

        return formats

    def get_info(self) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # devices = sorted(glob.glob("/dev/video*"))

        # webcams = [dev for dev in devices if self.is_webcam_device(dev)]
        webcams = ["/dev/video0"]
        if not webcams:
            print("No webcams detected.")
            return

        for device in webcams:
            try:
                controls_output = subprocess.check_output(
                    ["v4l2-ctl", "-d", device, "--list-ctrls-menus"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                formats_output = subprocess.check_output(
                    ["v4l2-ctl", "-d", device, "--list-formats-ext"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )

                controls = self.parse_controls(controls_output)
                formats = self.parse_formats(formats_output)

                data = {
                    "device": device,
                    "controls": controls,
                    "formats": formats
                }

                safe_name = device.replace("/", "_")
                output_path = os.path.join(script_dir, f"{safe_name}_capabilities.json")
                with open(output_path, "w") as f:
                    json.dump(data, f, indent=4)

                print(f"Saved capabilities for {device} at {output_path}")

            except subprocess.CalledProcessError as e:
                print(f"Error accessing {device}: {e}")