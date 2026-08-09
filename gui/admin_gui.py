"""Admin panel for uploading, processing, displaying, and saving videos."""

import os
from tkinter import filedialog, messagebox

import cv2
import customtkinter as ctk
from PIL import Image, ImageTk

from core.admin_log import attach_report_path, record_logout, update_last_record
from core.report_writer import create_traffic_report
from core.traffic_system import TrafficSystem
from gui.common import APP_TITLE, TopBar, apply_app_icon, maximize_window

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
DOC_OUTPUT_DIR = os.path.join(BASE_DIR, "Doc_output")
DISPLAY_SIZE = (800, 450)


class AdminGUI(ctk.CTk):
    def __init__(self, user):
        super().__init__()
        self.user = user

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1300x850")
        apply_app_icon(self)
        maximize_window(self)

        self.traffic_system = TrafficSystem()

        self.video_path = None
        self.output_dir = None
        self.cap = None
        self.writer = None
        self.is_running = False
        self.lanes = None
        self.orig_size = None
        self.logout_recorded = False
        self.current_output_path = None
        self.current_report_path = None
        self.report_saved = False
        self.frame_count = 0
        self.total_vehicle_detections = 0
        self.lane_totals = {}
        self.current_metadata = {}

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._setup_ui()

    def _setup_ui(self):
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        top_bar = TopBar(
            main_container,
            f"Admin Panel - {self.user['display_name']}",
            logout_command=self.logout,
            exit_command=self.exit_app,
        )
        top_bar.pack(fill="x", pady=(0, 10))

        content = ctk.CTkFrame(main_container)
        content.pack(fill="both", expand=True)

        left_panel = ctk.CTkFrame(content, width=350)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        ctk.CTkLabel(
            left_panel,
            text="Video Information",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(15, 20))

        select_btn = ctk.CTkButton(
            left_panel,
            text="Select Video File",
            command=self.select_video,
            height=38,
        )
        select_btn.pack(fill="x", padx=20, pady=5)

        self.video_label_info = ctk.CTkLabel(
            left_panel,
            text="No file selected",
            wraplength=300,
        )
        self.video_label_info.pack(padx=20, pady=(0, 15))

        self._required_label(left_panel, "Street Name").pack(fill="x", padx=20)
        self.street_entry = ctk.CTkEntry(left_panel, height=36)
        self.street_entry.pack(fill="x", padx=20, pady=(2, 15))

        self._required_label(left_panel, "Time Range").pack(fill="x", padx=20)
        self.time_entry = ctk.CTkEntry(left_panel, height=36, placeholder_text="Example: 14:00-15:00")
        self.time_entry.pack(fill="x", padx=20, pady=(2, 15))

        self._required_label(left_panel, "Output Folder").pack(fill="x", padx=20)
        output_btn = ctk.CTkButton(
            left_panel,
            text="Select Output Folder",
            command=self.select_output_dir,
            height=38,
        )
        output_btn.pack(fill="x", padx=20, pady=5)

        self.output_label_info = ctk.CTkLabel(
            left_panel,
            text="No output folder selected",
            wraplength=300,
        )
        self.output_label_info.pack(padx=20, pady=(0, 20))

        self.start_btn = ctk.CTkButton(
            left_panel,
            text="Start Processing",
            command=self.start_processing,
            height=42,
            fg_color="green",
            hover_color="darkgreen",
        )
        self.start_btn.pack(fill="x", padx=20, pady=(10, 5))

        self.stop_btn = ctk.CTkButton(
            left_panel,
            text="Stop",
            command=self.stop_button_clicked,
            height=38,
            fg_color="red",
            hover_color="darkred",
            state="disabled",
        )
        self.stop_btn.pack(fill="x", padx=20, pady=5)

        self.status_label = ctk.CTkLabel(left_panel, text="Status: Ready")
        self.status_label.pack(padx=20, pady=15)

        right_panel = ctk.CTkFrame(content)
        right_panel.pack(side="right", fill="both", expand=True)

        self.video_display = ctk.CTkLabel(right_panel, text="Processed video preview will appear here")
        self.video_display.pack(fill="both", expand=True, padx=15, pady=15)

    def _required_label(self, parent, label_text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(row, text=label_text, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=" *", text_color="red", anchor="w").pack(side="left")
        return row

    def select_video(self):
        path = filedialog.askopenfilename(
            title="Select Video File",
            initialdir=VIDEOS_DIR,
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")],
        )
        if path:
            self.video_path = path
            self.video_label_info.configure(text=f"Selected: {os.path.basename(path)}")

    def select_output_dir(self):
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        path = filedialog.askdirectory(title="Select Output Folder", initialdir=OUTPUTS_DIR)
        if path:
            self.output_dir = path
            self.output_label_info.configure(text=f"Output folder: {path}")

    def start_processing(self):
        if not self.video_path:
            messagebox.showerror("Error", "Please select a video file first.")
            return
        street = self.street_entry.get().strip()
        video_time = self.time_entry.get().strip()

        if not street:
            messagebox.showerror("Error", "Street Name is required.")
            return
        if not video_time:
            messagebox.showerror("Error", "Time Range is required.")
            return
        if not self.output_dir:
            messagebox.showerror("Error", "Please select an output folder first.")
            return

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Unable to open the selected video.")
            return

        orig_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.orig_size = (orig_w, orig_h)

        self.lanes = self.traffic_system.load_lanes(self.video_path)
        if self.lanes is None:
            self.status_label.configure(text="Status: No lane file found. Counting total vehicles only.")

        safe_street = self._safe_filename(street)
        output_path = self._unique_output_path(self.output_dir, safe_street)
        output_filename = os.path.basename(output_path)
        report_path = self._unique_report_path(safe_street)
        self._reset_report_state(output_path, report_path, street, video_time)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 20.0
        self.writer = cv2.VideoWriter(output_path, fourcc, fps, DISPLAY_SIZE)

        update_last_record(
            username=self.user["username"],
            street_name=street,
            video_time=video_time,
            output_path=output_path,
            video_path=self.video_path,
        )

        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text=f"Status: Processing | Output: {output_filename}")

        self._update_frame()

    def _reset_report_state(self, output_path, report_path, street, video_time):
        self.current_output_path = output_path
        self.current_report_path = report_path
        self.report_saved = False
        self.frame_count = 0
        self.total_vehicle_detections = 0
        self.lane_totals = {lane_name: 0 for lane_name in self.lanes} if self.lanes else {}
        self.current_metadata = {
            "admin": self.user["display_name"],
            "street_name": street,
            "video_time": video_time,
            "video_path": self.video_path,
            "output_path": output_path,
        }

    @staticmethod
    def _safe_filename(value):
        invalid_chars = '<>:"/\\|?*'
        cleaned = "".join("_" if ch in invalid_chars else ch for ch in value).strip()
        cleaned = cleaned.rstrip(". ")
        return cleaned or "output"

    @staticmethod
    def _unique_output_path(output_dir, safe_street):
        base_name = safe_street or "output"
        output_path = os.path.join(output_dir, f"{base_name}.mp4")
        if not os.path.exists(output_path):
            return output_path

        counter = 2
        while True:
            output_path = os.path.join(output_dir, f"{base_name}_{counter}.mp4")
            if not os.path.exists(output_path):
                return output_path
            counter += 1

    @staticmethod
    def _unique_report_path(safe_street):
        os.makedirs(DOC_OUTPUT_DIR, exist_ok=True)
        base_name = safe_street or "output"
        report_path = os.path.join(DOC_OUTPUT_DIR, f"{base_name}.xlsx")
        if not os.path.exists(report_path):
            return report_path

        counter = 2
        while True:
            report_path = os.path.join(DOC_OUTPUT_DIR, f"{base_name}_{counter}.xlsx")
            if not os.path.exists(report_path):
                return report_path
            counter += 1

    def stop_button_clicked(self):
        self.stop_processing(show_saved_message=True, reset_form=True)

    def stop_processing(self, show_saved_message=False, reset_form=False):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.writer:
            self.writer.release()
            self.writer = None
        self._save_excel_report()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="Status: Stopped")
        if show_saved_message and self.current_output_path:
            messagebox.showinfo("Saved", "Video and Excel report were saved successfully.")
        if reset_form:
            self._clear_form()

    def _clear_form(self):
        self.video_path = None
        self.output_dir = None
        self.lanes = None
        self.orig_size = None
        self.current_output_path = None
        self.current_report_path = None
        self.current_metadata = {}
        self.video_label_info.configure(text="No file selected")
        self.output_label_info.configure(text="No output folder selected")
        self.street_entry.delete(0, "end")
        self.time_entry.delete(0, "end")
        self.video_display.configure(image="", text="Processed video preview will appear here")
        self.video_display.image = None
        self.status_label.configure(text="Status: Ready")

    def _save_excel_report(self):
        if self.report_saved or not self.current_report_path or self.frame_count == 0:
            return

        create_traffic_report(
            report_path=self.current_report_path,
            metadata=self.current_metadata,
            frame_count=self.frame_count,
            total_vehicle_detections=self.total_vehicle_detections,
            lane_totals=self.lane_totals,
        )
        if self.current_output_path:
            average_total = round(self.total_vehicle_detections / self.frame_count, 2) if self.frame_count else 0
            lane_averages = {
                lane_name: round(total / self.frame_count, 2) if self.frame_count else 0
                for lane_name, total in self.lane_totals.items()
            }
            attach_report_path(
                self.current_output_path,
                self.current_report_path,
                {
                    "frame_count": self.frame_count,
                    "total_vehicle_detections": self.total_vehicle_detections,
                    "average_vehicles_per_frame": average_total,
                    "lane_averages": lane_averages,
                },
            )
        self.report_saved = True

    def _update_frame(self):
        if not self.is_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.stop_processing(reset_form=True)
            messagebox.showinfo("Finished", "Video processing finished and the output was saved.")
            return

        annotated, total_count, lane_counts = self.traffic_system.process_frame(
            frame,
            lanes=self.lanes,
            display_size=self.orig_size,
            orig_size=self.orig_size,
        )
        self._update_report_stats(total_count, lane_counts)

        annotated = cv2.resize(annotated, DISPLAY_SIZE)

        if self.writer is not None:
            self.writer.write(annotated)

        frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(image=img)
        self.video_display.configure(image=photo, text="")
        self.video_display.image = photo

        self.after(15, self._update_frame)

    def _update_report_stats(self, total_count, lane_counts):
        self.frame_count += 1
        self.total_vehicle_detections += total_count
        if lane_counts:
            for lane_name, count in lane_counts.items():
                self.lane_totals[lane_name] = self.lane_totals.get(lane_name, 0) + count

    def on_closing(self):
        self.stop_processing()
        self._record_logout_once()
        self.destroy()

    def logout(self):
        self.stop_processing()
        self._record_logout_once()
        self.destroy()

        from gui.login_window import LoginWindow

        app = LoginWindow()
        app.mainloop()

    def exit_app(self):
        self.stop_processing()
        self._record_logout_once()
        self.destroy()

    def _record_logout_once(self):
        if self.logout_recorded:
            return
        record_logout(self.user["username"])
        self.logout_recorded = True
