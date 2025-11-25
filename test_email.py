"""
Test script for email functionality
Sends a test email to verify SMTP configuration
"""
import os
import asyncio
from dotenv import load_dotenv
from src.app.service.background import send_email

# Load environment variables
load_dotenv()

async def test_email():
    """Send a test email to verify email configuration"""
    
    print("=" * 60)
    print("Testing Email Configuration")
    print("=" * 60)
    
    # Display current email settings (without password)
    print(f"\nEmail Host: {os.getenv('EMAIL_HOST')}")
    print(f"Email Port: {os.getenv('EMAIL_PORT')}")
    print(f"Email User: {os.getenv('EMAIL_HOST_USER')}")
    print(f"From Email: {os.getenv('DEFAULT_FROM_EMAIL')}")
    print(f"Use TLS: {os.getenv('EMAIL_USE_TLS')}")
    print(f"Use SSL: {os.getenv('EMAIL_USE_SSL')}")
    
    # Test email details
    to_email = "segzyboiy@gmail.com"
    subject = "Test Email from Alpha Granite Backend"
    body = """
    Hello,
    
    This is a test email from the Alpha Granite backend system.
    
    If you're receiving this, it means the email configuration is working correctly!
    
    Email Settings:
    - SMTP Host: smtp.gmail.com
    - SMTP Port: 587
    - TLS Enabled: Yes
    
    Timestamp: {}
    
    Best regards,
    Alpha Granite System
    """.format(asyncio.get_event_loop().time())
    
    print(f"\n{'=' * 60}")
    print(f"Sending test email to: {to_email}")
    print(f"Subject: {subject}")
    print(f"{'=' * 60}\n")
    
    try:
        # Run send_email in executor since it's synchronous
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, send_email, to_email, subject, body)
        
        print("✅ Email sent successfully!")
        print(f"Please check {to_email} inbox (and spam folder)")
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'=' * 60}")

if __name__ == "__main__":
    print("\nStarting email test...\n")
    asyncio.run(test_email())
    print("\nTest completed.\n")
