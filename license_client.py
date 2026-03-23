"""
license_client.py  –  Online License Activation for College Result Analyzer
Place this file in the SAME folder as app.py and pdf_parser.py.

HOW IT WORKS:
  • First launch      → GUI dialog asks for license key → activates with server
  • Every launch      → validates key silently in background
  • Every launch      → checks for new version → shows update popup if available
  • If revoked        → clears saved key → asks to enter new key
  • If expired        → clears saved key → asks to enter new key
  • If server down    → shows warning but still allows app to open
  • College name      → saved locally and used in Excel export header
"""

from __future__ import annotations
import hashlib, json, os, platform, sys, tkinter as tk, webbrowser
from tkinter import messagebox
import requests

# ─────────────────────────── CONFIG ────────────────────────────────────────
SERVER_URL      = "https://license-server-p81y.onrender.com"
LICENSE_FILE    = os.path.join(os.path.expanduser("~"), ".result_analyzer_license.dat")
APP_NAME        = "College Result Analyzer"
CURRENT_VERSION = "1.0.0"   # ← change this every time you build a new EXE
TIMEOUT         = 10
# ───────────────────────────────────────────────────────────────────────────

_REACTIVATE_MESSAGES = {
    "license revoked",
    "this license has been revoked",
    "invalid license key",
    "license expired",
    "license has expired",
}


def _machine_id() -> str:
    raw = f"{platform.node()}|{platform.system()}|{platform.machine()}|{platform.processor()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _save_license(key: str, college: str = "") -> None:
    with open(LICENSE_FILE, "w") as f:
        json.dump({"key": key, "college": college}, f)


def _clear_license() -> None:
    try:
        if os.path.exists(LICENSE_FILE):
            os.remove(LICENSE_FILE)
    except Exception:
        pass


