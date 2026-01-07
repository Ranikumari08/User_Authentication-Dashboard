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
app.py
 ├── /register  → create user + send OTP
 ├── /verify    → verify OTP + activate account
 ├── /login     → block if not verified
 ├── /logout

/templates
 ├── register.html
 ├── login.html
 ├── verify.html  
 ├── dashboard.html
 ├── app.html



