"""Authentication manager for attendance system."""
import pyotp
import qrcode
import os
from io import BytesIO
from modules.db_manager import verify_user, verify_2fa, get_2fa_secret
from modules.utils import CONFIG, logger

def generate_qr_code_url(username, secret):
    """Generates a QR code URL for TOTP setup."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name="Voice Attendance System"
    )

def generate_temp_password():
    """Generates a temporary password."""
    return pyotp.random_base32()[:8]

def create_2fa_qr_code(username):
    """
    Creates and saves a QR code image for setting up 2FA.
    Returns path to QR code image.
    """
    try:
        # Get the user's 2FA secret
        secret = get_2fa_secret(username)
        if not secret:
            logger.error(f"No 2FA secret found for {username}")
            return None
            
        # Generate the provisioning URI
        uri = generate_qr_code_url(username, secret)
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Ensure directory exists
        os.makedirs("qrcodes", exist_ok=True)
        
        # Save image
        qr_path = f"qrcodes/{username}_2fa_qr.png"
        img.save(qr_path)
        
        logger.info(f"Created 2FA QR code for {username}")
        return qr_path
        
    except Exception as e:
        logger.error(f"Failed to create 2FA QR code: {str(e)}")
        return None

def show_2fa_setup_info(username):
    """
    Displays 2FA setup information for a user.
    Creates QR code and displays instructions.
    """
    qr_path = create_2fa_qr_code(username)
    
    if qr_path:
        print("\n🔐 Two-Factor Authentication Setup")
        print(f"QR code saved to: {qr_path}")
        print("\nInstructions:")
        print("1. Open an authenticator app (Google Authenticator, Microsoft Authenticator, etc.)")
        print("2. Scan the QR code with the app")
        print("3. The app will generate a 6-digit code that changes every 30 seconds")
        print("4. Use this code when prompted during login")
        
        # Optional - if we're in an environment that can open files:
        # try:
        #     import webbrowser
        #     webbrowser.open(qr_path)
        # except:
        #     pass
        
        return True
    else:
        print("❌ Failed to set up 2FA. Please contact system administrator.")
        return False