def _load_license() -> dict:
    try:
        with open(LICENSE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def get_college_name() -> str:
    """Call anywhere in app.py to get the college name for Excel header."""
    return _load_license().get("college", "")


def _post(endpoint: str, payload: dict) -> dict:
    try:
        r = requests.post(
            f"{SERVER_URL.rstrip('/')}/{endpoint}",
            json=payload,
            timeout=TIMEOUT,
        )
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Cannot reach license server.\nCheck your internet connection.", "type": "network"}
    except Exception as e:
        return {"status": "error", "message": str(e), "type": "network"}


def _should_reactivate(message: str) -> bool:
    msg_lower = message.lower()
    return any(trigger in msg_lower for trigger in _REACTIVATE_MESSAGES)


# ─────────────────────── Update Checker ────────────────────────────────────

def _check_for_updates() -> None:
    """
    Silently checks server for latest version.
    If newer version exists → shows a popup with download button.
    If same version or server unreachable → does nothing.
    """
    try:
        r = requests.get(f"{SERVER_URL.rstrip('/')}/version", timeout=5)
        data = r.json()
        latest  = data.get("latest", CURRENT_VERSION)
        download = data.get("download", "")
        message  = data.get("message", "A new version is available!")

        if latest == CURRENT_VERSION:
            return  # Already up to date — do nothing

        # ── Show update popup ──
        _tmp = tk.Tk()
        _tmp.withdraw()

        response = messagebox.askyesno(
            APP_NAME + " – Update Available 🆕",
            f"New Version Available!\n\n"
            f"  Current version : {CURRENT_VERSION}\n"
            f"  New version     : {latest}\n\n"
            f"{message}\n\n"
            f"Click YES to open the download page now.\n"
            f"Click NO to continue with current version.",
            parent=_tmp,
        )
        _tmp.destroy()

        if response and download:
            webbrowser.open(download)   # Opens Google Drive / website in browser

    except Exception:
        pass   # Silent fail — never block the app for update check


# ──────────────────────── GUI Activation Dialog ────────────────────────────

class _ActivationDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, message: str = ""):
        super().__init__(parent)
        self.result: str | None = None
        self.college: str = ""

        self.title(f"{APP_NAME} – Activation")
        self.resizable(False, False)
        self.configure(bg="#0F172A")
        self.grab_set()

        w, h = 480, 320 if message else 280
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        tk.Label(
            self, text="⚡ " + APP_NAME,
            bg="#0F172A", fg="#F8FAFC",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(24, 2))

        if message:
            tk.Label(
                self,
                text=f"⚠  {message}",
                bg="#3B0A0A", fg="#FCA5A5",
                font=("Segoe UI", 10, "bold"),
                wraplength=420, justify="center",
                padx=10, pady=8,
            ).pack(fill="x", padx=30, pady=(4, 4))
            tk.Label(
                self, text="Please enter your new license key.",
                bg="#0F172A", fg="#94A3B8",
                font=("Segoe UI", 11),
            ).pack(pady=(4, 12))
        else:
            tk.Label(
                self, text="Please enter your license key to activate.",
                bg="#0F172A", fg="#94A3B8",
                font=("Segoe UI", 11),
            ).pack(pady=(0, 16))

        tk.Label(
            self, text="License Key",
            bg="#0F172A", fg="#CBD5E1",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x", padx=40)

        self._key_var = tk.StringVar()
        entry = tk.Entry(
            self,
            textvariable=self._key_var,
            font=("Courier New", 13),
            bg="#1E293B", fg="#38BDF8",
            insertbackground="#38BDF8",
            relief="flat", bd=6,
            width=34,
            justify="center",
        )
        entry.pack(padx=40, ipady=6)
        entry.focus_set()
        entry.bind("<Return>", lambda e: self._on_activate())

        self._status_var = tk.StringVar(value="")
        tk.Label(
            self,
            textvariable=self._status_var,
            bg="#0F172A", fg="#F97316",
            font=("Segoe UI", 10),
        ).pack(pady=(8, 0))

        tk.Button(
            self,
            text="  Activate  ",
            command=self._on_activate,
            bg="#2563EB", fg="white",
            activebackground="#1D4ED8",
            font=("Segoe UI", 12, "bold"),
            relief="flat", bd=0, padx=18, pady=8, cursor="hand2",
        ).pack(pady=(10, 0))

    def _on_activate(self):
        key = self._key_var.get().strip().upper()
        if not key:
            self._status_var.set("⚠  Please enter a license key.")
            return
        self._status_var.set("🔄  Activating, please wait…")
        self.update_idletasks()

        resp = _post("activate", {"key": key, "machine_id": _machine_id()})
        if resp.get("status") == "ok":
            self.college = resp.get("college", "")
            _save_license(key, self.college)
            self.result = key
            self.destroy()
        else:
            self._status_var.set(f"✖  {resp.get('message', 'Activation failed.')}")


# ─────────────────────── Activation Flow ───────────────────────────────────

def _show_activation_dialog(message: str = "") -> None:
    root = tk.Tk()
    root.withdraw()
    dlg = _ActivationDialog(root, message=message)
    root.wait_window(dlg)
    if dlg.result:
        root.destroy()
        return
    root.destroy()
    sys.exit(0)


# ─────────────────────── Public entry-point ────────────────────────────────

def check_license() -> None:
    """
    Call this ONCE at the very start of app.py (before building the GUI).
    Also checks for software updates on every launch.
    """
    saved = _load_license()
    saved_key = saved.get("key")

    if not saved_key:
        _show_activation_dialog()
        return

    resp = _post("validate", {"key": saved_key, "machine_id": _machine_id()})

    if resp.get("status") == "ok":
        # Refresh college name
        college = resp.get("college", saved.get("college", ""))
        _save_license(saved_key, college)

        # ── Check for software updates ──
        _check_for_updates()
        return

    msg = resp.get("message", "Unknown error")
    err_type = resp.get("type", "")

    if err_type == "network":
        _tmp = tk.Tk(); _tmp.withdraw()
        messagebox.showwarning(
            APP_NAME + " – No Connection",
            f"Could not reach license server.\n\n{msg}\n\n"
            "The app will open, but please check your internet connection.",
            parent=_tmp,
        )
        _tmp.destroy()
        return

    if _should_reactivate(msg):
        _clear_license()
        _show_activation_dialog(message=msg)
        return

    _tmp = tk.Tk(); _tmp.withdraw()
    messagebox.showerror(
        APP_NAME + " – License Error",
        f"License check failed:\n\n{msg}\n\nPlease contact support.",
        parent=_tmp,
    )
    _tmp.destroy()
    sys.exit(1)
