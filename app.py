from flask import Flask, render_template, redirect, url_for, session, flash,request
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
import bcrypt
from flask_mysqldb import MySQL
from flask_mail import Mail,Message
from random import randint

app = Flask(__name__) #WSGI application
app.secret_key = "supersecretkey"

#email verification
app.config["MAIL_SERVER"]='smtp.gmail.com'
app.config["MAIL_PORT"]=465
app.config["MAIL_USERNAME"]='your email'
app.config['MAIL_PASSWORD']='gmail app password'                   
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
mail=Mail(app)

#MYSQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mysql password'
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
@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
            #password hashing
        hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
        
        otp=str(randint(000000,999999))  #generating otp

        #communicate with database using cursor
        cursor = mysql.connection.cursor()  #create cursor object
        cursor.execute("INSERT INTO users (name,email,password, otp, is_verified) VALUES (%s,%s,%s,%s, %s)",
                       (name,email,hashed_password,otp,0)) #insert new row in table
        
        mysql.connection.commit()  #save the changes permanently in mysql
        cursor.close() #close cursor connection

        # send OTP email
        msg = Message('Email Verification OTP',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f"Your OTP is {otp}"
        mail.send(msg)

        session['verify_email'] = email
        flash("OTP sent to your email. Verify to complete signup.","otp")

        return redirect(url_for('verify'))  #redirect to verify user
    return render_template('register.html',form=form)

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
        user = cursor.fetchone()
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
        user_otp = request.form['otp']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT otp FROM users WHERE email=%s", (email,))
        row = cursor.fetchone()

        if row and user_otp == row[0]:
            cursor.execute("""
                UPDATE users
                SET is_verified=1, otp=NULL
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

if __name__ == "__main__":
    app.run(debug=True)
