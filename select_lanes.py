"""
Interactive lane selector for traffic videos.
"""

import json
import os
from tkinter import Tk, filedialog

import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LANES_DIR = os.path.join(BASE_DIR, "lanes")
WINDOW_NAME = "Lane Selector"

LINE_COLOR = (0, 255, 255)
POINT_COLOR = (0, 80, 255)
SAVED_COLOR = (0, 180, 0)
TEXT_COLOR = (255, 255, 255)


class LaneSelector:
    def __init__(self, video_path):
        self.video_path = video_path
        self.frame = self._read_first_frame(video_path)
        self.lanes = {}
        self.current_points = []
        self.next_lane_number = 1

    @staticmethod
    def _read_first_frame(video_path):
        cap = cv2.VideoCapture(video_path)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise RuntimeError(f"Unable to read first frame from: {video_path}")
        return frame

    @property
    def output_path(self):
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        return os.path.join(LANES_DIR, f"{video_name}_lanes.json")

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_points.append([x, y])

    def save_current_lane(self):
        if len(self.current_points) < 3:
            return False

        lane_name = f"Lane {self.next_lane_number}"
        self.lanes[lane_name] = self.current_points.copy()
        self.current_points = []
        self.next_lane_number += 1
        return True

    def save_all(self):
        if len(self.current_points) >= 3:
            self.save_current_lane()

        if not self.lanes:
            return False

        os.makedirs(LANES_DIR, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.lanes, f, indent=2)
        return True

    def draw(self):
        canvas = self.frame.copy()

        for name, points in self.lanes.items():
            poly = np.array(points, dtype=np.int32)
            overlay = canvas.copy()
            cv2.fillPoly(overlay, [poly], SAVED_COLOR)
            canvas = cv2.addWeighted(overlay, 0.18, canvas, 0.82, 0)
            cv2.polylines(canvas, [poly], True, SAVED_COLOR, 2)
            center = poly.mean(axis=0).astype(int)
            cv2.putText(canvas, name, tuple(center), cv2.FONT_HERSHEY_SIMPLEX, 0.7, TEXT_COLOR, 2)

        if self.current_points:
            pts = np.array(self.current_points, dtype=np.int32)
            for x, y in self.current_points:
                cv2.circle(canvas, (x, y), 5, POINT_COLOR, -1)
            if len(pts) >= 2:
                cv2.polylines(canvas, [pts], False, LINE_COLOR, 2)

        help_lines = [
            "Left click: add point | N: next lane | S: save | Backspace: undo",
            "R: reset current lane | Q/Esc: quit",
            f"Saved lanes: {len(self.lanes)} | Current points: {len(self.current_points)}",
        ]
        y = 28
        for line in help_lines:
            cv2.putText(canvas, line, (18, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 4)
            cv2.putText(canvas, line, (18, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, TEXT_COLOR, 2)
            y += 30

        return canvas

    def run(self):
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(WINDOW_NAME, self.mouse_callback)

        saved = False
        while True:
            cv2.imshow(WINDOW_NAME, self.draw())
            key = cv2.waitKey(20) & 0xFF

            if key in (27, ord("q"), ord("Q")):
                break
            if key in (8, 127):
                if self.current_points:
                    self.current_points.pop()
            elif key in (ord("n"), ord("N")):
                self.save_current_lane()
            elif key in (ord("r"), ord("R")):
                self.current_points = []
            elif key in (ord("s"), ord("S")):
                saved = self.save_all()
                break

        cv2.destroyAllWindows()
        return saved


def choose_video():
    root = Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Select a video for lane setup",
        initialdir=os.path.join(BASE_DIR, "videos"),
        filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")],
    )
    root.destroy()
    return path


def main():
    video_path = choose_video()
    if not video_path:
        print("No video selected.")
        return

    selector = LaneSelector(video_path)
    saved = selector.run()

    if saved:
        print(f"Saved lane file: {selector.output_path}")
    else:
        print("No lane file was saved.")


if __name__ == "__main__":
    main()
