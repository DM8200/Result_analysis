"""
license_client.py  –  Online License Activation for College Result Analyzer

HOW IT WORKS:
  Windows/Mac → GUI activation dialog (tkinter)
  Linux       → Terminal activation (no tkinter = no segfault)

On Linux first run:
  1. Run: ResultAnalyzer --activate
  2. Enter your license key
  3. Then run: ResultAnalyzer  (opens normally)
"""

from __future__ import annotations
import hashlib, json, os, platform, sys, webbrowser
import requests

# ─────────────────────────── CONFIG ────────────────────────────────────────
SERVER_URL      = "https://license-server-p81y.onrender.com"
LICENSE_FILE    = os.path.join(os.path.expanduser("~"), ".result_analyzer_license.dat")
APP_NAME        = "College Result Analyzer"
CURRENT_VERSION = "1.0.0"
TIMEOUT         = 10
# ───────────────────────────────────────────────────────────────────────────

IS_LINUX   = sys.platform.startswith("linux")
IS_FROZEN  = getattr(sys, "frozen", False)

_REACTIVATE_MESSAGES = {
    "license revoked",
    "this license has been revoked",
    "invalid license key",
    "machine id mismatch",
    "license expired",
    "license has expired",
}


# ─────────────────────── Core helpers ──────────────────────────────────────

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
        return {"status": "error", "message": "Cannot reach license server. Check internet.", "type": "network"}
    except Exception as e:
        return {"status": "error", "message": str(e), "type": "network"}

def _should_reactivate(message: str) -> bool:
    return any(t in message.lower() for t in _REACTIVATE_MESSAGES)


# ─────────────────────── Linux Terminal Activation ─────────────────────────

def _linux_activate() -> None:
    """Activate via terminal — no tkinter needed."""
    print("\n" + "="*55)
    print(f"  {APP_NAME}")
    print("  License Activation")
    print("="*55)
    try:
        key = input("\n  Enter your license key: ").strip().upper()
        if not key:
            print("\n  No key entered. Exiting.")
            sys.exit(1)

        print("\n  Activating, please wait...")
        resp = _post("activate", {"key": key, "machine_id": _machine_id()})

        if resp.get("status") == "ok":
            college = resp.get("college", "")
            _save_license(key, college)
            print(f"\n  Activation successful!")
            print(f"  College : {college}")
            print(f"  Plan    : {resp.get('plan', '')}")
            print(f"\n  Now run: ResultAnalyzer")
            print("="*55 + "\n")
            sys.exit(0)
        else:
            print(f"\n  Error: {resp.get('message', 'Activation failed')}")
            print("="*55 + "\n")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n  Cancelled.")
        sys.exit(1)


def _linux_validate(saved_key: str) -> bool:
    """Validate silently on Linux — returns True if valid."""
    resp = _post("validate", {"key": saved_key, "machine_id": _machine_id()})
    if resp.get("status") == "ok":
        college = resp.get("college", "")
        _save_license(saved_key, college)
        return True

    msg      = resp.get("message", "")
    err_type = resp.get("type", "")

    if err_type == "network":
        # No internet — allow app to open
        print(f"WARNING: Cannot reach license server. {msg}", file=sys.stderr)
        return True

    if _should_reactivate(msg):
        _clear_license()
        print(f"\n  License Error: {msg}", file=sys.stderr)
        print(f"  Please re-activate: ResultAnalyzer --activate", file=sys.stderr)
        sys.exit(1)

    print(f"  License Error: {msg}", file=sys.stderr)
    sys.exit(1)


# ─────────────────────── Windows/Mac GUI Activation ────────────────────────

