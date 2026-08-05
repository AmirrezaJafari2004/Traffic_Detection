# Traffic Monitoring and Analysis System

This desktop application monitors traffic videos using a trained YOLO model.
It has two user roles:

- **Admin:** uploads a video, enters street/time information, runs detection,
  previews the processed video, and saves the annotated output.
- **System Manager:** views saved admin output videos. At most two videos are
  displayed at a time, and each visible slot can be swapped with any saved
  output. The manager panel only plays saved videos and does not run YOLO again.

## Project Structure

```text
traffic_admin_app/
  main.py
  requirements.txt
  core/
    auth.py
    admin_log.py
    traffic_system.py
  gui/
    common.py
    login_window.py
    admin_gui.py
    manager_gui.py
  data/
    credentials.json
    admin_logins.json
  assets/
    app_icon.ico
    app_icon.png
  lanes/
    <video_name>_lanes.json
  models/
    weights/
      best.pt
      last.pt
  videos/
```

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Run the command from inside the `traffic_admin_app` folder, or run:

```bash
python traffic_admin_app/main.py
```

from the project root.

## Lane Setup

Lane coloring is enabled when a matching lane JSON file exists in `lanes/`.
Use the lane selector before processing a video:

```bash
python select_lanes.py
```

Controls:

- Left click: add polygon points for the current lane.
- `N`: save the current lane polygon and start the next lane.
- `S`: save all lanes to `lanes/<video_name>_lanes.json`.
- Backspace: remove the last point.
- `R`: reset the current lane.
- `Q` or Esc: quit without saving.

When lane data exists, the processed video shows each lane with a color based
on vehicle count:

- Green: low traffic
- Yellow: medium traffic
- Red: heavy traffic

## Default Users

| Role | Username | Password |
| --- | --- | --- |
| Admin 1 | `admin1` | `admin123` |
| Admin 2 | `admin2` | `admin123` |
| System Manager | `manager` | `manager123` |

The login data is stored in `data/credentials.json` and can be changed later.

## Notes

- The YOLO model path is `models/weights/best.pt`.
- Admin login, logout, and processing records are stored in
  `data/admin_logins.json`.
- The manager dashboard can clear admin logs when needed.
- Optional lane files can be stored in `lanes/` using the naming pattern
  `<video_name>_lanes.json`.
