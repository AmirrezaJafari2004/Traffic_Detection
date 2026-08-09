"""Traffic detection and lane-level counting logic."""

import json
import os

import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YOLO_CONFIG_DIR = os.path.join(BASE_DIR, "data", "ultralytics_config")
os.makedirs(YOLO_CONFIG_DIR, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", YOLO_CONFIG_DIR)

from ultralytics import YOLO

MODEL_PATH = os.path.join(BASE_DIR, "models", "weights", "best.pt")
LANES_DIR = os.path.join(BASE_DIR, "lanes")

GREEN_MAX = 4
YELLOW_MAX = 7

COLOR_GREEN = (0, 200, 0)
COLOR_YELLOW = (0, 220, 220)
COLOR_RED = (0, 0, 220)
COLOR_BOX = (255, 255, 255)


class TrafficSystem:
    def __init__(self, model_path=MODEL_PATH):
        self.model = YOLO(model_path)

    @staticmethod
    def lanes_path_for_video(video_path):
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        return os.path.join(LANES_DIR, f"{video_name}_lanes.json")

    def load_lanes(self, video_path):
        lanes_file = self.lanes_path_for_video(video_path)
        if not os.path.exists(lanes_file):
            return None

        with open(lanes_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {name: np.array(pts, dtype=np.int32) for name, pts in data.items()}

    @staticmethod
    def _lane_color(count):
        if count <= GREEN_MAX:
            return COLOR_GREEN, "Low"
        if count <= YELLOW_MAX:
            return COLOR_YELLOW, "Medium"
        return COLOR_RED, "Heavy"

    def process_frame(self, frame, lanes=None, conf=0.5, iou=0.45, display_size=None, orig_size=None):
        results = self.model(frame, conf=conf, iou=iou, verbose=False)[0]
        total_count = len(results.boxes)

        lane_counts = None
        scaled_lanes = None

        if lanes is not None and display_size is not None and orig_size is not None:
            scale_x = display_size[0] / orig_size[0]
            scale_y = display_size[1] / orig_size[1]
            scaled_lanes = {}
            for name, pts in lanes.items():
                scaled = pts.astype(np.float32).copy()
                scaled[:, 0] *= scale_x
                scaled[:, 1] *= scale_y
                scaled_lanes[name] = scaled.astype(np.int32)
            lane_counts = {name: 0 for name in lanes}

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            if scaled_lanes is not None:
                for name, poly in scaled_lanes.items():
                    if cv2.pointPolygonTest(poly, (float(cx), float(cy)), False) >= 0:
                        lane_counts[name] += 1
                        break

            cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_BOX, 1)

        if scaled_lanes is not None:
            overlay = frame.copy()
            for name, poly in scaled_lanes.items():
                count = lane_counts[name]
                color, level = self._lane_color(count)
                cv2.fillPoly(overlay, [poly], color)

            frame = cv2.addWeighted(overlay, 0.25, frame, 0.75, 0)

            y_offset = 60
            for name, poly in scaled_lanes.items():
                count = lane_counts[name]
                color, level = self._lane_color(count)

                cv2.polylines(frame, [poly], isClosed=True, color=color, thickness=2)

                cx = int(np.mean(poly[:, 0]))
                cy = int(np.mean(poly[:, 1]))
                cv2.putText(
                    frame,
                    f"{name}: {count}",
                    (cx - 40, cy),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"{name}: {count} ({level})",
                    (20, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    2,
                )
                y_offset += 24

        cv2.putText(
            frame,
            f"Vehicles: {total_count}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
        )

        return frame, total_count, lane_counts
