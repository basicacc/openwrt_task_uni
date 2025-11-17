#!/usr/bin/env python3

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@example.com"
SMTP_PASSWORD = "your-password-here"
FROM_EMAIL = "your-email@example.com"
TEST_EMAIL = "your-email@example.com"

def test_smtp_connection():
    print("=" * 70)
    print("Testing Disroot SMTP Configuration")
    print("=" * 70)
    print(f"SMTP Server: {SMTP_SERVER}")
    print(f"SMTP Port: {SMTP_PORT}")
    print(f"Username: {SMTP_USERNAME}")
    print(f"From Email: {FROM_EMAIL}")
    print("-" * 70)

    try:
        print("\n[1/3] Connecting to SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        print("✅ Connected successfully")

        print("\n[2/3] Starting TLS encryption...")
        server.starttls()
        print("✅ TLS enabled successfully")

        print("\n[3/3] Authenticating...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("✅ Authentication successful")

        server.quit()
        print("\n" + "=" * 70)
        print("✅ SMTP Connection Test: PASSED")
        print("=" * 70)
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication failed: {str(e)}")
        print("Please check your username and password")
        return False
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        return False

def send_test_email():
    print("\n" + "=" * 70)
    print("Sending Test Email")
    print("=" * 70)

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'OTP Server Email Test - Disroot Configuration'
        msg['From'] = FROM_EMAIL
        msg['To'] = TEST_EMAIL

        test_otp = "123456"

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.2);">
                <h2 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 28px; margin-bottom: 20px;">🔐 Email Configuration Test</h2>
                <p style="font-size: 16px; color: #333;">Hello,</p>
                <p style="font-size: 16px; color: #333;">This is a test email from your OTP authentication server.</p>
                <p style="font-size: 16px; color: #333;">Your test OTP code is:</p>
                <div style="background: linear-gradient(135deg, #f0f4ff 0%, #e8f5e9 100%); padding: 30px; border-radius: 15px; text-align: center; margin: 25px 0; border: 3px solid #38ef7d;">
                    <h1 style="color: #38ef7d; font-size: 48px; letter-spacing: 15px; margin: 0; text-shadow: 0 0 10px rgba(56, 239, 125, 0.3);">{test_otp}</h1>
                </div>
                <p style="font-size: 14px; color: #666;">✅ Email Configuration: <strong>Working!</strong></p>
                <p style="font-size: 14px; color: #666;">✅ SMTP Server: <strong>Disroot</strong></p>
                <p style="font-size: 14px; color: #666;">✅ Sent at: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="font-size: 12px; color: #999; text-align: center;">
                    This is a test email from your OTP authentication server.
                </p>
            </div>
        </body>
        </html>
        """

        text = f"""
        Email Configuration Test

        This is a test email from your OTP authentication server.

        Your test OTP code is: {test_otp}

        ✅ Email Configuration: Working!
        ✅ SMTP Server: Disroot
        ✅ Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        This is a test email from your OTP authentication server.
        """

        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)

        print(f"Sending test email to: {TEST_EMAIL}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print("\n" + "=" * 70)
        print("✅ Test Email Sent Successfully!")
        print("=" * 70)
        print(f"\nCheck your inbox at {TEST_EMAIL}")
        print("(Note: It may take a few moments to arrive)")
        return True

    except Exception as e:
        print(f"\n❌ Failed to send email: {str(e)}")
        return False

if __name__ == '__main__':
    if test_smtp_connection():
        print("\n")
        send_test_email()
    else:
        print("\n❌ SMTP connection test failed. Not sending test email.")
        print("Please check your configuration and try again.")
