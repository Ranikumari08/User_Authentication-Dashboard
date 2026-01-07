Create a Python application with the following requirements:

Task 1. Implement Signup, Login, and Logout functionality using Python.

Store user data in a MySQL/SQL database.

Ensure email uniqueness and password hashing.
Prevent fake signups by implementing email verification using OTP.

Send an OTP to the user’s email during signup.

Complete signup only after OTP verification.

Handle invalid credentials and session management properly.
------------------------------------------------------------------------------------------
Flow: 
    Register → OTP sent → OTP verified → Account activated → Login allowed

File Structure:
User_auth/
│
├── app.py                  # Main Flask application
│
├── requirements.txt        # Project dependencies
│
├── venv/                   # Virtual environment
│
├── templates/
│   ├── app.html             # Base layout (Bootstrap, block content)
│   ├── index.html           # Home page
│   ├── register.html        # Signup form
│   ├── login.html           # Login form
│   ├── verify.html          # OTP input page
│   └── dashboard.html       # Logged-in user page
│
└── static/   (optional)
    └── css/                 # Custom CSS

Database Structure (User table)
users
│
├── id             INT (PK)
├── name           VARCHAR
├── email          VARCHAR (UNIQUE)
├── password       VARCHAR (hashed)
├── otp            VARCHAR(6)
├── verify_token   VARCHAR
├── is_verified    BOOLEAN


