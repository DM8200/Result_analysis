"""
keygen.py  –  Remote License Key Generator for College Result Analyzer
Run this on YOUR computer to create/list/revoke keys on your server.
No file copying needed — keys are saved directly on the server.

Install:  pip install requests tabulate
Usage:    python keygen.py
"""

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tabulate import tabulate

# ─────────────────── CONFIG — change these two lines ───────────────────────
SERVER_URL   = "https://license-server-p81y.onrender.com"    # ← your Render URL
ADMIN_TOKEN  = "Darshan949158"                               # ← your ADMIN_TOKEN
# ───────────────────────────────────────────────────────────────────────────

# ─────────────────── EMAIL CONFIG – configure for auto-sending keys ───────────
SMTP_SERVER  = "smtp.gmail.com"                              # ← Gmail SMTP server
SMTP_PORT    = 587                                           # ← Gmail port (TLS)
SENDER_EMAIL = "darshan.m@raoinformationtechnology.com"                        # ← Your email address
SENDER_PASS  = "quxoulqqpboeeafg"                           # ← Gmail app password (NOT regular password)
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


def send_email_key(recipient_email, customer_name, college_name, license_key, plan, expiry_text):
    """Send license key to customer via email"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Your College Result Analyzer License Key"
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        
        # Email body - HTML formatted
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h1 style="color: #1E3A5F; text-align: center;">License Key Generated</h1>
                    
                    <p style="color: #333; font-size: 16px;">Hello <strong>{customer_name}</strong>,</p>
                    
                    <p style="color: #555;">Your College Result Analyzer license key has been successfully generated. Use this key to activate the application on your institution's computers.</p>
                    
                    <div style="background-color: #1E3A5F; color: white; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
                        <p style="margin: 0; font-size: 12px; opacity: 0.8;">LICENSE KEY</p>
                        <p style="margin: 10px 0; font-size: 20px; font-weight: bold; font-family: 'Courier New', monospace; letter-spacing: 1px;">{license_key}</p>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr>
                            <td style="padding: 10px; background-color: #f9f9f9; font-weight: bold; color: #1E3A5F; border: 1px solid #ddd;">College Name</td>
                            <td style="padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd;">{college_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; background-color: #fff; font-weight: bold; color: #1E3A5F; border: 1px solid #ddd;">Plan</td>
                            <td style="padding: 10px; background-color: #fff; border: 1px solid #ddd;">{plan.capitalize()}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; background-color: #f9f9f9; font-weight: bold; color: #1E3A5F; border: 1px solid #ddd;">Expiry</td>
                            <td style="padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd;">{expiry_text}</td>
                        </tr>
                    </table>
                    
                    <div style="background-color: #E7F0F7; padding: 15px; border-left: 4px solid #1E3A5F; border-radius: 3px; margin: 20px 0;">
                        <p style="margin: 0; color: #1E3A5F; font-weight: bold;">📌 How to Use:</p>
                        <ol style="margin: 10px 0; padding-left: 20px; color: #555;">
                            <li>Install College Result Analyzer</li>
                            <li>Launch the application</li>
                            <li>Enter the license key above when prompted</li>
                            <li>Start analyzing results!</li>
                        </ol>
                    </div>
                    
                    <p style="color: #555; font-size: 14px; margin-top: 20px;">
                        If you have any questions or need support, please contact us.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        This is an automated message from College Result Analyzer License Manager<br>
                        Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
College Result Analyzer - License Key
=====================================

Hello {customer_name},

Your license key has been generated. Use this to activate the application:

LICENSE KEY: {license_key}

Details:
- College: {college_name}
- Plan: {plan}
- Expires: {expiry_text}

How to Use:
1. Install College Result Analyzer
2. Launch the application
3. Enter the license key when prompted
4. Start analyzing results!

If you have any questions, please contact support.

---
This is an automated message. Please do not reply.
        """
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.send_message(msg)
        server.quit()
        
        return True, "✅ Email sent successfully"
    except smtplib.SMTPAuthenticationError:
        return False, "❌ Email Error: Invalid credentials. Check SENDER_EMAIL and SENDER_PASS."
    except smtplib.SMTPException as e:
        return False, f"❌ Email Error: {str(e)}"
    except Exception as e:
        return False, f"❌ Email Error: {str(e)}"


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
    
    # Ask for email to send key
    send_email = input("  Send key via email? (yes/no, default: yes) : ").strip().lower()
    recipient_email = None
    if send_email != "no":
        recipient_email = input("  Enter recipient email address : ").strip()
        if not recipient_email or "@" not in recipient_email:
            print("  ⚠  Invalid email address.")
            recipient_email = None

    print("  Sending to server...")
    resp = _post("create_key", {
        "customer": customer,
        "college":  college,
        "plan":     plan,
        "days":     days,
    })

    if resp.get("status") == "ok":
        key = resp["key"]
        expiry_text = f'in {days} days' if days else 'Never (Lifetime)'
        
        print(f"""
  ✅  License key created on server!
  ┌─────────────────────────────────────────────┐
  │  Key      : {key:<33}│
  │  Customer : {customer:<33}│
  │  College  : {college:<33}│
  │  Plan     : {plan:<33}│
  │  Expires  : {expiry_text:<33}│
  └─────────────────────────────────────────────┘
  📧 Key details: {key}
""")
        
        # Send email if requested
        if recipient_email:
            print("  📨 Sending email...")
            success, msg = send_email_key(recipient_email, customer, college, key, plan, expiry_text)
            print(f"  {msg}")
            if success:
                print(f"  ✅ Key sent to: {recipient_email}")
        else:
            print("  ℹ  Email not sent. Share this key with customer:")
            print(f"     {key}")
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

    headers = ["KEY", "CUSTOMER", "COLLEGE", "PLAN", "EXPIRES", "ACTIVE", "REVOKED"]
    rows = [
        [
            lic['key'],
            lic['customer'],
            lic.get('college', ''),
            lic['plan'],
            lic['expires_at'],
            str(lic['activated']),
            str(lic['revoked'])
        ]
        for lic in licenses
    ]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
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


