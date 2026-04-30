"""
license_client.py  –  Online License Activation for College Result Analyzer

HOW IT WORKS:
  Windows/Mac → GUI activation dialog
  Linux       → Terminal activation (no tkinter = no segfault)

FIXES:
  - Python 3.13 tkinter thread error fixed
  - Uses single persistent root window throughout
  - Proper cleanup to avoid gc thread errors
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

IS_LINUX = sys.platform.startswith("linux")

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
        return {"status": "error", "message": "Cannot reach license server.\nCheck your internet connection.", "type": "network"}
    except Exception as e:
        return {"status": "error", "message": str(e), "type": "network"}

def _should_reactivate(message: str) -> bool:
    return any(t in message.lower() for t in _REACTIVATE_MESSAGES)


# ─────────────────────── Linux Terminal Activation ─────────────────────────

def _linux_activate() -> None:
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
            _save_license(key, resp.get("college", ""))
            print(f"\n  Activation successful!")
            print(f"  College : {resp.get('college', '')}")
            print(f"  Plan    : {resp.get('plan', '')}")
            print(f"\n  Now run: ResultAnalyzer")
            print("="*55 + "\n")
            sys.exit(0)
        else:
            print(f"\n  Error: {resp.get('message', 'Activation failed')}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n  Cancelled.")
        sys.exit(1)

def _linux_validate(saved_key: str) -> None:
    resp = _post("validate", {"key": saved_key, "machine_id": _machine_id()})
    if resp.get("status") == "ok":
        _save_license(saved_key, resp.get("college", ""))
        return
    msg      = resp.get("message", "")
    err_type = resp.get("type", "")
    if err_type == "network":
        return  # Allow app to open offline
    if _should_reactivate(msg):
        _clear_license()
        print(f"\n  License Error: {msg}", file=sys.stderr)
        print(f"  Please re-activate: ResultAnalyzer --activate", file=sys.stderr)
        sys.exit(1)
    print(f"  License Error: {msg}", file=sys.stderr)
    sys.exit(1)


# ─────────────────────── Windows GUI Activation ────────────────────────────

def _run_gui_license() -> None:
    """
    Run the complete license GUI flow.
    Creates ONE tkinter root, handles everything, then destroys it.
    This avoids the Python 3.13 threading/gc error.
    """
    import tkinter as tk
    from tkinter import messagebox

    # ── Create single persistent root ──
    root = tk.Tk()
    root.withdraw()
    root.title(APP_NAME)

    saved     = _load_license()
    saved_key = saved.get("key")

    if saved_key:
        # ── Validate existing key ──
        resp = _post("validate", {"key": saved_key, "machine_id": _machine_id()})

        if resp.get("status") == "ok":
            _save_license(saved_key, resp.get("college", saved.get("college", "")))
            _check_for_updates_gui(root)
            root.destroy()
            return

        msg      = resp.get("message", "Unknown error")
        err_type = resp.get("type", "")

        if err_type == "network":
            messagebox.showwarning(
                APP_NAME + " – No Connection",
                f"Could not reach license server.\n\n{msg}\n\nThe app will open anyway.",
                parent=root,
            )
            root.destroy()
            return

        if _should_reactivate(msg):
            _clear_license()
            saved_key = None  # Fall through to activation dialog
        else:
            messagebox.showerror(
                APP_NAME + " – License Error",
                f"License check failed:\n\n{msg}\n\nContact support.",
                parent=root,
            )
            root.destroy()
            sys.exit(1)

    if not saved_key:
        # ── Show activation dialog ──
        _show_activation_dialog(root, message="" if not saved else
            _load_license().get("_last_error", ""))
        root.destroy()


def _show_activation_dialog(root, message: str = "") -> None:
    """Show activation dialog using existing root window."""
    import tkinter as tk

    activated = [False]  # Use list to allow mutation in nested function

    dialog = tk.Toplevel(root)
    dialog.title(f"{APP_NAME} – Activation")
    dialog.resizable(False, False)
    dialog.configure(bg="#0F172A")
    dialog.grab_set()
    dialog.protocol("WM_DELETE_WINDOW", lambda: _on_close(dialog, activated, root))

    w, h = 480, 320 if message else 280
    sw = dialog.winfo_screenwidth()
    sh = dialog.winfo_screenheight()
    dialog.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    tk.Label(
        dialog, text="⚡ " + APP_NAME,
        bg="#0F172A", fg="#F8FAFC",
        font=("Segoe UI", 18, "bold"),
    ).pack(pady=(24, 2))

    if message:
        tk.Label(
            dialog, text=f"⚠  {message}",
            bg="#3B0A0A", fg="#FCA5A5",
            font=("Segoe UI", 10, "bold"),
            wraplength=420, justify="center",
            padx=10, pady=8,
        ).pack(fill="x", padx=30, pady=(4, 4))
        tk.Label(
            dialog, text="Please enter your new license key.",
            bg="#0F172A", fg="#94A3B8",
            font=("Segoe UI", 11),
        ).pack(pady=(4, 12))
    else:
        tk.Label(
            dialog, text="Please enter your license key to activate.",
            bg="#0F172A", fg="#94A3B8",
            font=("Segoe UI", 11),
        ).pack(pady=(0, 16))

    tk.Label(
        dialog, text="License Key",
        bg="#0F172A", fg="#CBD5E1",
        font=("Segoe UI", 10, "bold"),
        anchor="w",
    ).pack(fill="x", padx=40)

    key_var = tk.StringVar()
    entry = tk.Entry(
        dialog, textvariable=key_var,
        font=("Courier New", 13),
        bg="#1E293B", fg="#38BDF8",
        insertbackground="#38BDF8",
        relief="flat", bd=6, width=34,
        justify="center",
    )
    entry.pack(padx=40, ipady=6)
    entry.focus_set()

    status_var = tk.StringVar(value="")
    tk.Label(
        dialog, textvariable=status_var,
        bg="#0F172A", fg="#F97316",
        font=("Segoe UI", 10),
    ).pack(pady=(8, 0))

    def _do_activate():
        key = key_var.get().strip().upper()
        if not key:
            status_var.set("⚠  Please enter a license key.")
            return
        status_var.set("🔄  Activating, please wait…")
        dialog.update_idletasks()
        resp = _post("activate", {"key": key, "machine_id": _machine_id()})
        if resp.get("status") == "ok":
            _save_license(key, resp.get("college", ""))
            activated[0] = True
            dialog.destroy()
        else:
            status_var.set(f"✖  {resp.get('message', 'Activation failed.')}")

    entry.bind("<Return>", lambda e: _do_activate())

    tk.Button(
        dialog, text="  Activate  ",
        command=_do_activate,
        bg="#2563EB", fg="white",
        activebackground="#1D4ED8",
        font=("Segoe UI", 12, "bold"),
        relief="flat", bd=0, padx=18, pady=8,
        cursor="hand2",
    ).pack(pady=(10, 0))

    root.wait_window(dialog)

    if not activated[0]:
        root.destroy()
        sys.exit(0)


def _on_close(dialog, activated, root):
    activated[0] = False
    dialog.destroy()


def _check_for_updates_gui(root) -> None:
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
        if messagebox.askyesno(
            APP_NAME + " – Update Available",
            f"New version {latest} available!\n\n{msg}\n\nOpen download page?",
            parent=root,
        ):
            webbrowser.open(dl)
    except Exception:
        pass


# ─────────────────────── Public entry-point ────────────────────────────────

def check_license() -> None:
    """
    Call once at the top of app.py BEFORE building the GUI.

    Linux:   first run → ResultAnalyzer --activate
             after that → validates silently

    Windows: first run → GUI activation dialog
             after that → validates silently
    """
    # Linux --activate flag
    if IS_LINUX and "--activate" in sys.argv:
        _linux_activate()
        return

    saved     = _load_license()
    saved_key = saved.get("key")

    # Linux flow — terminal only
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

    # Windows/Mac flow — GUI
    _run_gui_license()