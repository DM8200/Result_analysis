"""
keygen.py  –  Remote License Key Generator for College Result Analyzer
Run this on YOUR computer to create/list/revoke keys on your server.
No file copying needed — keys are saved directly on the server.

Install:  pip install requests
Usage:    python keygen.py
"""

import requests

# ─────────────────── CONFIG — change these two lines ───────────────────────
SERVER_URL   = "https://license-server-p81y.onrender.com"    # ← your Render URL
ADMIN_TOKEN  = "Darshan949158"                               # ← your ADMIN_TOKEN
# ───────────────────────────────────────────────────────────────────────────

TIMEOUT = 10


def _post(endpoint, payload):
    try:
        r = requests.post(
            f"{SERVER_URL.rstrip('/')}/{endpoint}",
            json={**payload, "admin_token": ADMIN_TOKEN},
            timeout=TIMEOUT,
        )
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "❌ Cannot connect to server. Check SERVER_URL and internet."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_key():
    print("\n── Generate New License Key ──")

    customer = input("  Customer name or email : ").strip()
    if not customer:
        print("  ⚠  Customer name is required.")
        return

    college = input("  College name (shown in Excel header) : ").strip()
    if not college:
        print("  ⚠  College name is required.")
        return

    plan = input("  Plan [standard/pro/lifetime] (default: standard) : ").strip() or "standard"
    days_in = input("  Expiry in days? (leave blank = lifetime) : ").strip()
    days = int(days_in) if days_in.isdigit() else None

    print("  Sending to server...")
    resp = _post("create_key", {
        "customer": customer,
        "college":  college,
        "plan":     plan,
        "days":     days,
    })

    if resp.get("status") == "ok":
        key = resp["key"]
        print(f"""
  ✅  License key created on server!
  ┌─────────────────────────────────────────────┐
  │  Key      : {key:<33}│
  │  Customer : {customer:<33}│
  │  College  : {college:<33}│
  │  Plan     : {plan:<33}│
  │  Expires  : {(f'in {days} days' if days else 'Never (Lifetime)'):<33}│
  └─────────────────────────────────────────────┘
  📧 Send this key to your customer:
     {key}
""")
    else:
        print(f"  ❌ Error: {resp.get('message')}")


def list_keys():
    print("\n── All License Keys ──")
    resp = _post("list_keys", {})
    if resp.get("status") != "ok":
        print(f"  ❌ Error: {resp.get('message')}")
        return

    licenses = resp.get("licenses", [])
    if not licenses:
        print("  (no licenses yet)")
        return

    print(f"\n  {'KEY':<25} {'CUSTOMER':<20} {'COLLEGE':<25} {'PLAN':<12} {'EXPIRES':<22} {'ACTIVE':<8} {'REVOKED'}")
    print("  " + "─" * 120)
    for lic in licenses:
        print(
            f"  {lic['key']:<25} {lic['customer']:<20} {lic.get('college',''):<25} {lic['plan']:<12} "
            f"{lic['expires_at']:<22} {lic['activated']:<8} {lic['revoked']}"
        )
    print()


def revoke_key():
    print("\n── Revoke a License Key ──")
    key = input("  Enter key to revoke : ").strip().upper()
    if not key:
        print("  ⚠  No key entered.")
        return

    confirm = input(f"  Revoke {key}? This cannot be undone. (yes/no) : ").strip().lower()
    if confirm != "yes":
        print("  Cancelled.")
        return

    resp = _post("revoke", {"key": key})
    if resp.get("status") == "ok":
        print(f"  ✅ Key {key} has been revoked.")
    else:
        print(f"  ❌ Error: {resp.get('message')}")


# ─────────────────────── Main Menu ─────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n  Server : {SERVER_URL}")

    while True:
        print("""
══════════════════════════════════════
  College Result Analyzer – Key Manager
══════════════════════════════════════
  1. Generate new license key
  2. List all license keys
  3. Revoke a license key
  4. Exit""")
        choice = input("\n  Choose: ").strip()

        if choice == "1":
            create_key()
        elif choice == "2":
            list_keys()
        elif choice == "3":
            revoke_key()
        elif choice == "4":
            break
        else:
            print("  Invalid choice.")