def send_existing_key():
    print("\n── Send Existing Key via Email ──")
    
    # Fetch all keys
    resp = _post("list_keys", {})
    if resp.get("status") != "ok":
        print(f"  ❌ Error: {resp.get('message')}")
        return

    licenses = resp.get("licenses", [])
    if not licenses:
        print("  (no licenses available)")
        return

    # Display available keys
    print("\n  Available Keys:")
    headers = ["#", "KEY", "CUSTOMER", "COLLEGE", "PLAN", "EXPIRES"]
    rows = []
    for idx, lic in enumerate(licenses, 1):
        rows.append([
            idx,
            lic['key'],
            lic['customer'],
            lic.get('college', ''),
            lic['plan'],
            lic['expires_at']
        ])
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    
    # Select a key
    try:
        choice = input("\n  Select key number (or 0 to cancel) : ").strip()
        if choice == "0":
            print("  Cancelled.")
            return
        
        key_idx = int(choice) - 1
        if key_idx < 0 or key_idx >= len(licenses):
            print("  ⚠  Invalid selection.")
            return
        
        selected_lic = licenses[key_idx]
        key = selected_lic['key']
        customer = selected_lic['customer']
        college = selected_lic.get('college', '')
        plan = selected_lic['plan']
        expires = selected_lic['expires_at']
        
    except (ValueError, IndexError):
        print("  ⚠  Invalid input.")
        return
    
    # Get recipient email
    recipient_email = input("  Enter recipient email address : ").strip()
    if not recipient_email or "@" not in recipient_email:
        print("  ⚠  Invalid email address.")
        return
    
    # Send email
    print("  📨 Sending email...")
    success, msg = send_email_key(recipient_email, customer, college, key, plan, expires)
    print(f"  {msg}")
    if success:
        print(f"  ✅ Key sent to: {recipient_email}")


