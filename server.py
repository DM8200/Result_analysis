"""
server.py  –  License Server for College Result Analyzer
Deploy this on Render.com / Railway.app (free hosting with HTTPS).

Install:  pip install flask gunicorn
Run:      python server.py

Environment variable (set on your hosting):
    ADMIN_TOKEN=your_secret_password_here
"""

from flask import Flask, request, jsonify
import json, os, datetime, random, string

app = Flask(__name__)
LICENSES_FILE = "licenses.json"

# ─────────────────────── VERSION CONFIG ────────────────────────────────────
# ⬇ Change this EVERY time you release a new version
LATEST_VERSION  = "1.0.0"
DOWNLOAD_URL    = "https://drive.google.com/your-file-link-here"  # ← your Google Drive link
UPDATE_MESSAGE  = "A new version of College Result Analyzer is available!\nPlease download and replace your EXE file."
# ───────────────────────────────────────────────────────────────────────────


# ─────────────────────── Helpers ───────────────────────────────────────────

def _load():
    if not os.path.exists(LICENSES_FILE):
        return {}
    with open(LICENSES_FILE) as f:
        return json.load(f)

def _save(data):
    with open(LICENSES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def _expired(lic):
    if not lic.get("expires_at"):
        return False
    return datetime.datetime.utcnow() > datetime.datetime.fromisoformat(lic["expires_at"])

def _check_admin(d):
    return d.get("admin_token") == os.environ.get("ADMIN_TOKEN", "changeme")

def _gen_key():
    chars = string.ascii_uppercase + string.digits
    return "-".join("".join(random.choices(chars, k=5)) for _ in range(4))


# ─────────────────────── Root (Health Check) ───────────────────────────────

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "License Server is running ✅"})

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"})


# ─────────────────────── Version Check ─────────────────────────────────────

@app.route("/version", methods=["GET"])
def version():
    """Called by app on every launch to check for updates."""
    return jsonify({
        "latest":   LATEST_VERSION,
        "download": DOWNLOAD_URL,
        "message":  UPDATE_MESSAGE,
    })


# ─────────────────────── Admin: Create Key ─────────────────────────────────

@app.route("/create_key", methods=["POST"])
def create_key():
    d = request.json or {}
    if not _check_admin(d):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    customer = str(d.get("customer", "")).strip()
    college  = str(d.get("college",  "")).strip()
    plan     = str(d.get("plan", "standard")).strip()
    days     = d.get("days")

    if not customer:
        return jsonify({"status": "error", "message": "Customer name is required"}), 400
    if not college:
        return jsonify({"status": "error", "message": "College name is required"}), 400

    licenses = _load()

    for _ in range(20):
        key = _gen_key()
        if key not in licenses:
            break
    else:
        return jsonify({"status": "error", "message": "Could not generate unique key"}), 500

    expires_at = None
    if days:
        try:
            expires_at = (datetime.datetime.utcnow() + datetime.timedelta(days=int(days))).isoformat()
        except Exception:
            pass

    licenses[key] = {
        "customer":     customer,
        "college":      college,
        "plan":         plan,
        "created_at":   datetime.datetime.utcnow().isoformat(),
        "expires_at":   expires_at,
        "machine_id":   None,
        "activated_at": None,
        "revoked":      False,
    }
    _save(licenses)

    return jsonify({
        "status":     "ok",
        "key":        key,
        "customer":   customer,
        "college":    college,
        "plan":       plan,
        "expires_at": expires_at,
    })


# ─────────────────────── Admin: List Keys ──────────────────────────────────

@app.route("/list_keys", methods=["POST"])
def list_keys():
    d = request.json or {}
    if not _check_admin(d):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    licenses = _load()
    result = []
    for key, lic in licenses.items():
        result.append({
            "key":        key,
            "customer":   lic.get("customer", ""),
            "college":    lic.get("college",  ""),
            "plan":       lic.get("plan", ""),
            "expires_at": lic.get("expires_at") or "Lifetime",
            "activated":  "Yes" if lic.get("activated_at") else "No",
            "revoked":    "Yes" if lic.get("revoked") else "No",
        })
    return jsonify({"status": "ok", "licenses": result})


# ─────────────────────── Admin: Revoke Key ─────────────────────────────────

@app.route("/revoke", methods=["POST"])
def revoke():
    d = request.json or {}
    if not _check_admin(d):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    key = d.get("key", "").strip().upper()
    licenses = _load()
    if key not in licenses:
        return jsonify({"status": "error", "message": "Key not found"}), 404
    licenses[key]["revoked"] = True
    _save(licenses)
    return jsonify({"status": "ok", "message": f"{key} revoked"})


# ─────────────────────── Customer: Activate ────────────────────────────────

@app.route("/activate", methods=["POST"])
def activate():
    d = request.json or {}
    key, mid = d.get("key", "").strip().upper(), d.get("machine_id", "").strip()
    if not key or not mid:
        return jsonify({"status": "error", "message": "Missing key or machine_id"}), 400

    licenses = _load()
    if key not in licenses:
        return jsonify({"status": "error", "message": "Invalid license key"}), 403

    lic = licenses[key]
    if lic.get("revoked"):
        return jsonify({"status": "error", "message": "This license has been revoked. Contact support."}), 403
    if _expired(lic):
        return jsonify({"status": "error", "message": "License has expired. Please renew."}), 403
    if lic["machine_id"] and lic["machine_id"] != mid:
        return jsonify({"status": "error", "message": "License already activated on another machine. Contact support."}), 403

    lic["machine_id"]   = mid
    lic["activated_at"] = datetime.datetime.utcnow().isoformat()
    _save(licenses)

    return jsonify({
        "status":     "ok",
        "message":    "Activated successfully",
        "customer":   lic["customer"],
        "college":    lic.get("college", ""),
        "plan":       lic["plan"],
        "expires_at": lic.get("expires_at"),
    })


# ─────────────────────── Customer: Validate ────────────────────────────────

@app.route("/validate", methods=["POST"])
def validate():
    d = request.json or {}
    key, mid = d.get("key", "").strip().upper(), d.get("machine_id", "").strip()
    if not key or not mid:
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    licenses = _load()
    if key not in licenses:
        return jsonify({"status": "error", "message": "Invalid license key"}), 403

    lic = licenses[key]
    if lic.get("revoked"):
        return jsonify({"status": "error", "message": "License revoked"}), 403
    if lic.get("machine_id") != mid:
        return jsonify({"status": "error", "message": "Machine ID mismatch"}), 403
    if _expired(lic):
        return jsonify({"status": "error", "message": "License expired"}), 403

    return jsonify({
        "status":     "ok",
        "customer":   lic["customer"],
        "college":    lic.get("college", ""),
        "plan":       lic["plan"],
        "expires_at": lic.get("expires_at"),
    })


# ───────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.path.exists(LICENSES_FILE):
        _save({})
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
