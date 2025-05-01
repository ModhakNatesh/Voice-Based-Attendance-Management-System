"""Voice-based attendance management system."""
import os
import sqlite3
import getpass
from datetime import datetime
import qrcode
import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtGui import QIcon
from modules.utils import CONFIG, validate_date, logger
from modules.db_manager import (
    verify_user, verify_2fa, register_student_db, 
    add_user, mark_attendance, fetch_attendance_by_date,
    fetch_attendance_by_range, fetch_attendance_by_student,
    calculate_attendance_percentage, export_to_excel,
    delete_student, rollback_student_registration
)
from modules.audio_processor import record_voice_samples, record_attendance_sample
from modules.voice_processor import generate_speaker_embeddings, identify_speaker
# Update imports to use your current folder structure
from gui.splash_screen import SplashScreen
from gui.main_menu import MainMenu

app = QApplication(sys.argv)

splash = SplashScreen()

def display_banner():
    """Displays application banner."""
    banner = """
    ╔═════════════════════════════════════════════╗
    ║      VOICE-BASED ATTENDANCE SYSTEM          ║
    ╚═════════════════════════════════════════════╝
    """
    print(banner)

def register_student_flow():
    """Complete student registration workflow."""
    print("\n📝 Student Registration")
    
    # 1. Get details
    student_name = input("Full Name: ").strip()
    user_id = input("Student ID: ").strip()
    
    if not student_name or not user_id:
        print("❌ Name and ID are required")
        return
    # 2. Database registration
    print("\n💾 Creating student record...")
    temp_password = register_student_db(student_name, user_id)
    if not temp_password:
        print("❌ Failed to create database record")
        return
    # 3. Voice sample collection
    try:
        print("\n🎙️ Voice Sample Collection (3 samples needed)")
        samples = record_voice_samples(student_name, user_id)
        
        # 4. Train embeddings
        print("\n🧠 Training voice recognition model...")
        if generate_speaker_embeddings():
            print(f"\n✅ Successfully registered {student_name}!")
            print(f"🔑 Temporary password: {temp_password}")
        else:
            raise Exception("Voice model training failed")
            
    except Exception as e:
        print(f"❌ Registration failed: {str(e)}")
        rollback_student_registration(user_id)
        print("⚠️ Rolled back all changes")

def mark_attendance_flow():
    """Workflow for marking attendance using voice."""
    try:
        print("\n📋 Voice Attendance Check-In")
        
        # 1. Record sample
        print("\n🎤 Please speak for attendance verification...")
        audio_sample = record_attendance_sample()
        if not audio_sample:
            print("❌ Failed to record voice sample")
            return
        
        # 2. Identify speaker
        print("\n🔍 Analyzing voice...")
        match, confidence = identify_speaker(audio_sample)
        
        if match is None:
            print(f"❌ Voice not recognized. Confidence score: {confidence:.2f}")
            print("🔁 Please try again or contact admin if the issue persists.")
            logger.warning(f"Voice match failed. Score: {confidence:.2f}")
            return
        
        user_id, name = match
        
        # 3. Display verification and confirm attendance
        print(f"\n👋 Hello, {name}!")
        print(f"🔊 Voice match confidence: {confidence:.2f}")
        
        if confidence < CONFIG['min_voice_confidence']:
            print("⚠️ Low confidence match. Voice not reliable.")
            print("📢 Please contact the admin to manually mark your attendance.")
            logger.warning(f"Low confidence voice match for {user_id} ({name}). Score: {confidence:.2f}")
            return

        # 4. Mark attendance
        current_time = datetime.now()
        attendance_id = mark_attendance(user_id, name)
        
        if attendance_id:
            print(f"\n✅ Attendance marked successfully at {current_time.strftime('%H:%M:%S')}")
            logger.info(f"Attendance marked for {user_id} ({name}) at {current_time}")
        else:
            print("❌ Failed to mark attendance.")
            logger.error(f"Attendance marking failed for {user_id} ({name})")
    
    except Exception as e:
        print(f"❌ Error during attendance: {str(e)}")
        logger.error(f"Attendance error: {str(e)}")


