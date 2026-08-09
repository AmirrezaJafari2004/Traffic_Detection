"""Login window for admin and system manager users."""

from tkinter import messagebox

import customtkinter as ctk

from core.admin_log import record_login
from core.auth import verify_login
from gui.common import APP_TITLE, apply_app_icon


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("520x520")
        self.resizable(False, False)
        apply_app_icon(self)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=42, pady=42)

        ctk.CTkLabel(
            container,
            text="Traffic Monitoring and Analysis",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(pady=(12, 38))

        ctk.CTkLabel(container, text="Username", anchor="w", font=ctk.CTkFont(size=15)).pack(fill="x")
        self.username_entry = ctk.CTkEntry(container, height=44, font=ctk.CTkFont(size=15))
        self.username_entry.pack(fill="x", pady=(4, 18))

        ctk.CTkLabel(container, text="Password", anchor="w", font=ctk.CTkFont(size=15)).pack(fill="x")
        self.password_entry = ctk.CTkEntry(container, height=44, show="*", font=ctk.CTkFont(size=15))
        self.password_entry.pack(fill="x", pady=(4, 32))

        self.password_entry.bind("<Return>", lambda e: self.attempt_login())

        login_btn = ctk.CTkButton(
            container,
            text="Login",
            command=self.attempt_login,
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        login_btn.pack(fill="x", pady=(0, 12))

        exit_btn = ctk.CTkButton(
            container,
            text="Exit",
            command=self.destroy,
            height=44,
            font=ctk.CTkFont(size=15),
            fg_color="gray30",
            hover_color="gray20",
        )
        exit_btn.pack(fill="x", pady=(0, 12))

        self.error_label = ctk.CTkLabel(container, text="", text_color="red")
        self.error_label.pack(pady=(5, 0))

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_label.configure(text="Please enter both username and password.")
            return

        user = verify_login(username, password)

        if user is None:
            self.error_label.configure(text="Invalid username or password.")
            return

        self.destroy()

        if user["role"] == "admin":
            record_login(user["username"], user["display_name"])
            from gui.admin_gui import AdminGUI

            app = AdminGUI(user)
        elif user["role"] == "manager":
            from gui.manager_gui import ManagerGUI

            app = ManagerGUI(user)
        else:
            messagebox.showerror("Error", "Invalid user role.")
            return

        app.mainloop()
