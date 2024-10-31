import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import gspread
from flask_mail import Mail, Message
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = 'rudra'

# Load Google credentials from the environment variable
credentials_info = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scopes=[
    "https://spreadsheets.google.com/feeds", 
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file", 
    "https://www.googleapis.com/auth/drive"
])

client = gspread.authorize(creds)
sheet = client.open("Members Web").sheet1

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'contact.rudrarvu@gmail.com'
app.config['MAIL_PASSWORD'] = 'ypqa imky byop odyw'
app.config['MAIL_USE_TLS'] = True
mail = Mail(app)

@app.route('/')
def home():
    logged_in = session.get('logged_in', False)
    user_name = session.get('user_name', 'Guest')
    return render_template('index.html', logged_in=logged_in, user_name=user_name)
def home():
    if session.get('logged_in'):
        return redirect(url_for('profile'))
    return render_template('index.html')

@app.route('/aboutus')
def aboutus():
    logged_in = session.get('logged_in', False)
    user_name = session.get('user_name', 'Guest')
    return render_template('aboutus.html', logged_in=logged_in, user_name=user_name)

@app.route('/comingsoon')
def comingsoon():
    logged_in = session.get('logged_in', False)
    user_name = session.get('user_name', 'Guest')
    return render_template('comingsoon.html', logged_in=logged_in, user_name=user_name)

import random
import string

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        
        # Check if the email ends with 'rvu.edu.in'
        if not email.endswith('@rvu.edu.in'):
            flash("Please use your 'rvu.edu.in' email address to register.", "error")
            return redirect(url_for('register'))

        usn = request.form['usn']
        school = request.form.get('school', '')
        semester = request.form.get('semester', '')
        section = request.form.get('section', '')

        # Generate a secure random password
        random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
        password = f"{name.split()[0]}@rudra_{random_chars}"  # e.g., John@rudra_a1B2c

        # Save user data with the generated password
        user_data = {
            "name": name,
            "email": email,
            "usn": usn,
            "school": school,
            "semester": semester,
            "section": section,
            "password": password,
            "password_set": True  # Indicate that password is already set
        }
        sheet.append_row(list(user_data.values()))

        # Send email with the generated password
        msg = Message('Welcome to RUDRA!', sender='contact.rudrarvu@gmail.com', recipients=[email])
        msg.body = (
            f"Hello {name},\n\n"
            "Welcome to RUDRA - The Resourceful Unit for Data Research and Analytics!\n\n"
            "We’re excited to have you on board. You can now confirm your account and start exploring RUDRA’s resources.\n\n"
            f"Your login password is: {password}\n\n"
            "Please keep this password secure and use it to log in to your RUDRA account.\n\n"
            "Welcome to the community, and we look forward to seeing you engage and grow with us!\n\n"
            "Best Regards,\n"
            "The RUDRA Team"
        )
        mail.send(msg)

        flash("Registration successful! You can proceed to check your email to confirm your account and password.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Fetch users and check credentials
        users = sheet.get_all_records()
        user = next((u for u in users if u.get('Email') == email and u.get('Password') == password), None)
        
        if user:
            session['logged_in'] = True
            session['user_name'] = user['Name']
            session['user_email'] = user['Email']  # Store user email in session
            return redirect(url_for('home'))  # Redirecting directly to profile after login
        else:
            flash("Invalid credentials, try again.")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        flash("Please log in to access your profile.", "error")
        return redirect(url_for('login'))
    
    user_name = session.get('user_name')
    email = session.get('user_email')
    
    # Fetch user data from Sheet 1
    users = sheet.get_all_records()
    user_data = next((u for u in users if u.get('Email') == email), None)
    
    if not user_data:
        flash("User not found.", "error")
        return redirect(url_for('home'))

    # Fetch announcements from Sheet 2
    announcements_sheet = client.open("Members Web").get_worksheet(1)  # Assuming Sheet 2 is the second worksheet
    announcements = announcements_sheet.get_all_records()

    masked_password_length = len(user_data['Password']) if 'Password' in user_data else 8

    return render_template('profile.html', 
                           user_name=user_name, 
                           user_data=user_data, 
                           masked_password_length=masked_password_length, 
                           announcements=announcements)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password_page():
    if not session.get('logged_in'):
        flash("Please log in to access this page.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        email = session.get('user_email')
        
        # Fetch user data
        users = sheet.get_all_records()
        user_row = None
        for index, user in enumerate(users, start=2):  # start=2 to account for header row
            if user.get('Email') == email and user.get('Password') == old_password:
                user_row = index
                break

        if user_row is not None:
            # Update password in Google Sheets
            sheet.update_cell(user_row, 7, new_password)  # Assuming password column is at index 7
            flash("Password updated successfully!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Old password is incorrect.", "error")
    
    return render_template('change_password.html')

@app.route('/events')
def events():
    # Fetch Knowledge Drops from Google Sheet (Sheet 3)
    knowledge_sheet = client.open("Members Web").get_worksheet(2)  # Assuming Sheet 3 is the third worksheet
    knowledge_drops_data = knowledge_sheet.get_all_records()
    
    # Process the data to create a list of dictionaries with title, thumbnail, and PDF link
    knowledge_drops = [
        {
            'title': row['Title'],
            'thumbnail': row['Thumbnail Image URL'],  # Column for image URLs
            'pdf': row['Pdf Link']  # Column for PDF links
        }
        for row in knowledge_drops_data
    ]

    # Pass the list of knowledge drops to the template
    latest_knowledge_drop = knowledge_drops[-1] if knowledge_drops else None  # Get the latest drop if available
    
    return render_template('events.html', latest_knowledge_drop=latest_knowledge_drop, knowledge_drops=knowledge_drops)



@app.route('/all_knowledge_drops')
def all_knowledge_drops():
    # Fetch Knowledge Drops from Google Sheet (Sheet 3)
    knowledge_sheet = client.open("Members Web").get_worksheet(2)  # Assuming Sheet 3 is the 3rd worksheet
    knowledge_drops_data = knowledge_sheet.get_all_records()

    # Print the first row to check for the exact column names
    if knowledge_drops_data:
        print("Column names:", knowledge_drops_data[0].keys())

    # Process the data with updated column names if necessary
    knowledge_drops = []
    for row in knowledge_drops_data:
        try:
            knowledge_drops.append({
                'title': row['Title'],
                'thumbnail': row['Thumbnail Image URL'],  # Adjust name if it doesn’t match
                'pdf': row['Pdf Link']  # Adjust name to match exactly as it appears in the sheet
            })
        except KeyError as e:
            print(f"KeyError: {e} - Check the column names in the Google Sheet.")

    return render_template('all_knowledge_drops.html', knowledge_drops=knowledge_drops)

@app.route('/knowledge_drop')
def knowledge_drop():
    return render_template(
        'knowledgedrop31oct.html'
    )






if __name__ == '__main__':
    app.run(debug=True)
