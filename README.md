# OpenWrt Captive Portal with Email OTP Authentication

A complete captive portal system for OpenWrt routers featuring email-based One-Time Password (OTP) authentication.

## Features

- Email-based OTP authentication
- Modern, responsive web interface
- Flask-based authentication server
- Secure session management
- Real-time admin dashboard
- Support for multiple concurrent users
- Automatic session expiration
- Email notifications with HTML templates

## Components

### 1. OTP Authentication Server (`otp_auth_server.py`)
Flask-based server that handles:
- OTP generation and verification
- Email sending via SMTP
- Client authentication
- Session management
- Admin dashboard

### 2. Splash Page (`splash_otp.html`)
User-facing captive portal interface featuring:
- Email input form
- 6-digit OTP entry interface
- Step-by-step authentication flow
- Mobile-responsive design

### 3. OpenWrt Router Configuration (`router/`)
Complete router-side configuration:
- **Firewall Rules** (`router/etc/firewall.captive`) - iptables configuration for captive portal
- **Startup Script** (`router/etc/rc.local`) - Auto-start firewall on boot
- **Authentication Binary** (`router/usr/bin/captive-auth`) - Client authentication management
- **CGI Scripts** (`router/www/cgi-bin/`) - Web endpoints for authentication and MAC detection
- **Splash Page** (`router/www/simple-otp.html`) - Portal landing page

### 4. Email Testing Utility (`test_email.py`)
Test SMTP email configuration before deployment

## Installation

### Requirements

- Python 3.x
- Flask
- flask-cors
- OpenWrt router with openNDS or nodogsplash

### Setup

1. Install Python dependencies:
```bash
pip install flask flask-cors requests
```

2. Configure email settings in `otp_auth_server.py`:
```python
EMAIL_ENABLED = True
SMTP_SERVER = "your-smtp-server.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@example.com"
SMTP_PASSWORD = "your-password"
FROM_EMAIL = "your-email@example.com"
```

3. Configure router URL:
```python
ROUTER_AUTH_URL = "http://192.168.1.1/cgi-bin/auth"
```

4. Run the authentication server:
```bash
python3 otp_auth_server.py
```

5. Deploy router files to OpenWrt:
```bash
scp -r router/etc/* root@your-router-ip:/etc/
scp router/usr/bin/captive-auth root@your-router-ip:/usr/bin/
chmod +x /usr/bin/captive-auth
scp -r router/www/* root@your-router-ip:/www/
chmod +x /www/cgi-bin/*
```

6. Restart router or run `/etc/firewall.captive` manually

## Configuration

### Server Configuration

- `OTP_LENGTH`: Number of digits in OTP (default: 6)
- `OTP_VALIDITY`: OTP expiration time in seconds (default: 300)
- `SESSION_DURATION`: Authenticated session duration (default: 3600)

### Router Configuration

Configure openNDS or nodogsplash to point to the splash page and authentication server.

## Usage

1. Start the authentication server on your host machine
2. Configure OpenWrt router to use the splash page
3. When users connect to WiFi, they are redirected to the captive portal
4. Users enter their email address
5. System sends OTP code via email
6. Users enter the OTP to gain internet access

## Admin Dashboard

Access the admin dashboard at `http://your-server-ip:5000` to view:
- Active OTPs
- Authenticated clients
- Session information
- Real-time statistics

## Security Features

- OTPs expire after 5 minutes
- Single-use OTP codes
- Session token-based authentication
- MAC address verification
- HTTPS-ready (configure reverse proxy)

## Testing

Test email configuration:
```bash
python3 test_email.py
```

## License

This project is provided as-is for educational and personal use.

## Support

For issues and questions, please open an issue on GitHub.
