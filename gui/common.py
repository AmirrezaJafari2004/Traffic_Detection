"""Shared GUI components."""

from datetime import datetime
import os

import customtkinter as ctk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_ICON_PATH = os.path.join(BASE_DIR, "assets", "app_icon.ico")
APP_TITLE = "System Traffic Detection"


def apply_app_icon(window):
    
    if not os.path.exists(APP_ICON_PATH):
        return
    try:
        window.iconbitmap(APP_ICON_PATH)
    except Exception:
        pass


def maximize_window(window):
    
    def _maximize():
        try:
            window.state("zoomed")
        except Exception:
            try:
                width = window.winfo_screenwidth()
                height = window.winfo_screenheight()
                window.geometry(f"{width}x{height}+0+0")
            except Exception:
                pass

    window.after(100, _maximize)


class TopBar(ctk.CTkFrame):

    def __init__(self, parent, title_text, logout_command=None, exit_command=None):
        super().__init__(parent, height=70)
        self.pack_propagate(False)
        self.logout_command = logout_command
        self.exit_command = exit_command

        self.title_label = ctk.CTkLabel(
            self,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.pack(side="left", padx=20, pady=15)

        self.datetime_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=16),
        )
        self.datetime_label.pack(side="right", padx=20, pady=15)

        if self.exit_command is not None:
            self.exit_button = ctk.CTkButton(
                self,
                text="Exit",
                command=self.exit_command,
                width=80,
                height=34,
                fg_color="darkred",
                hover_color="#7f1d1d",
            )
            self.exit_button.pack(side="right", padx=(0, 10), pady=15)

        if self.logout_command is not None:
            self.logout_button = ctk.CTkButton(
                self,
                text="Logout",
                command=self.logout_command,
                width=90,
                height=34,
                fg_color="gray30",
                hover_color="gray20",
            )
            self.logout_button.pack(side="right", padx=(0, 10), pady=15)

        self._update_clock()

    def _update_clock(self):
        now = datetime.now().strftime("%A, %Y-%m-%d  |  %H:%M:%S")
        self.datetime_label.configure(text=now)
        self.after(1000, self._update_clock)