def _gui_activate(message: str = "") -> None:
    """GUI activation dialog for Windows/Mac."""
    import tkinter as tk
    from tkinter import messagebox
    import gc

    class _Dialog(tk.Toplevel):
        def __init__(self, parent):
            super().__init__(parent)
            self.activated = False
            self.college   = ""
            self.title(f"{APP_NAME} – Activation")
            self.resizable(False, False)
            self.configure(bg="#0F172A")
            self.grab_set()
            self.protocol("WM_DELETE_WINDOW", self._close)

            w, h = 480, 320 if message else 280
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

            tk.Label(self, text="⚡ " + APP_NAME,
                     bg="#0F172A", fg="#F8FAFC",
                     font=("Segoe UI", 18, "bold")).pack(pady=(24, 2))

            if message:
                tk.Label(self, text=f"⚠  {message}",
                         bg="#3B0A0A", fg="#FCA5A5",
                         font=("Segoe UI", 10, "bold"),
                         wraplength=420, justify="center",
                         padx=10, pady=8).pack(fill="x", padx=30, pady=(4, 4))
                tk.Label(self, text="Please enter your new license key.",
                         bg="#0F172A", fg="#94A3B8",
                         font=("Segoe UI", 11)).pack(pady=(4, 12))
            else:
                tk.Label(self, text="Please enter your license key to activate.",
                         bg="#0F172A", fg="#94A3B8",
                         font=("Segoe UI", 11)).pack(pady=(0, 16))

            tk.Label(self, text="License Key",
                     bg="#0F172A", fg="#CBD5E1",
                     font=("Segoe UI", 10, "bold"),
                     anchor="w").pack(fill="x", padx=40)

            self._kv = tk.StringVar()
            e = tk.Entry(self, textvariable=self._kv,
                         font=("Courier New", 13),
                         bg="#1E293B", fg="#38BDF8",
                         insertbackground="#38BDF8",
                         relief="flat", bd=6, width=34,
                         justify="center")
            e.pack(padx=40, ipady=6)
            e.focus_set()
            e.bind("<Return>", lambda _: self._activate())

            self._sv = tk.StringVar(value="")
            tk.Label(self, textvariable=self._sv,
                     bg="#0F172A", fg="#F97316",
                     font=("Segoe UI", 10)).pack(pady=(8, 0))

            tk.Button(self, text="  Activate  ",
                      command=self._activate,
                      bg="#2563EB", fg="white",
                      activebackground="#1D4ED8",
                      font=("Segoe UI", 12, "bold"),
                      relief="flat", bd=0,
                      padx=18, pady=8,
                      cursor="hand2").pack(pady=(10, 0))

        def _close(self):
            self.activated = False
            self.destroy()

        def _activate(self):
            key = self._kv.get().strip().upper()
            if not key:
                self._sv.set("⚠  Please enter a license key.")
                return
            self._sv.set("🔄  Activating, please wait…")
            self.update_idletasks()
            resp = _post("activate", {"key": key, "machine_id": _machine_id()})
            if resp.get("status") == "ok":
                self.college   = resp.get("college", "")
                self.activated = True
                _save_license(key, self.college)
                self.destroy()
            else:
                self._sv.set(f"✖  {resp.get('message', 'Activation failed.')}")

    root = tk.Tk()
    root.withdraw()
    dlg = _Dialog(root)

    def _check():
        if dlg.winfo_exists():
            root.after(100, _check)
        else:
            root.quit()

    root.after(100, _check)
    root.mainloop()
    activated = getattr(dlg, "activated", False)
    try: root.destroy()
    except Exception: pass
    gc.collect()

    if not activated:
        sys.exit(0)


def _gui_validate(saved_key: str) -> None:
    """Validate with GUI error dialogs for Windows/Mac."""
    import tkinter as tk
    from tkinter import messagebox

    resp = _post("validate", {"key": saved_key, "machine_id": _machine_id()})

    if resp.get("status") == "ok":
        college = resp.get("college", "")
        _save_license(saved_key, college)
        _check_for_updates()
        return

    msg      = resp.get("message", "Unknown error")
    err_type = resp.get("type", "")

    if err_type == "network":
        _tmp = tk.Tk(); _tmp.withdraw()
        messagebox.showwarning(APP_NAME + " – No Connection",
                               f"Could not reach license server.\n\n{msg}\n\n"
                               "The app will open anyway.",
                               parent=_tmp)
        _tmp.destroy()
        return

    if _should_reactivate(msg):
        _clear_license()
        _gui_activate(message=msg)
        return

    _tmp = tk.Tk(); _tmp.withdraw()
    messagebox.showerror(APP_NAME + " – License Error",
                         f"License check failed:\n\n{msg}\n\nContact support.",
                         parent=_tmp)
    _tmp.destroy()
    sys.exit(1)


# ─────────────────────── Update Checker ────────────────────────────────────

def _check_for_updates() -> None:
    if IS_LINUX:
        return  # Skip update popup on Linux to avoid tkinter issues
    try:
        import tkinter as tk
        from tkinter import messagebox
        r       = requests.get(f"{SERVER_URL.rstrip('/')}/version", timeout=5)
        data    = r.json()
        latest  = data.get("latest", CURRENT_VERSION)
        dl      = data.get("download", "")
        msg     = data.get("message", "A new version is available!")
        if latest == CURRENT_VERSION:
            return
        _tmp = tk.Tk(); _tmp.withdraw()
        if messagebox.askyesno(APP_NAME + " – Update Available",
                               f"New version {latest} available!\n\n{msg}\n\n"
                               "Open download page?", parent=_tmp):
            webbrowser.open(dl)
        _tmp.destroy()
    except Exception:
        pass


# ─────────────────────── Public entry-point ────────────────────────────────

def check_license() -> None:
    """
    Call once at the top of app.py before building the GUI.

    Linux flow:
      - First time → user must run: ResultAnalyzer --activate
      - After that → validates silently, app opens normally

    Windows/Mac flow:
      - First time → GUI dialog appears
      - After that → validates silently, app opens normally
    """

    # ── Linux: handle --activate flag ──
    if IS_LINUX and "--activate" in sys.argv:
        _linux_activate()
        return

    saved     = _load_license()
    saved_key = saved.get("key")

    # ── Linux flow ──
    if IS_LINUX:
        if not saved_key:
            print("\n" + "="*55, file=sys.stderr)
            print(f"  {APP_NAME}", file=sys.stderr)
            print("  ACTIVATION REQUIRED", file=sys.stderr)
            print("="*55, file=sys.stderr)
            print("\n  Please activate first:", file=sys.stderr)
            print("  ResultAnalyzer --activate\n", file=sys.stderr)
            sys.exit(1)
        _linux_validate(saved_key)
        return

    # ── Windows / Mac flow ──
    if not saved_key:
        _gui_activate()
        return
    _gui_validate(saved_key)
