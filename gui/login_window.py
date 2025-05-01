# # login_window.py
# from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
# from PyQt5.QtGui import QFont
# from PyQt5.QtCore import Qt
# import sys

# class LoginWindow(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("VBAMS v1.0 - Login")
#         self.setFixedSize(400, 300)
#         self.setStyleSheet("background-color: #ffffff;")
#         self.initUI()

#     def initUI(self):
#         layout = QVBoxLayout()

#         title = QLabel("Login to VBAMS")
#         title.setFont(QFont("Arial", 18, QFont.Bold))
#         title.setAlignment(Qt.AlignCenter)
#         layout.addWidget(title)

#         # Username
#         self.username_input = QLineEdit()
#         self.username_input.setPlaceholderText("Username")
#         self.username_input.setFont(QFont("Arial", 12))
#         layout.addWidget(self.username_input)

#         # Password
#         self.password_input = QLineEdit()
#         self.password_input.setPlaceholderText("Password")
#         self.password_input.setEchoMode(QLineEdit.Password)
#         self.password_input.setFont(QFont("Arial", 12))
#         layout.addWidget(self.password_input)

#         # 2FA Token (optional initially)
#         self.token_input = QLineEdit()
#         self.token_input.setPlaceholderText("2FA Token (if setup)")
#         self.token_input.setFont(QFont("Arial", 12))
#         layout.addWidget(self.token_input)

#         # Login Button
#         login_button = QPushButton("Login")
#         login_button.setFont(QFont("Arial", 12, QFont.Bold))
#         login_button.clicked.connect(self.handle_login)
#         layout.addWidget(login_button)

#         self.setLayout(layout)

#     def handle_login(self):
#         username = self.username_input.text()
#         password = self.password_input.text()
#         token = self.token_input.text()

#         # TODO: Validate username/password/token here (integrate with your backend)

#         if username == "admin" and password == "admin123":  # Example validation
#             self.show_message("Login Successful!", "Success")
#             # After login, open the right dashboard based on user type
#             # You will later check if user is Admin or Normal user here
#         else:
#             self.show_message("Invalid credentials. Try again.", "Error")

#     def show_message(self, message, title):
#         msg = QMessageBox()
#         msg.setWindowTitle(title)
#         msg.setText(message)
#         msg.exec_()

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = LoginWindow()
#     window.show()
#     sys.exit(app.exec_())
