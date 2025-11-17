#!/usr/bin/env python3

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import secrets
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import re
import requests
import urllib.parse

app = Flask(__name__)
CORS(app)

active_otps = {}
authenticated_clients = {}
pending_registrations = {}

OTP_LENGTH = 6
OTP_VALIDITY = 300
SESSION_DURATION = 3600

EMAIL_ENABLED = False
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@example.com"
SMTP_PASSWORD = "your-password-here"
FROM_EMAIL = "your-email@example.com"

ROUTER_AUTH_URL = "http://192.168.1.1/cgi-bin/auth"

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_otp():
    return ''.join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])

def send_email_otp(email, otp):
    if not EMAIL_ENABLED:
        print(f"[EMAIL SIMULATION] Would send OTP {otp} to {email}")
        print(f"[EMAIL SIMULATION] Subject: Your WiFi Access Code")
        print(f"[EMAIL SIMULATION] Body: Your OTP is: {otp} (valid for 5 minutes)")
        return True

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Your WiFi Access Code'
        msg['From'] = FROM_EMAIL
        msg['To'] = email

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.2);">
                <h2 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 28px; margin-bottom: 20px;">🔐 WiFi Access Code</h2>
                <p style="font-size: 16px; color: #333;">Hello,</p>
                <p style="font-size: 16px; color: #333;">Your One-Time Password (OTP) for WiFi access is:</p>
                <div style="background: linear-gradient(135deg, #f0f4ff 0%, #e8f5e9 100%); padding: 30px; border-radius: 15px; text-align: center; margin: 25px 0; border: 3px solid #38ef7d;">
                    <h1 style="color: #38ef7d; font-size: 48px; letter-spacing: 15px; margin: 0; text-shadow: 0 0 10px rgba(56, 239, 125, 0.3);">{otp}</h1>
                </div>
                <p style="font-size: 14px; color: #666;">This code is valid for <strong>5 minutes</strong>.</p>
                <p style="font-size: 14px; color: #666;">Enter this code on the WiFi login page to connect to the internet.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="font-size: 12px; color: #999; text-align: center;">
                    If you didn't request this code, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

        text = f"""
        WiFi Access Code

        Your One-Time Password (OTP) is: {otp}

        This code is valid for 5 minutes.
        Enter this code on the WiFi login page to connect to the internet.

        If you didn't request this code, please ignore this email.
        """

        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Email sent to {email}")
        return True

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Email send failed: {str(e)}")
        return False

def authenticate_on_router(mac_address, ip_address=None):
    try:
        mac_encoded = urllib.parse.quote(mac_address)
        ip_param = f"&ip={urllib.parse.quote(ip_address)}" if ip_address else ""

        url = f"{ROUTER_AUTH_URL}?action=auth&mac={mac_encoded}{ip_param}"

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔓 Authenticating {mac_address} on router...")

        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Router auth successful: {mac_address}")
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Router auth failed: {result.get('message')}")
                return False
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Router auth HTTP error: {response.status_code}")
            return False

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Router auth exception: {str(e)}")
        return False

def cleanup_expired():
    current_time = time.time()

    expired_otps = [otp for otp, data in active_otps.items()
                    if current_time - data['created'] > OTP_VALIDITY]
    for otp in expired_otps:
        del active_otps[otp]

    expired_clients = [mac for mac, data in authenticated_clients.items()
                      if current_time > data['expires']]
    for mac in expired_clients:
        del authenticated_clients[mac]

    expired_pending = [email for email, data in pending_registrations.items()
                      if current_time - data['created'] > OTP_VALIDITY]
    for email in expired_pending:
        del pending_registrations[email]

