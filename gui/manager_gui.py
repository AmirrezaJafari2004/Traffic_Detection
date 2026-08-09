"""System manager dashboard.

The manager view plays saved admin output videos without running detection
again. At most two videos are visible at a time; the manager can swap each
visible slot with any saved output.
"""

import os
from tkinter import messagebox

import cv2
import customtkinter as ctk
from PIL import Image, ImageTk

from core.admin_log import clear_all_records, get_all_records, prune_unplayable_records
from gui.common import APP_TITLE, TopBar, apply_app_icon, maximize_window

DISPLAY_SIZES = {
    1: (1120, 640),
    2: (560, 370),
}
MAX_VISIBLE_VIDEOS = 2


class VideoSlot:
    def __init__(self, label_widget, video_path, display_size, generation):
        self.label_widget = label_widget
        self.video_path = video_path
        self.display_size = display_size
        self.generation = generation
        self.cap = None
        self.running = False
        self.delay_ms = 30


class ManagerGUI(ctk.CTk):
    def __init__(self, user):
        super().__init__()
        self.user = user

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1500x900")
        apply_app_icon(self)
        maximize_window(self)

        self.video_slots = []
        self.playback_generation = 0
        self.playable_records = []
        self.visible_indices = []
        self.summary_frame = None
        self.video_grid_container = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._setup_ui()
        self._refresh_dashboard()

    def _setup_ui(self):
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        top_bar = TopBar(
            main_container,
            f"System Manager Panel - {self.user['display_name']}",
            logout_command=self.logout,
            exit_command=self.exit_app,
        )
        top_bar.pack(fill="x", pady=(0, 10))

        content = ctk.CTkFrame(main_container)
        content.pack(fill="both", expand=True)

        side_panel = ctk.CTkFrame(content, width=380)
        side_panel.pack(side="right", fill="y", padx=(10, 0))
        side_panel.pack_propagate(False)

        ctk.CTkLabel(
            side_panel,
            text="Admin Activity Log",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(15, 5))

        refresh_btn = ctk.CTkButton(
            side_panel,
            text="Refresh Dashboard",
            command=self._refresh_dashboard,
            height=34,
        )
        refresh_btn.pack(fill="x", padx=15, pady=(0, 10))

        clear_btn = ctk.CTkButton(
            side_panel,
            text="Clear Admin Logs",
            command=self._clear_admin_logs,
            height=34,
            fg_color="darkred",
            hover_color="#7f1d1d",
        )
        clear_btn.pack(fill="x", padx=15, pady=(0, 10))

        self.admin_scroll = ctk.CTkScrollableFrame(side_panel)
        self.admin_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.video_area = ctk.CTkFrame(content)
        self.video_area.pack(side="left", fill="both", expand=True)

        self.summary_frame = ctk.CTkFrame(self.video_area)
        self.summary_frame.pack(fill="x", padx=8, pady=(8, 0))

        self.video_grid_container = ctk.CTkFrame(self.video_area)
        self.video_grid_container.pack(fill="both", expand=True)

    def _refresh_dashboard(self):
        self._stop_videos()
        prune_unplayable_records()
        self.playback_generation += 1
        self.playable_records = self._get_playable_records()
        self.visible_indices = list(range(min(MAX_VISIBLE_VIDEOS, len(self.playable_records))))
        self._refresh_summary()
        self._refresh_admin_log()
        self._show_visible_outputs()

    def _refresh_summary(self):
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        summary = self._build_summary()
        cards = [
            ("Processed Videos", str(summary["video_count"])),
            ("Detected Vehicles", str(summary["vehicle_total"])),
            ("Busiest Street", summary["busiest_street"]),
            ("Latest Record", summary["latest_record"]),
        ]

        for col, (label, value) in enumerate(cards):
            self.summary_frame.grid_columnconfigure(col, weight=1)
            card = ctk.CTkFrame(self.summary_frame)
            card.grid(row=0, column=col, sticky="ew", padx=6, pady=6)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12)).pack(pady=(8, 2))
            ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=18, weight="bold"), wraplength=190).pack(
                pady=(0, 8),
                padx=8,
            )

    def _build_summary(self):
        vehicle_total = 0
        street_totals = {}

        for record in self.playable_records:
            stats = record.get("report_stats") or {}
            detections = int(stats.get("total_vehicle_detections") or 0)
            vehicle_total += detections

            street = record.get("street_name") or "Unknown"
            street_totals[street] = street_totals.get(street, 0) + detections

        busiest_street = "-"
        if street_totals:
            street, total = max(street_totals.items(), key=lambda item: item[1])
            busiest_street = f"{street} ({total})" if total else street

        latest_record = "-"
        if self.playable_records:
            latest_record = self.playable_records[0].get("login_time") or "-"

        return {
            "video_count": len(self.playable_records),
            "vehicle_total": vehicle_total,
            "busiest_street": busiest_street,
            "latest_record": latest_record,
        }

    def _refresh_admin_log(self):
        for widget in self.admin_scroll.winfo_children():
            widget.destroy()

        records = self.playable_records

        if not records:
            ctk.CTkLabel(self.admin_scroll, text="No playable admin outputs are available.").pack(pady=10)
            return

        for record in records:
            output_path = record.get("output_path") or "-"
            video_path = record.get("video_path") or "-"
            street_name = record.get("street_name") or "-"
            video_time = record.get("video_time") or "-"
            logout_time = record.get("logout_time") or "-"

            item = ctk.CTkFrame(self.admin_scroll)
            item.pack(fill="x", pady=5)

            text = (
                f"Admin: {record.get('display_name', '-')}\n"
                f"Login: {record.get('login_time', '-')}\n"
                f"Logout: {logout_time}\n"
                f"Street: {street_name}\n"
                f"Time: {video_time}\n"
                f"Input: {os.path.basename(video_path) if video_path != '-' else '-'}\n"
                f"Output: {os.path.basename(output_path) if output_path != '-' else '-'}"
            )
            ctk.CTkLabel(item, text=text, anchor="w", justify="left", wraplength=320).pack(
                fill="x",
                padx=10,
                pady=10,
            )

            report_path = record.get("report_path")
            report_btn = ctk.CTkButton(
                item,
                text="Show Excel Report",
                command=lambda path=report_path: self._show_excel_report(path),
                height=30,
                state="normal" if report_path and os.path.exists(report_path) else "disabled",
            )
            report_btn.pack(fill="x", padx=10, pady=(0, 10))

    @staticmethod
    def _get_playable_records():
        records = []
        seen_output_paths = set()
        for record in get_all_records():
            output_path = record.get("output_path")
            if not output_path or not os.path.exists(output_path):
                continue

            normalized_path = os.path.normcase(os.path.abspath(output_path))
            if normalized_path in seen_output_paths:
                continue

            seen_output_paths.add(normalized_path)
            records.append(record)

        return records

    def _show_visible_outputs(self):
        self._stop_videos()
        self.playback_generation += 1

        for widget in self.video_grid_container.winfo_children():
            widget.destroy()

        if not self.playable_records:
            ctk.CTkLabel(
                self.video_grid_container,
                text="No saved output videos are available yet.",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(expand=True)
            return

        count = len(self.visible_indices)
        display_size = DISPLAY_SIZES[count]

        grid = ctk.CTkFrame(self.video_grid_container)
        grid.pack(fill="both", expand=True, padx=8, pady=8)

        if count == 1:
            layout = [(0, 0)]
        else:
            layout = [(0, 0), (0, 1)]

        grid.grid_rowconfigure(0, weight=1)
        for col in range(2):
            grid.grid_columnconfigure(col, weight=1)

        self.video_slots = []
        for slot_index, record_index in enumerate(self.visible_indices):
            record = self.playable_records[record_index]
            row, col = layout[slot_index]
            cell = ctk.CTkFrame(grid)
            columnspan = 2 if count == 1 else 1
            cell.grid(row=row, column=col, columnspan=columnspan, sticky="nsew", padx=8, pady=8)

            title = self._format_video_title(record)
            ctk.CTkLabel(cell, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(8, 4))

            if len(self.playable_records) > 1:
                options = [self._option_label(i, item) for i, item in enumerate(self.playable_records)]
                option_menu = ctk.CTkOptionMenu(
                    cell,
                    values=options,
                    command=lambda value, s=slot_index: self._replace_visible_slot(s, value),
                    width=320,
                )
                option_menu.set(self._option_label(record_index, record))
                option_menu.pack(pady=(0, 6))

            video_label = ctk.CTkLabel(cell, text="Loading video...")
            video_label.pack(fill="both", expand=True, padx=8, pady=8)

            slot = VideoSlot(video_label, record["output_path"], display_size, self.playback_generation)
            self.video_slots.append(slot)
            self._start_slot(slot_index)

    @staticmethod
    def _format_video_title(record):
        street = record.get("street_name") or "Unknown street"
        video_time = record.get("video_time") or "Unknown time"
        admin = record.get("display_name") or record.get("username") or "Admin"
        return f"{street} | {video_time} | {admin}"

    def _option_label(self, index, record):
        output_name = os.path.basename(record.get("output_path") or f"Output {index + 1}")
        street = record.get("street_name") or "Unknown street"
        return f"{index + 1}. {street} - {output_name}"

    def _replace_visible_slot(self, slot_index, selected_label):
        selected_index = self._index_from_option_label(selected_label)
        if selected_index is None or slot_index >= len(self.visible_indices):
            return

        current_index = self.visible_indices[slot_index]
        if selected_index == current_index:
            return

        if selected_index in self.visible_indices:
            other_slot = self.visible_indices.index(selected_index)
            self.visible_indices[other_slot] = current_index

        self.visible_indices[slot_index] = selected_index
        self._show_visible_outputs()

    @staticmethod
    def _index_from_option_label(label):
        try:
            return int(label.split(".", 1)[0]) - 1
        except (ValueError, IndexError):
            return None

    def _start_slot(self, index):
        slot = self.video_slots[index]
        cap = cv2.VideoCapture(slot.video_path)
        if not cap.isOpened():
            slot.label_widget.configure(text=f"Unable to open video:\n{slot.video_path}")
            return

        slot.cap = cap
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        slot.delay_ms = max(1, int(1000 / fps))
        slot.running = True
        self._update_slot(index, slot.generation)

    def _update_slot(self, index, generation):
        if index >= len(self.video_slots):
            return

        slot = self.video_slots[index]
        if generation != self.playback_generation or generation != slot.generation:
            return
        if not slot.running or slot.cap is None:
            return

        ret, frame = slot.cap.read()
        if not ret:
            slot.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = slot.cap.read()
            if not ret:
                slot.label_widget.configure(text="Unable to read video frames.")
                return

        annotated = cv2.resize(frame, slot.display_size)
        frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(image=img)
        slot.label_widget.configure(image=photo, text="")
        slot.label_widget.image = photo

        self.after(slot.delay_ms, lambda: self._update_slot(index, generation))

    def _stop_videos(self):
        for slot in self.video_slots:
            slot.running = False
            if slot.cap is not None:
                slot.cap.release()
                slot.cap = None
        self.video_slots = []

    def on_closing(self):
        self._stop_videos()
        self.destroy()

    def _clear_admin_logs(self):
        confirmed = messagebox.askyesno(
            "Clear Admin Logs",
            "Are you sure you want to clear all admin activity logs and delete saved output videos?",
        )
        if not confirmed:
            return

        clear_all_records(delete_output_videos=True)
        self._refresh_dashboard()

    def _show_excel_report(self, report_path):
        if not report_path or not os.path.exists(report_path):
            messagebox.showinfo("Excel Report", "No Excel report is available for this video.")
            return

        try:
            os.startfile(report_path)
        except OSError:
            messagebox.showinfo("Excel Report", f"Report saved at:\n{report_path}")

    def logout(self):
        self._stop_videos()
        self.destroy()

        from gui.login_window import LoginWindow

        app = LoginWindow()
        app.mainloop()

    def exit_app(self):
        self._stop_videos()
        self.destroy()