def transfer_key():
    print("\n── Transfer License Key to New System ──")
    
    # Fetch all keys
    resp = _post("list_keys", {})
    if resp.get("status") != "ok":
        print(f"  ❌ Error: {resp.get('message')}")
        return

    licenses = resp.get("licenses", [])
    if not licenses:
        print("  (no licenses available)")
        return

    # Display available keys
    print("\n  Available Keys:")
    headers = ["#", "KEY", "CUSTOMER", "COLLEGE", "PLAN", "EXPIRES", "ACTIVE"]
    rows = []
    for idx, lic in enumerate(licenses, 1):
        rows.append([
            idx,
            lic['key'],
            lic['customer'],
            lic.get('college', ''),
            lic['plan'],
            lic['expires_at'],
            str(lic['activated'])
        ])
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    
    # Select a key
    try:
        choice = input("\n  Select key number to transfer (or 0 to cancel) : ").strip()
        if choice == "0":
            print("  Cancelled.")
            return
        
        key_idx = int(choice) - 1
        if key_idx < 0 or key_idx >= len(licenses):
            print("  ⚠  Invalid selection.")
            return
        
        selected_lic = licenses[key_idx]
        key = selected_lic['key']
        customer = selected_lic['customer']
        college = selected_lic.get('college', '')
        
    except (ValueError, IndexError):
        print("  ⚠  Invalid input.")
        return
    
    # Confirm transfer
    print(f"\n  🔄 Transferring key: {key}")
    print(f"  👤 Customer: {customer}")
    print(f"  🏫 College: {college}")
    
    confirm = input("\n  This will allow the key to be used on a new system. Continue? (yes/no) : ").strip().lower()
    if confirm != "yes":
        print("  Cancelled.")
        return
    
    # Send transfer request to server
    print("  📡 Sending transfer request to server...")
    resp = _post("transfer_key", {"key": key})
    
    if resp.get("status") == "ok":
        print(f"  ✅ Key {key} has been transferred successfully!")
        print("  ℹ  The customer can now activate this key on their new system.")
        
        # Ask if they want to send email notification
        send_email = input("  📧 Send transfer notification email to customer? (yes/no) : ").strip().lower()
        if send_email == "yes":
            recipient_email = input("  Enter customer email address : ").strip()
            if recipient_email and "@" in recipient_email:
                print("  📨 Sending transfer notification...")
                # Create transfer notification email
                try:
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = "License Key Transfer Approved - College Result Analyzer"
                    msg['From'] = SENDER_EMAIL
                    msg['To'] = recipient_email
                    
                    html_body = f"""
                    <html>
                        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                <h1 style="color: #1E3A5F; text-align: center;">License Transfer Approved</h1>
                                
                                <p style="color: #333; font-size: 16px;">Hello <strong>{customer}</strong>,</p>
                                
                                <p style="color: #555;">Your license key transfer request has been approved. You can now use your license on a new system.</p>
                                
                                <div style="background-color: #1E3A5F; color: white; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
                                    <p style="margin: 0; font-size: 12px; opacity: 0.8;">LICENSE KEY</p>
                                    <p style="margin: 10px 0; font-size: 20px; font-weight: bold; font-family: 'Courier New', monospace; letter-spacing: 1px;">{key}</p>
                                </div>
                                
                                <div style="background-color: #E7F0F7; padding: 15px; border-left: 4px solid #1E3A5F; border-radius: 3px; margin: 20px 0;">
                                    <p style="margin: 0; color: #1E3A5F; font-weight: bold;">📋 Next Steps:</p>
                                    <ol style="margin: 10px 0; padding-left: 20px; color: #555;">
                                        <li>Uninstall the application from your old system</li>
                                        <li>Install College Result Analyzer on your new system</li>
                                        <li>Enter the license key above when prompted</li>
                                        <li>Start analyzing results!</li>
                                    </ol>
                                </div>
                                
                                <p style="color: #555; font-size: 14px; margin-top: 20px;">
                                    If you encounter any issues, please contact support.
                                </p>
                                
                                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                                
                                <p style="color: #999; font-size: 12px; text-align: center;">
                                    This is an automated message from College Result Analyzer License Manager<br>
                                    Please do not reply to this email.
                                </p>
                            </div>
                        </body>
                    </html>
                    """
                    
                    text_body = f"""
College Result Analyzer - License Transfer Approved
==================================================

Hello {customer},

Your license key transfer request has been approved. You can now use your license on a new system.

LICENSE KEY: {key}

Next Steps:
1. Uninstall the application from your old system
2. Install College Result Analyzer on your new system
3. Enter the license key when prompted
4. Start analyzing results!

If you have any issues, please contact support.

---
This is an automated message. Please do not reply.
                    """
                    
                    msg.attach(MIMEText(text_body, 'plain'))
                    msg.attach(MIMEText(html_body, 'html'))
                    
                    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                    server.starttls()
                    server.login(SENDER_EMAIL, SENDER_PASS)
                    server.send_message(msg)
                    server.quit()
                    
                    print("  ✅ Transfer notification sent successfully!")
                except Exception as e:
                    print(f"  ❌ Email Error: {str(e)}")
            else:
                print("  ⚠  Invalid email address.")
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
  3. Send existing key via email
  4. Transfer key to new system
  5. Revoke a license key
  6. Exit""")
        choice = input("\n  Choose: ").strip()

        if choice == "1":
            create_key()
        elif choice == "2":
            list_keys()
        elif choice == "3":
            send_existing_key()
        elif choice == "4":
            transfer_key()
        elif choice == "5":
            revoke_key()
        elif choice == "6":
            break
        else:
            print("  Invalid choice.")