@app.route('/')
def index():
    cleanup_expired()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OTP Auth Server - Admin Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 {
                color: white;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .stat-card h3 {
                color: #666;
                font-size: 14px;
                margin-bottom: 10px;
            }
            .stat-card .value {
                color: #764ba2;
                font-size: 32px;
                font-weight: bold;
            }
            .section {
                background: white;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .section h2 {
                color: #333;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #764ba2;
            }
            .refresh-btn {
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 15px;
                box-shadow: 0 4px 15px rgba(56, 239, 125, 0.3);
                transition: all 0.3s ease;
            }
            .refresh-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(56, 239, 125, 0.5);
            }
            table {
                width: 100%;
                border-collapse: collapse;
                overflow-x: auto;
                display: block;
            }
            thead, tbody { display: table; width: 100%; table-layout: fixed; }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
                word-wrap: break-word;
            }
            th {
                background: #f8f9fa;
                color: #333;
                font-weight: 600;
            }
            tr:hover {
                background: #f8f9fa;
            }
            .otp-code {
                font-family: 'Courier New', monospace;
                font-size: 20px;
                font-weight: bold;
                color: #38ef7d;
                letter-spacing: 3px;
            }
            .status {
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
            }
            .status-active {
                background: #d4edda;
                color: #155724;
            }
            .status-used {
                background: #f8d7da;
                color: #721c24;
            }
            .status-expired {
                background: #fff3cd;
                color: #856404;
            }
            .time {
                color: #666;
                font-size: 14px;
            }
            .email {
                color: #764ba2;
                font-size: 14px;
                font-weight: 500;
            }
            .alert {
                background: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .alert-warning {
                background: #fff3cd;
                border: 1px solid #ffc107;
                color: #856404;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 OTP Authentication Server - Admin Dashboard</h1>

            {% if not email_enabled %}
            <div class="alert alert-warning">
                <strong>⚠️ Email Simulation Mode</strong><br>
                Emails are not actually being sent. OTPs are displayed in the console/logs.<br>
                To enable real email sending, configure SMTP settings in otp_auth_server.py
            </div>
            {% endif %}

            <div class="stats">
                <div class="stat-card">
                    <h3>Active OTPs</h3>
                    <div class="value">{{ active_count }}</div>
                </div>
                <div class="stat-card">
                    <h3>Authenticated Clients</h3>
                    <div class="value">{{ client_count }}</div>
                </div>
                <div class="stat-card">
                    <h3>Pending Registrations</h3>
                    <div class="value">{{ pending_count }}</div>
                </div>
                <div class="stat-card">
                    <h3>Total Generated</h3>
                    <div class="value">{{ total_count }}</div>
                </div>
            </div>

            <div class="section">
                <h2>📧 Recent OTP Requests</h2>
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
                <table>
                    <thead>
                        <tr>
                            <th>OTP Code</th>
                            <th>Email</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Expires In</th>
                            <th>Used By MAC</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for otp, data in otps.items() %}
                        <tr>
                            <td class="otp-code">{{ otp }}</td>
                            <td class="email">{{ data.email }}</td>
                            <td>
                                {% if data.used %}
                                    <span class="status status-used">USED</span>
                                {% elif data.expired %}
                                    <span class="status status-expired">EXPIRED</span>
                                {% else %}
                                    <span class="status status-active">ACTIVE</span>
                                {% endif %}
                            </td>
                            <td class="time">{{ data.created_str }}</td>
                            <td class="time">{{ data.expires_in }}</td>
                            <td>{{ data.mac or '-' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% if not otps %}
                <p style="text-align: center; color: #666; padding: 20px;">No OTP requests yet</p>
                {% endif %}
            </div>

            <div class="section">
                <h2>👥 Authenticated Clients</h2>
                <table>
                    <thead>
                        <tr>
                            <th>MAC Address</th>
                            <th>Email</th>
                            <th>Session Token</th>
                            <th>Expires At</th>
                            <th>Time Remaining</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for mac, data in clients.items() %}
                        <tr>
                            <td><code>{{ mac }}</code></td>
                            <td class="email">{{ data.email }}</td>
                            <td><code style="font-size: 11px;">{{ data.token[:16] }}...</code></td>
                            <td class="time">{{ data.expires_str }}</td>
                            <td class="time">{{ data.time_remaining }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% if not clients %}
                <p style="text-align: center; color: #666; padding: 20px;">No authenticated clients</p>
                {% endif %}
            </div>
        </div>

        <script>
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    """

    current_time = time.time()
    otps_data = {}

    for otp, data in active_otps.items():
        age = current_time - data['created']
        expires_in = OTP_VALIDITY - age

        otps_data[otp] = {
            'email': data['email'],
            'used': data['used'],
            'expired': expires_in <= 0,
            'created_str': datetime.fromtimestamp(data['created']).strftime('%H:%M:%S'),
            'expires_in': f"{int(expires_in)}s" if expires_in > 0 else "Expired",
            'mac': data.get('mac', None)
        }

    clients_data = {}
    for mac, data in authenticated_clients.items():
        time_remaining = data['expires'] - current_time
        clients_data[mac] = {
            'email': data.get('email', 'N/A'),
            'token': data['token'],
            'expires_str': datetime.fromtimestamp(data['expires']).strftime('%H:%M:%S'),
            'time_remaining': f"{int(time_remaining / 60)}m {int(time_remaining % 60)}s"
        }

    return render_template_string(
        html,
        email_enabled=EMAIL_ENABLED,
        active_count=len([d for d in active_otps.values() if not d['used']]),
        client_count=len(authenticated_clients),
        pending_count=len(pending_registrations),
        total_count=len(active_otps),
        otps=otps_data,
        clients=clients_data
    )

@app.route('/api/request_otp', methods=['POST'])
def api_request_otp():
    cleanup_expired()

    data = request.get_json() or {}
    email = data.get('email', request.form.get('email', '')).strip().lower()

    if not email:
        return jsonify({
            'success': False,
            'error': 'Email address is required'
        }), 400

    if not validate_email(email):
        return jsonify({
            'success': False,
            'error': 'Invalid email format'
        }), 400

    otp = generate_otp()
    while otp in active_otps:
        otp = generate_otp()

    active_otps[otp] = {
        'email': email,
        'created': time.time(),
        'used': False,
        'mac': None
    }

    email_sent = send_email_otp(email, otp)

    if not email_sent and EMAIL_ENABLED:
        return jsonify({
            'success': False,
            'error': 'Failed to send email. Please try again.'
        }), 500

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📧 OTP {otp} requested for {email}")

    return jsonify({
        'success': True,
        'message': 'OTP sent to your email',
        'validity': OTP_VALIDITY
    })

@app.route('/api/verify_otp', methods=['POST', 'GET'])
def api_verify_otp():
    cleanup_expired()

    if request.method == 'POST':
        data = request.get_json() or {}
        otp = data.get('otp', request.form.get('otp'))
        mac = data.get('mac', request.form.get('mac'))
    else:
        otp = request.args.get('otp')
        mac = request.args.get('mac')

    if not otp or not mac:
        return jsonify({
            'success': False,
            'error': 'Missing OTP or MAC address'
        }), 400

    if otp not in active_otps:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Invalid OTP attempt: {otp} from {mac}")
        return jsonify({
            'success': False,
            'error': 'Invalid OTP code'
        }), 401

    otp_data = active_otps[otp]

    if otp_data['used']:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ OTP already used: {otp}")
        return jsonify({
            'success': False,
            'error': 'This OTP has already been used'
        }), 401

    age = time.time() - otp_data['created']
    if age > OTP_VALIDITY:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Expired OTP: {otp}")
        return jsonify({
            'success': False,
            'error': 'OTP has expired. Please request a new one.'
        }), 401

    otp_data['used'] = True
    otp_data['mac'] = mac

    token = secrets.token_urlsafe(32)
    authenticated_clients[mac] = {
        'token': token,
        'email': otp_data['email'],
        'expires': time.time() + SESSION_DURATION,
        'otp_used': otp
    }

    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Authenticated: {mac} ({otp_data['email']}) with OTP {otp}")

    client_ip = request.remote_addr
    router_auth_success = authenticate_on_router(mac, client_ip)

    if not router_auth_success:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Warning: Router authentication failed for {mac}, but client is authenticated in OTP server")

    return jsonify({
        'success': True,
        'token': token,
        'expires_in': SESSION_DURATION,
        'message': 'Authentication successful',
        'router_auth': router_auth_success
    })

@app.route('/api/check_auth', methods=['GET', 'POST'])
def api_check_auth():
    cleanup_expired()

    mac = request.args.get('mac') or (request.get_json() or {}).get('mac')

    if not mac:
        return jsonify({'authenticated': False}), 400

    if mac in authenticated_clients:
        data = authenticated_clients[mac]
        if time.time() < data['expires']:
            return jsonify({
                'authenticated': True,
                'email': data.get('email'),
                'expires_in': int(data['expires'] - time.time())
            })

    return jsonify({'authenticated': False})

@app.route('/api/stats', methods=['GET'])
def api_stats():
    cleanup_expired()

    return jsonify({
        'active_otps': len([d for d in active_otps.values() if not d['used']]),
        'used_otps': len([d for d in active_otps.values() if d['used']]),
        'authenticated_clients': len(authenticated_clients),
        'total_otps': len(active_otps),
        'email_enabled': EMAIL_ENABLED
    })

if __name__ == '__main__':
    print("=" * 70)
    print("🔐 OTP Authentication Server with Email Registration")
    print("=" * 70)
    print(f"Server starting on http://0.0.0.0:5000")
    print(f"Admin Dashboard: http://192.168.1.246:5000")
    print(f"")
    print(f"Configuration:")
    print(f"  - OTP Length: {OTP_LENGTH} digits")
    print(f"  - OTP Validity: {OTP_VALIDITY} seconds ({OTP_VALIDITY//60} minutes)")
    print(f"  - Session Duration: {SESSION_DURATION} seconds ({SESSION_DURATION//60} minutes)")
    print(f"  - Email Sending: {'ENABLED (Real emails)' if EMAIL_ENABLED else 'SIMULATION MODE (Console only)'}")
    print(f"")
    if not EMAIL_ENABLED:
        print("⚠️  EMAIL SIMULATION MODE")
        print("  OTPs will be shown in console/logs instead of being emailed")
        print("  To enable real emails, configure SMTP settings in the script")
    print("=" * 70)

    app.run(host='0.0.0.0', port=5000, debug=True)
