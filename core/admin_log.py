"""Admin login and processing log storage."""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGINS_PATH = os.path.join(BASE_DIR, "data", "admin_logins.json")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
DOC_OUTPUT_DIR = os.path.join(BASE_DIR, "Doc_output")
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
REPORT_EXTENSIONS = {".xlsx"}


def _load_all():
    if not os.path.exists(LOGINS_PATH):
        return []
    with open(LOGINS_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_all(records):
    with open(LOGINS_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def record_login(username, display_name):
    records = _load_all()
    records.append(
        {
            "username": username,
            "display_name": display_name,
            "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "logout_time": None,
            "street_name": None,
            "video_time": None,
            "output_path": None,
            "video_path": None,
            "report_path": None,
        }
    )
    _save_all(records)
    return len(records) - 1


def update_last_record(username, street_name, video_time, output_path, video_path):
    records = _load_all()
    latest_user_record = None

    for record in reversed(records):
        if record["username"] == username:
            latest_user_record = record
            break

    if latest_user_record is None:
        latest_user_record = {
            "username": username,
            "display_name": username,
            "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "logout_time": None,
            "street_name": None,
            "video_time": None,
            "output_path": None,
            "video_path": None,
            "report_path": None,
        }
        records.append(latest_user_record)

    if latest_user_record.get("output_path"):
        latest_user_record = {
            "username": latest_user_record.get("username", username),
            "display_name": latest_user_record.get("display_name", username),
            "login_time": latest_user_record.get("login_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "logout_time": latest_user_record.get("logout_time"),
            "street_name": None,
            "video_time": None,
            "output_path": None,
            "video_path": None,
            "report_path": None,
        }
        records.append(latest_user_record)

    latest_user_record["street_name"] = street_name
    latest_user_record["video_time"] = video_time
    latest_user_record["output_path"] = output_path
    latest_user_record["video_path"] = video_path
    _save_all(records)


def attach_report_path(output_path, report_path, report_stats=None):
    records = _load_all()
    for record in reversed(records):
        if record.get("output_path") == output_path:
            record["report_path"] = report_path
            if report_stats is not None:
                record["report_stats"] = report_stats
            break
    _save_all(records)


def record_logout(username):
    """Attach logout time to all open records for an admin session."""
    records = _load_all()
    logout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for record in reversed(records):
        if record["username"] == username and not record.get("logout_time"):
            record["logout_time"] = logout_time
    _save_all(records)


def get_all_records():
    """Return all records with the newest entries first."""
    records = _load_all()
    return list(reversed(records))


def clear_all_records(delete_output_videos=False):
    """Remove all admin activity records and optionally delete saved outputs."""
    if delete_output_videos:
        deleted_paths = set()
        for record in _load_all():
            for field_name in ("output_path", "report_path"):
                file_path = record.get(field_name)
                if not file_path or not os.path.exists(file_path):
                    continue
                try:
                    os.remove(file_path)
                    deleted_paths.add(os.path.abspath(file_path))
                except OSError:
                    pass

        _delete_files_in_folder(OUTPUTS_DIR, VIDEO_EXTENSIONS, deleted_paths)
        _delete_files_in_folder(DOC_OUTPUT_DIR, REPORT_EXTENSIONS, deleted_paths)

    _save_all([])


def _delete_files_in_folder(folder_path, allowed_extensions, deleted_paths):
    if not os.path.isdir(folder_path):
        return

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.abspath(file_path) in deleted_paths:
            continue
        if not os.path.isfile(file_path):
            continue
        if os.path.splitext(filename)[1].lower() not in allowed_extensions:
            continue
        try:
            os.remove(file_path)
        except OSError:
            pass


def prune_unplayable_records():
    """Remove records whose saved output video is missing or not registered."""
    records = _load_all()
    playable_records = [
        record
        for record in records
        if record.get("output_path") and os.path.exists(record["output_path"])
    ]
    removed_count = len(records) - len(playable_records)
    if removed_count:
        _save_all(playable_records)
    return removed_count
