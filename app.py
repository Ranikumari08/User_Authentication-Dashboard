from flask import Flask, render_template, redirect, url_for, session, flash,request
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
import bcrypt
from flask_mysqldb import MySQL
from flask_mail import Mail,Message
from random import randint
import uuid

app = Flask(__name__) #WSGI application
app.secret_key = "supersecretkey"

#email verification with SMTP
app.config["MAIL_SERVER"]='smtp.gmail.com'
app.config["MAIL_PORT"]=465
<<<<<<< HEAD
app.config["MAIL_USERNAME"]='your email if'
app.config['MAIL_PASSWORD']='your gmail app password' #your gmail app password               
=======
app.config["MAIL_USERNAME"]='your email id'
app.config['MAIL_PASSWORD']='your gmail app password'  #your gmail app password           
>>>>>>> 3e1ca6b (email verification added instead of direct otp verify)
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
mail=Mail(app)

#MYSQL db configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your mysql password'
app.config['MYSQL_DB'] = 'userdb'
app.secret_key = 'your_secret_key_here'  #for using sessions

mysql=MySQL(app)  #mysql object creation

#creating register form
class RegisterForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Register")

    #validate unique emails
    def validate_email(self,field):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where email=%s",(field.data,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError('Email Already Taken')


#creating login form
class LoginForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")

@app.route('/')
def index():
    return render_template('index.html')

#register route -> create user + send OTP
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        # password hashing (FIXED)
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        otp = str(randint(100000, 999999))
        verify_token = str(uuid.uuid4())

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, password, otp, verify_token, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, email, hashed_password, otp, verify_token, 0))
        mysql.connection.commit()
        cursor.close()

        # SEND VERIFICATION LINK (NOT OTP PAGE)
        verify_link = url_for('verify_link', token=verify_token, _external=True)

        msg = Message(
            subject='Verify your email',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"""
Hi {name},

Please click the link below to verify your email:

{verify_link}

After clicking the link, you will be asked to enter OTP.
"""

        mail.send(msg)

        flash("Verification link sent to your email.", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


#login route → block if not verified
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            flash("Invalid email or password.", "login")
            return redirect(url_for('login'))

        if user[5] != 1:   # is_verified column
            flash("Please verify your email before logging in.", "login")
            return redirect(url_for('login'))

        if bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))

        flash("Invalid email or password.", "login")
        return redirect(url_for('login'))

    return render_template('login.html', form=form)

   

#dashboard route -> UI 
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id'] 

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where id=%s",(user_id,))
        user = cursor.fetchone() #fetch user id from mysql
        cursor.close()

        if user:
            return render_template('dashboard.html',user=user)
    return redirect(url_for('login')) 


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out successfully.")
    return redirect(url_for('login'))

#verify user -> verify OTP + activate account
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    email = session.get('verify_email')

    if not email:
        flash("Session expired. Please register again.")
        return redirect(url_for('register'))

    if request.method == 'POST':
        user_otp = request.form['otp'] #user entered otp in page

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT otp FROM users WHERE email=%s", (email,))
        row = cursor.fetchone()  # original otp generated

        if row and user_otp == row[0]:  #matching both otps
            cursor.execute("""
                UPDATE users
                SET is_verified=1, otp=NULL, verify_token=NULL
                WHERE email=%s
            """, (email,))
            mysql.connection.commit()
            cursor.close()

            session.pop('verify_email', None)
            flash("Email verified successfully. You can login now.","success")
            return redirect(url_for('login'))

        cursor.close()
        flash("Invalid OTP. Please try again.","otp")
        return redirect(url_for('verify'))

    return render_template('verify.html')

@app.route('/verify/<token>')
def verify_link(token):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT name, email, otp FROM users WHERE verify_token=%s AND is_verified=0",
        (token,)
    )
    user = cursor.fetchone()
    cursor.close()

    if not user:
        flash("Invalid or expired verification link.", "login")
        return redirect(url_for('login'))

    name, email, otp = user

    # SEND OTP EMAIL HERE 
    msg = Message(
        subject='Your OTP for Email Verification',
        sender=app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.body = f"""
Hi {name},

Your OTP for email verification is:

{otp}

Please enter this OTP to complete verification.
"""

    mail.send(msg)

    session['verify_email'] = email
    flash("OTP sent to your email. Please enter it below.", "otp")

    return redirect(url_for('verify'))


if __name__ == "__main__":
    app.run(debug=True)