def admin_login():
    """Admin authentication process."""
    print("\n🔐 Admin Login")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    
    # The verify_user function returns role if authenticated, None otherwise
    role = verify_user(username, password)
    
    if not role:
        print("❌ Invalid credentials")
        return False
    
    if role != "admin":
        print("❌ Access denied. Admin privileges required.")
        return False
    
    # Two-factor authentication for admin
    print("\n📱 2FA Verification")
    two_factor_code = input("Enter 2FA code: ").strip()
    
    if verify_2fa(username, two_factor_code):
        print("✅ Admin authentication successful")
        return True
    else:
        print("❌ 2FA verification failed")
        return False

def generate_attendance_report():
    """Generate attendance reports based on various filters."""
    print("\n📊 Attendance Reports")
    
    print("\nSelect report type:")
    print("1. Daily Report")
    print("2. Date Range Report")
    print("3. Student Report")
    print("4. Attendance Percentage")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        date_str = input("Date (YYYY-MM-DD, blank for today): ").strip()
        if not date_str:
            date = datetime.now().date()
        else:
            if not validate_date(date_str):
                print("❌ Invalid date format")
                return
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        records = fetch_attendance_by_date(date)
        print(f"\n📆 Attendance for {date}")
        display_attendance_records(records)
        
    elif choice == '2':
        start_date = input("Start date (YYYY-MM-DD): ").strip()
        end_date = input("End date (YYYY-MM-DD): ").strip()
        
        if not validate_date(start_date) or not validate_date(end_date):
            print("❌ Invalid date format")
            return
            
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start > end:
            print("❌ Start date must be before end date")
            return
            
        records = fetch_attendance_by_range(start, end)
        print(f"\n📅 Attendance from {start} to {end}")
        display_attendance_records(records)
        
    elif choice == '3':
        student_id = input("Student ID: ").strip()
        records = fetch_attendance_by_student(student_id)
        print(f"\n👨‍🎓 Attendance for Student ID: {student_id}")
        display_attendance_records(records)
        
    elif choice == '4':
        student_id = input("Student ID (blank for all students): ").strip()
        start_date = input("Start date (YYYY-MM-DD): ").strip()
        end_date = input("End date (YYYY-MM-DD): ").strip()
        
        if not validate_date(start_date) or not validate_date(end_date):
            print("❌ Invalid date format")
            return
            
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start > end:
            print("❌ Start date must be before end date")
            return
            
        percentages = calculate_attendance_percentage(start, end, student_id)
        
        print(f"\n📊 Attendance Percentages ({start} to {end})")
        print("-" * 50)
        print(f"{'Student ID':<15}{'Name':<25}{'Percentage':<10}")
        print("-" * 50)
        
        for record in percentages:
            print(f"{record['student_id']:<15}{record['name']:<25}{record['percentage']:.2f}%")
    
    else:
        print("❌ Invalid choice")
        return
    
    # Export option
    export_choice = input("\nExport to Excel? (y/n): ").lower().strip()
    if export_choice == 'y':
        if choice == '1':
            # Daily report
            date_str = date.strftime("%Y-%m-%d")
            filename = export_to_excel(start_date=date_str, end_date=date_str)
        elif choice == '2':
            filename = export_to_excel(start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d"))
        elif choice == '3':
            filename = export_to_excel(user_id=student_id)
        else:
            # For student report or percentage, exporting the whole table
            filename = export_to_excel()

        if filename:
            print(f"✅ Exported to {filename}")
        else:
            print("❌ Export failed")

def manual_attendance_marking():
    """Allow admin to manually mark attendance for a student."""
    print("\n✍️ Manual Attendance Entry")
    student_user_id = input("Enter student user ID to mark present: ").strip()

    # Check if the user exists with that user_id and is a student
    conn = sqlite3.connect(CONFIG["attendance_db"])
    conn.row_factory = sqlite3.Row  # Enable access by column name
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users WHERE user_id = ?", (student_user_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        print("❌ No user found with this user ID.")
        return
    elif result['role'] != 'student':
        print("🚫 Only students can have their attendance marked manually.")
        return

    username = result['username']
    confirm = input(f"Are you sure you want to mark attendance for {username} (user_id: {student_user_id})? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled.")
        return

    current_time = datetime.now()
    attendance_id = mark_attendance(student_user_id, current_time)

    if attendance_id:
        print(f"✅ Attendance marked manually for {username} (user_id: {student_user_id}) at {current_time.strftime('%H:%M:%S')}")
        logger.info(f"Manual attendance marked by admin for {student_user_id} - {username}")
    else:
        print("❌ Failed to mark attendance.")


def display_attendance_records(records):
    """Display attendance records in tabular format."""
    if not records:
        print("No records found.")
        return
        
    print("-" * 70)
    print(f"{'Student ID':<15}{'Name':<25}{'Date':<12}{'Time':<10}")
    print("-" * 70)
    
    for row in records:
        user_id = row[1]
        name = row[2]
        timestamp = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
        date = timestamp.date()
        time = timestamp.time()
        print(f"{user_id:<14} {name:<24} {date}   {time}")
        
    print(f"\nTotal Records: {len(records)}")

def manage_students():
    """Admin functions for student management."""
    print("\n👨‍🎓 Student Management")
    
    print("\nSelect operation:")
    print("1. Add New Student")
    print("2. Delete Student")
    print("3. Generate QR Code for Student")
    print("4. Return to Main Menu")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        register_student_flow()
    
    elif choice == '2':
        student_id = input("Student ID to delete: ").strip()
        confirm = input(f"Are you sure you want to delete student {student_id}? (y/n): ").lower().strip()
        
        if confirm == 'y':
            if delete_student(student_id):
                print(f"✅ Student {student_id} deleted successfully")
            else:
                print("❌ Failed to delete student")
    
    elif choice == '3':
        student_id = input("Student ID for QR code: ").strip()
        qr_data = f"STUDENT:{student_id}"
        
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_filename = f"qrcodes/{student_id}_qr.png"
            os.makedirs(os.path.dirname(qr_filename), exist_ok=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(qr_filename)
            
            print(f"✅ QR Code generated: {qr_filename}")
        
        except Exception as e:
            print(f"❌ Failed to generate QR code: {str(e)}")
    
    elif choice == '4':
        return
    
    else:
        print("❌ Invalid choice")

def admin_panel():
    """Admin control panel."""
    if not admin_login():
        return
    
    while True:
        print("\n🔧 Admin Control Panel")
        print("1. Generate Attendance Reports")
        print("2. Manage Students")
        print("3. Manually Mark Attendance")
        print("4. System Configuration")
        print("5. Exit Admin Panel")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            generate_attendance_report()
        elif choice == '2':
            manage_students()
        elif choice == '3':
            manual_attendance_marking()
        elif choice == '4':
            print("\n⚙️ System Configuration")
            print(f"Current configuration: {CONFIG}")
            print("Configuration can be modified in config.json")
        elif choice == '5':
            print("Exiting admin panel...")
            break
        else:
            print("❌ Invalid choice")

def main():
    """Main application entry point."""
    display_banner()
    
    while True:
        print("\n🔹 Main Menu 🔹")
        print("1. Mark Attendance (Voice)")
        print("2. Register New Student")
        print("3. Admin Panel")
        print("4. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            mark_attendance_flow()
        
        elif choice == '2':
            register_student_flow()
        
        elif choice == '3':
            admin_panel()
        
        elif choice == '4':
            print("Thank you for using Voice Attendance System! Goodbye.")
            break
        
        else:
            print("❌ Invalid choice")

def start_gui():
    """Start the GUI application."""
    app = QApplication(sys.argv)
    
    # Set application name and icon
    app.setApplicationName("VBAMS - Voice Based Attendance System")
    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'assets', 'voicesync_icon.png')))

    # Stack to manage multiple screens
    stack = QStackedWidget()
    stack.setWindowTitle("VBAMS - Voice Based Attendance System")
    
    # Create main screens
    splash = SplashScreen()
    main_menu = MainMenu(stack=stack)  # Pass stack reference

    # Add screens to stack
    stack.addWidget(splash)      # index 0
    stack.addWidget(main_menu)   # index 1

    # Show splash screen first
    stack.setCurrentIndex(0)
    stack.show()

    # After splash, show main menu
    splash.start_animation(stack)

    sys.exit(app.exec_())

if __name__ == "__main__":
    # Choose whether to run GUI or CLI version
    use_gui = True  # Set to False if you want CLI mode
    
    if use_gui:
        start_gui()
    else:
        try:
            main()
        except KeyboardInterrupt:
            print("\n\nProgram interrupted. Exiting...")
        except Exception as e:
            logger.critical(f"Unhandled exception: {str(e)}")
            print(f"\n❌ An unexpected error occurred: {str(e)}")
            print("Please check the logs for more details.")
