import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import gspread
from flask_mail import Mail, Message
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = 'rudra'

# Load Google credentials from the environment variable
credentials_info = "/etc/secrets/Google_Credentials.json"
creds = Credentials.from_service_account_file(credentials_info, scopes=[
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

# Enhanced RUDRA Position Application System - Flask Backend

from datetime import datetime
import json

# Add these routes to your existing Flask app

@app.route('/apply', methods=['GET', 'POST'])
def apply_for_position():
    if not session.get('logged_in'):
        flash("Please log in to apply for positions.", "error")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        user_email = session.get('user_email')
        application_data = {
            "email": user_email,
            "name": session.get('user_name'),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "personal_info": {
                "year_of_study": request.form.get('year_of_study'),
                "previous_experience": request.form.get('previous_experience'),
                "technical_skills": request.form.get('technical_skills'),
                "leadership_experience": request.form.get('leadership_experience'),
                "time_commitment": request.form.get('time_commitment'),
                "academic_performance": request.form.get('academic_performance')
            },
            "preferences": {
                "primary_choice": request.form.get('primary_choice'),
                "secondary_choice": request.form.get('secondary_choice'),
                "why_primary": request.form.get('why_primary'),
                "relevant_experience": request.form.get('relevant_experience'),
                "specific_skills": request.form.get('specific_skills')
            },
            "position_specific": {
                "question_1": request.form.get('position_q1'),
                "question_2": request.form.get('position_q2'),
                "question_3": request.form.get('position_q3')
            },
            "assessment_answers": {
                "scenario_1": request.form.get('scenario_1'),
                "scenario_2": request.form.get('scenario_2'),
                "innovation_project": request.form.get('innovation_project'),
                "collaboration_example": request.form.get('collaboration_example'),
                "availability": request.form.get('availability')
            },
            "status": "Applied",
            "interview_status": "Pending",
            "admin_notes": "",
            "application_score": 0
        }
        
        # Save to Google Sheets
        applications_sheet = client.open("Members Web").get_worksheet(3)  # Sheet 4 for applications
        
        # Prepare row data
        row_data = [
            application_data["email"],
            application_data["name"],
            application_data["timestamp"],
            application_data["personal_info"]["year_of_study"],
            application_data["personal_info"]["previous_experience"],
            application_data["personal_info"]["technical_skills"],
            application_data["personal_info"]["leadership_experience"],
            application_data["personal_info"]["time_commitment"],
            application_data["personal_info"]["academic_performance"],
            application_data["preferences"]["primary_choice"],
            application_data["preferences"]["secondary_choice"],
            application_data["preferences"]["why_primary"],
            application_data["preferences"]["relevant_experience"],
            application_data["preferences"]["specific_skills"],
            application_data["position_specific"]["question_1"],
            application_data["position_specific"]["question_2"],
            application_data["position_specific"]["question_3"],
            application_data["assessment_answers"]["scenario_1"],
            application_data["assessment_answers"]["scenario_2"],
            application_data["assessment_answers"]["innovation_project"],
            application_data["assessment_answers"]["collaboration_example"],
            application_data["assessment_answers"]["availability"],
            application_data["status"],
            application_data["interview_status"],
            application_data["admin_notes"],
            application_data["application_score"]
        ]
        
        applications_sheet.append_row(row_data)
        
        # Send confirmation email
        send_application_confirmation(user_email, application_data["name"], application_data["preferences"]["primary_choice"])
        
        flash("Application submitted successfully! You'll receive a confirmation email shortly.", "success")
        return redirect(url_for('application_status'))
    
    # Get available positions and their current application counts
    positions_data = get_detailed_positions_data()
    
    return render_template('apply_position.html', positions=positions_data)

@app.route('/application_status')
def application_status():
    if not session.get('logged_in'):
        flash("Please log in to view your application status.", "error")
        return redirect(url_for('login'))
    
    user_email = session.get('user_email')
    applications_sheet = client.open("Members Web").get_worksheet(3)
    applications = applications_sheet.get_all_records()
    
    user_applications = [app for app in applications if app.get('Email') == user_email]
    
    return render_template('application_status.html', applications=user_applications)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_admin_credentials(username, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash("Admin login successful!", "success")
            return redirect(url_for('admin_applications'))
        else:
            flash("Invalid admin credentials!", "error")
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash("Admin logged out successfully!", "info")
    return redirect(url_for('home'))

@app.route('/admin/applications')
def admin_applications():
    if not session.get('admin_logged_in'):
        flash("Admin access required.", "error")
        return redirect(url_for('admin_login'))
    
    applications_sheet = client.open("Members Web").get_worksheet(3)
    applications = applications_sheet.get_all_records()
    
    # Group by position and sort by application score
    grouped_applications = {}
    for app in applications:
        position = app.get('Primary Choice', 'Unknown')
        if position not in grouped_applications:
            grouped_applications[position] = []
        grouped_applications[position].append(app)
    
    # Sort applications by score (descending)
    for position in grouped_applications:
        grouped_applications[position].sort(key=lambda x: x.get('Application Score', 0), reverse=True)
    
    return render_template('admin_applications.html', applications=grouped_applications)

def verify_admin_credentials(username, password):
    """Verify admin credentials from Google Sheets"""
    try:
        admin_sheet = client.open("Members Web").get_worksheet(4)  # Sheet 5 for admin credentials
        admin_data = admin_sheet.get_all_records()
        
        for admin in admin_data:
            if admin.get('Username') == username and admin.get('Password') == password:
                return True
        return False
    except Exception as e:
        print(f"Error verifying admin credentials: {e}")
        return False

def get_detailed_positions_data():
    """Get detailed position information with application counts"""
    applications_sheet = client.open("Members Web").get_worksheet(3)
    applications = applications_sheet.get_all_records()
    
    # Count applications per position
    position_counts = {}
    for app in applications:
        position = app.get('Primary Choice', 'Unknown')
        position_counts[position] = position_counts.get(position, 0) + 1
    
    # Define detailed positions with their complete information
    positions = {
        "President": {
            "status": "Selected",
            "applications": 0,
            "category": "Core Leadership",
            "icon": "fa-crown",
            "description": "The President is the visionary leader of the club, responsible for ensuring relevance to university standards, alignment with institutional policies, and driving the overall direction and credibility of the club.",
            "key_responsibilities": [
                "Leads the club strategically and administratively",
                "Acts as the chief representative in matters involving the university or formal bodies",
                "Ensures the club's structure, values, and initiatives align with long-term academic and professional goals",
                "Makes executive decisions during crises or high-stake moments",
                "Mentors all executive heads, especially in shaping relevance and sustainability of the club",
                "Stays focused on policies, recognition, and strategic alignment with institutional expectations"
            ],
            "required_skills": ["Leadership", "Strategic Thinking", "Communication", "Policy Understanding"],
            "time_commitment": "15+ hours/week",
            "max_applications": 0
        },
        "Vice President": {
            "status": "Open",
            "applications": position_counts.get("Vice President", 0),
            "category": "Core Leadership",
            "icon": "fa-handshake",
            "description": "The Vice President is the operational commander and advisor, ensuring daily excellence across departments, while managing the public face and outreach of the club through high-reputation initiatives.",
            "key_responsibilities": [
                "Second-in-command and trusted decision-maker in the President's absence",
                "Coordinates actively across all internal teams (Tech, Design, Events, R&D, WebOps)",
                "Advises and supports heads like Tech Head, R&D Head, and Event Leads with strategic and intellectual input",
                "Manages external-facing activities: AMA sessions, Podcasts, Online initiatives",
                "Brings in contacts, mentors, and external speakers, using network and knowledge",
                "Ensures that high-quality, outreach-driven events continue"
            ],
            "required_skills": ["Leadership", "Networking", "Communication", "Strategic Planning"],
            "time_commitment": "12-15 hours/week",
            "max_applications": 8
        },
        "Secretary": {
            "status": "Open",
            "applications": position_counts.get("Secretary", 0),
            "category": "Core Leadership",
            "icon": "fa-file-alt",
            "description": "The Secretary serves as the formal point of contact between the club and the university, ensuring all institutional requirements, documentation, and approvals are handled with clarity and professionalism.",
            "key_responsibilities": [
                "Manages official communications with university bodies, clubs council, and other administrative cells",
                "Submits required reports, event proposals, and compliance documentation",
                "Ensures that the club remains aligned with university policies, timelines, and formats",
                "Maintains high-level documentation such as annual reports, meeting records, and structural changes",
                "Works closely with the President to maintain institutional relevance and status"
            ],
            "required_skills": ["Documentation", "Communication", "Attention to Detail", "Policy Knowledge"],
            "time_commitment": "8-10 hours/week",
            "max_applications": 6
        },
        "Associate Secretary": {
            "status": "Open",
            "applications": position_counts.get("Associate Secretary", 0),
            "category": "Core Leadership",
            "icon": "fa-clipboard-list",
            "description": "The Associate Secretary handles the internal operational functioning of the club, ensuring every team is aligned, every deadline is tracked, and all internal records are maintained.",
            "key_responsibilities": [
                "Maintains the internal club calendar, schedules, and task timelines",
                "Coordinates with all team leads to collect updates and ensure deliverables are met",
                "Manages and organizes event-wise documentation, internal meeting notes, and project trackers",
                "Sends reminders, collects inputs, and keeps internal execution running smoothly",
                "Acts as the Secretary's counterpart for internal affairs"
            ],
            "required_skills": ["Organization", "Time Management", "Communication", "Record Keeping"],
            "time_commitment": "6-8 hours/week",
            "max_applications": 5
        },
        "Executive Director – Financial Operations": {
            "status": "Open",
            "applications": position_counts.get("Executive Director – Financial Operations", 0),
            "category": "Finance Wing",
            "icon": "fa-university",
            "description": "Handles all institutional coordination regarding finances — especially NFAs, documentation, and liaison with university entities.",
            "key_responsibilities": [
                "Prepares and submits NFA (Note for Approval) forms",
                "Coordinates with Finance Committee, Dean of Student Affairs, Faculty Advisor, and Representatives Club",
                "Tracks reimbursements and ensures proper fund utilization",
                "Maintains clean and complete records of all official expenses",
                "Collaborates with Secretary and Director of Events for approvals and documentation"
            ],
            "required_skills": ["Financial Management", "Documentation", "University Relations", "Attention to Detail"],
            "time_commitment": "6-8 hours/week",
            "max_applications": 5
        },
        "Treasurer": {
            "status": "Open",
            "applications": position_counts.get("Treasurer", 0),
            "category": "Finance Wing",
            "icon": "fa-coins",
            "description": "The Treasurer is the strategic revenue architect of the club, responsible for ensuring self-sustainability through partnerships, sponsorships, and creative monetization.",
            "key_responsibilities": [
                "Creates and executes fund-raising strategies",
                "Builds relationships with external sponsors, partners, or alumni",
                "Designs monetizable initiatives: paid workshops, merchandise, donor drives",
                "Collaborates with Tech and Events teams for fundable offerings",
                "Maintains incoming funds ledger and coordinates with VP for partnerships"
            ],
            "required_skills": ["Business Development", "Fundraising", "Partnership Management", "Financial Planning"],
            "time_commitment": "8-10 hours/week",
            "max_applications": 6
        },
        "Executive Director – Knowledge & Tech Strategy": {
            "status": "Open",
            "applications": position_counts.get("Executive Director – Knowledge & Tech Strategy", 0),
            "category": "Technology & Knowledge Wing",
            "icon": "fa-brain",
            "description": "Leads all elite tech and learning initiatives. Designs content structures like Knowledge Drops and ensures elite section upholds high standards.",
            "key_responsibilities": [
                "Screens and mentors elite tech members",
                "Plans and oversees Knowledge Drops, quizzes, and screening tests",
                "Works closely with R&D and WebOps for integration",
                "Guides tech excellence and real-world content application",
                "Collaborates on educational initiatives that reflect the club's technical brand"
            ],
            "required_skills": ["Technical Leadership", "Content Strategy", "Mentoring", "Quality Assurance"],
            "time_commitment": "10-12 hours/week",
            "max_applications": 7
        },
        "Director of Knowledge Initiatives": {
            "status": "Open",
            "applications": position_counts.get("Director of Knowledge Initiatives", 0),
            "category": "Technology & Knowledge Wing",
            "icon": "fa-book",
            "description": "Manages execution of the Knowledge Drop series, ensuring timely contributions and polished outcomes.",
            "key_responsibilities": [
                "Maintains contribution tracker for Knowledge Drops",
                "Coordinates contributor timelines and internal reviews",
                "Works with WebOps and Design teams for publishing",
                "Reports progress to Executive Director – Tech Strategy",
                "Ensures quality and consistency of knowledge content"
            ],
            "required_skills": ["Content Management", "Project Coordination", "Quality Control", "Communication"],
            "time_commitment": "6-8 hours/week",
            "max_applications": 5
        },
        "Director of WebOps & Infrastructure": {
            "status": "Open",
            "applications": position_counts.get("Director of WebOps & Infrastructure", 0),
            "category": "Technology & Knowledge Wing",
            "icon": "fa-server",
            "description": "Executes all technical content uploads, builds and maintains club's online platform.",
            "key_responsibilities": [
                "Maintains the official club website",
                "Uploads events, Knowledge Drops, project results, etc.",
                "Collaborates with Design and Content teams",
                "Ensures SEO, responsiveness, and scalability",
                "Must deliver final website by July-end as per club goals"
            ],
            "required_skills": ["Flask", "HTML/CSS", "JavaScript", "Web Development", "Server Management"],
            "time_commitment": "8-10 hours/week",
            "max_applications": 8,
            "technical_requirements": {
                "mandatory": ["Flask", "HTML", "CSS", "JavaScript"],
                "preferred": ["Python", "Bootstrap", "Database Management", "Git"]
            }
        },
        "Executive Director – Design & Content Creation": {
            "status": "Open",
            "applications": position_counts.get("Executive Director – Design & Content Creation", 0),
            "category": "Creative & Media Wing",
            "icon": "fa-palette",
            "description": "Owns the visual and textual branding of the club. Ensures polished and unified identity across platforms.",
            "key_responsibilities": [
                "Designs posters, decks, social media content",
                "Edits final write-ups, blogs, speaker announcements, etc.",
                "Collaborates with all verticals to deliver visual outputs",
                "Maintains club's design templates, color schemes, and brand guidelines",
                "Ensures consistent visual identity across all platforms"
            ],
            "required_skills": ["Graphic Design", "Content Creation", "Brand Management", "Adobe Creative Suite"],
            "time_commitment": "8-10 hours/week",
            "max_applications": 6
        },
        "Director of Public Engagement & Outreach": {
            "status": "Open",
            "applications": position_counts.get("Director of Public Engagement & Outreach", 0),
            "category": "Public Relations & Outreach",
            "icon": "fa-bullhorn",
            "description": "Reports to the Vice President and manages all public-facing intellectual content and outreach events.",
            "key_responsibilities": [
                "Manages AMAs, Podcasts, and online sessions",
                "Coordinates with Treasurer for sponsorships",
                "Reaches out to guests and speakers",
                "Ensures public communication maintains tone and quality",
                "Collaborates with Design, Content, and WebOps"
            ],
            "required_skills": ["Public Relations", "Event Management", "Communication", "Networking"],
            "time_commitment": "8-10 hours/week",
            "max_applications": 6
        },
        "Executive Director – R&D": {
            "status": "Disabled",
            "applications": 0,
            "category": "Research & Development Wing",
            "icon": "fa-microscope",
            "description": "Leads elite research and industry projects, ensuring every elite member has a publication or meaningful industrial contribution.",
            "key_responsibilities": [
                "Must pass the elite section screening",
                "Coordinates with faculty and mentors",
                "Oversees project timelines, deliverables, and quality",
                "Ensures paper publication or industry certificates for each participant",
                "Organizes review cycles and escalates blockers"
            ],
            "required_skills": ["Research Experience", "Project Management", "Academic Writing", "Data Analysis"],
            "time_commitment": "10-12 hours/week",
            "max_applications": 0,
            "disabled_reason": "This position will be enabled after the screening test is held and you qualify in the screening test of the elite tech section of the club."
        },
        "Associate Executive Director – R&D": {
            "status": "Disabled",
            "applications": 0,
            "category": "Research & Development Wing",
            "icon": "fa-flask",
            "description": "Supports execution and tracking of elite R&D initiatives.",
            "key_responsibilities": [
                "Must also be from the elite section",
                "Tracks project progress and member activity",
                "Assists with documentation, poster creation, and submissions",
                "Bridges member-mentor communications",
                "Supports the ED–R&D in driving quality and output"
            ],
            "required_skills": ["Research Support", "Documentation", "Communication", "Project Tracking"],
            "time_commitment": "6-8 hours/week",
            "max_applications": 0,
            "disabled_reason": "This position will be enabled after the screening test is held and you qualify in the screening test of the elite tech section of the club."
        },
        "Director of Events": {
            "status": "Open",
            "applications": position_counts.get("Director of Events", 0),
            "category": "Event Management Wing",
            "icon": "fa-calendar-check",
            "description": "Plans and executes all club events with professionalism, relevance, and logistical clarity.",
            "key_responsibilities": [
                "Builds event formats and guides event teams",
                "Secures permissions and handles logistics",
                "Coordinates with Secretary and Finance for NFAs",
                "Delivers flagship events with end-to-end accountability",
                "Manages vendor relationships and venue coordination"
            ],
            "required_skills": ["Event Planning", "Logistics Management", "Team Leadership", "Budget Management"],
            "time_commitment": "10-12 hours/week",
            "max_applications": 7
        },
        "Executive Director – Event Coordination": {
            "status": "Open",
            "applications": position_counts.get("Executive Director – Event Coordination", 0),
            "category": "Event Management Wing",
            "icon": "fa-sync-alt",
            "description": "Keeps the calendar clean and teams synced. Ensures timely and stress-free execution.",
            "key_responsibilities": [
                "Maintains a master event calendar",
                "Ensures no inter-departmental clashes",
                "Tracks task delegation across teams",
                "Reports progress and delays",
                "Supports Director of Events in last-mile delivery"
            ],
            "required_skills": ["Coordination", "Time Management", "Communication", "Problem Solving"],
            "time_commitment": "6-8 hours/week",
            "max_applications": 5
        }
    }
    
    return positions

def get_position_specific_questions(position):
    """Get detailed position-specific questions based on the role"""
    questions = {
        "Vice President": {
            "q1": "How would you leverage your network to bring in external speakers, mentors, and industry professionals for RUDRA events?",
            "q2": "Describe a time when you had to coordinate multiple teams or departments. What strategies did you use to ensure everyone stayed aligned?",
            "q3": "What innovative online initiatives (AMAs, podcasts, webinars) would you implement to enhance RUDRA's public reputation?"
        },
        "Secretary": {
            "q1": "Describe your experience with formal documentation, report writing, and university communications. Provide specific examples.",
            "q2": "How would you ensure that all club activities remain compliant with university policies and regulatory requirements?",
            "q3": "What systems would you implement to track institutional deadlines, approvals, and maintain comprehensive records?"
        },
        "Associate Secretary": {
            "q1": "How would you design and maintain an internal coordination system to track all team deliverables and deadlines?",
            "q2": "Describe your approach to collecting updates from multiple teams and ensuring smooth internal communication.",
            "q3": "What tools and processes would you use to organize meeting notes, project trackers, and internal documentation?"
        },
        "Executive Director – Financial Operations": {
            "q1": "Explain your understanding of university financial procedures, NFA processes, and institutional fund management.",
            "q2": "How would you coordinate with university bodies like Finance Committee and Dean of Student Affairs for approvals?",
            "q3": "Describe your experience with budget tracking, expense documentation, and financial record maintenance."
        },
        "Treasurer": {
            "q1": "What creative fund-raising strategies would you implement to make RUDRA financially self-sustainable?",
            "q2": "How would you identify and approach potential sponsors, partners, or alumni for long-term financial support?",
            "q3": "Describe a monetizable initiative you would design (workshops, merchandise, etc.) and its implementation strategy."
        },
        "Executive Director – Knowledge & Tech Strategy": {
            "q1": "How would you design screening criteria and mentoring programs for the elite tech section of RUDRA?",
            "q2": "Describe your vision for Knowledge Drops and how you would ensure they maintain high technical standards.",
            "q3": "What real-world tech applications and industry-relevant content would you integrate into RUDRA's educational initiatives?"
        },
        "Director of Knowledge Initiatives": {
            "q1": "How would you create and maintain a contribution tracking system for Knowledge Drops to ensure timely delivery?",
            "q2": "Describe your approach to coordinating with contributors, reviewers, and the publishing team for quality content.",
            "q3": "What quality control measures would you implement to ensure consistency across all knowledge content?"
        },
        "Director of WebOps & Infrastructure": {
            "q1": "Describe your experience with Flask, HTML, CSS, and JavaScript. Provide examples of projects you've built using these technologies.",
            "q2": "How would you ensure the RUDRA website is scalable, SEO-optimized, and mobile-responsive while meeting the July-end deadline?",
            "q3": "What technical infrastructure would you implement for content management, user authentication, and database integration?"
        },
        "Executive Director – Design & Content Creation": {
            "q1": "How would you develop and maintain brand guidelines to ensure consistent visual identity across all RUDRA platforms?",
            "q2": "Describe your experience with design tools and your approach to creating engaging social media content and marketing materials.",
            "q3": "What workflow would you establish for collaborating with different teams while maintaining design quality and brand consistency?"
        },
        "Director of Public Engagement & Outreach": {
            "q1": "How would you identify, reach out to, and convince industry experts and speakers to participate in RUDRA events?",
            "q2": "Describe your strategy for managing AMAs, podcasts, and online sessions to maximize audience engagement.",
            "q3": "What public relations strategies would you implement to enhance RUDRA's reputation and visibility?"
        },
        "Executive Director – R&D": {
            "q1": "This position requires elite section qualification. Questions will be available after screening test.",
            "q2": "This position requires elite section qualification. Questions will be available after screening test.",
            "q3": "This position requires elite section qualification. Questions will be available after screening test."
        },
        "Associate Executive Director – R&D": {
            "q1": "This position requires elite section qualification. Questions will be available after screening test.",
            "q2": "This position requires elite section qualification. Questions will be available after screening test.",
            "q3": "This position requires elite section qualification. Questions will be available after screening test."
        },
        "Director of Events": {
            "q1": "Describe your experience with end-to-end event planning, including logistics, vendor management, and budget coordination.",
            "q2": "How would you coordinate with university bodies for permissions, approvals, and ensure events meet institutional standards?",
            "q3": "What contingency plans would you develop for potential event challenges, and how would you ensure seamless execution?"
        },
        "Executive Director – Event Coordination": {
            "q1": "How would you create and maintain a master event calendar to prevent conflicts and ensure smooth scheduling?",
            "q2": "Describe your approach to task delegation across teams and tracking progress to meet event deadlines.",
            "q3": "What communication systems would you implement to ensure all stakeholders stay informed and aligned?"
        }
    }
    
    return questions.get(position, {
        "q1": "How would you contribute to RUDRA's mission of empowering students with data science skills?",
        "q2": "What unique value would you bring to this position and how would you measure your success?",
        "q3": "How would you handle challenges and collaborate with other team members in your role?"
    })

def send_application_confirmation(email, name, position):
    """Send confirmation email to applicant"""
    msg = Message('Application Confirmation - RUDRA Position', 
                  sender='contact.rudrarvu@gmail.com', 
                  recipients=[email])
    msg.body = f"""
Dear {name},

Thank you for applying for the position of {position} at RUDRA!

Your application has been successfully submitted and is under review. Our team will carefully evaluate your application and get back to you within 7-10 business days.

What happens next:
1. Application Review: Our team will review your application and responses
2. Shortlisting: Top candidates will be contacted for interviews (we typically interview 5-8 candidates per position)
3. Interview: Selected candidates will receive interview invitations with Google Meet links
4. Final Selection: Results will be communicated via email within 48 hours of interview

You can check your application status anytime by logging into your RUDRA account and visiting the Application Status page.

If you have any questions, please don't hesitate to reach out to us.

Best regards,
The RUDRA Team
Resourceful Unit for Data Research and Analytics
RV University
"""
    mail.send(msg)

def send_interview_email(email, interview_link, interview_datetime, position, additional_message):
    """Send interview invitation email"""
    msg = Message(f'Interview Invitation - {position} Position at RUDRA', 
                  sender='contact.rudrarvu@gmail.com', 
                  recipients=[email])
    msg.body = f"""
Dear Candidate,

Congratulations! You have been shortlisted for an interview for the {position} position at RUDRA.

Interview Details:
📅 Date & Time: {interview_datetime}
🔗 Google Meet Link: {interview_link}
💼 Position: {position}

Interview Guidelines:
• Duration: 20-30 minutes
• Format: Technical and behavioral questions
• Please join 5 minutes early
• Ensure stable internet connection
• Keep your camera on during the interview
• Have a quiet environment ready

{additional_message}

Preparation Tips:
• Review your application responses
• Prepare examples of your relevant experience
• Think about how you can contribute to RUDRA's mission
• Be ready to discuss your technical skills and project experience

If you have any technical issues or need to reschedule, please contact us immediately at contact.rudrarvu@gmail.com.

We look forward to meeting you!

Best regards,
The RUDRA Team
Resourceful Unit for Data Research and Analytics
RV University
"""
    mail.send(msg)

def setup_applications_sheet():
    """Set up the applications sheet with proper headers"""
    try:
        try:
            applications_sheet = client.open("Members Web").get_worksheet(3)
        except:
            spreadsheet = client.open("Members Web")
            applications_sheet = spreadsheet.add_worksheet(title="Applications", rows="1000", cols="26")
        
        # Set up headers
        headers = [
            "Email", "Name", "Timestamp", "Year of Study", "Previous Experience", 
            "Technical Skills", "Leadership Experience", "Time Commitment", "Academic Performance",
            "Primary Choice", "Secondary Choice", "Why Primary", "Relevant Experience", 
            "Specific Skills", "Position Q1", "Position Q2", "Position Q3", "Scenario 1", 
            "Scenario 2", "Innovation Project", "Collaboration Example", "Availability",
            "Status", "Interview Status", "Admin Notes", "Application Score"
        ]
        
        # Check if headers exist, if not add them
        try:
            existing_headers = applications_sheet.row_values(1)
            if not existing_headers or len(existing_headers) < len(headers):
                # Clear the first row and add proper headers
                applications_sheet.clear()
                applications_sheet.insert_row(headers, 1)
        except:
            applications_sheet.insert_row(headers, 1)
            
        return True
    except Exception as e:
        print(f"Error setting up applications sheet: {e}")
        return False

def setup_admin_credentials_sheet():
    """Set up the admin credentials sheet"""
    try:
        try:
            admin_sheet = client.open("Members Web").get_worksheet(4)
        except:
            spreadsheet = client.open("Members Web")
            admin_sheet = spreadsheet.add_worksheet(title="Admin Credentials", rows="100", cols="5")
        
        # Set up headers
        headers = ["Username", "Password", "Role", "Created Date", "Last Login"]
        
        # Check if headers exist, if not add them
        try:
            existing_headers = admin_sheet.row_values(1)
            if not existing_headers or len(existing_headers) < len(headers):
                # Clear the sheet and add proper headers
                admin_sheet.clear()
                admin_sheet.insert_row(headers, 1)
                
                # Add default admin credentials (only if sheet is empty)
                default_admins = [
                    ["admin_rudra", "SecurePass123!", "Super Admin", datetime.now().strftime("%Y-%m-%d"), ""],
                    ["president_rudra", "PresidentPass456!", "President", datetime.now().strftime("%Y-%m-%d"), ""],
                    ["vp_rudra", "VPPass789!", "VP", datetime.now().strftime("%Y-%m-%d"), ""]
                ]
                
                for admin in default_admins:
                    admin_sheet.append_row(admin)
                    
        except:
            admin_sheet.insert_row(headers, 1)
            
        return True
    except Exception as e:
        print(f"Error setting up admin credentials sheet: {e}")
        return False

# Additional routes for admin functionality
@app.route('/admin/update_status', methods=['POST'])
def update_application_status():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Admin access required'})
    
    data = request.get_json()
    email = data.get('email')
    status = data.get('status')
    
    try:
        applications_sheet = client.open("Members Web").get_worksheet(3)
        applications = applications_sheet.get_all_records()
        
        for i, app in enumerate(applications, start=2):  # Start from row 2 (header is row 1)
            if app.get('Email') == email:
                applications_sheet.update_cell(i, 23, status)  # Status column (column 23)
                break
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/save_notes', methods=['POST'])
def save_admin_notes():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Admin access required'})
    
    data = request.get_json()
    email = data.get('email')
    notes = data.get('notes')
    
    try:
        applications_sheet = client.open("Members Web").get_worksheet(3)
        applications = applications_sheet.get_all_records()
        
        for i, app in enumerate(applications, start=2):  # Start from row 2 (header is row 1)
            if app.get('Email') == email:
                applications_sheet.update_cell(i, 25, notes)  # Admin Notes column (column 25)
                break
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/export_applications')
def export_applications():
    if not session.get('admin_logged_in'):
        flash("Admin access required.", "error")
        return redirect(url_for('admin_login'))
    
    try:
        applications_sheet = client.open("Members Web").get_worksheet(3)
        applications = applications_sheet.get_all_records()
        
        # Create CSV content
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        if applications:
            writer.writerow(applications[0].keys())
            
            # Write data
            for app in applications:
                writer.writerow(app.values())
        
        csv_content = output.getvalue()
        output.close()
        
        # Create response
        from flask import make_response
        response = make_response(csv_content)
        response.headers["Content-Disposition"] = "attachment; filename=rudra_applications.csv"
        response.headers["Content-type"] = "text/csv"
        
        return response
        
    except Exception as e:
        flash(f"Error exporting applications: {str(e)}", "error")
        return redirect(url_for('admin_applications'))

@app.route('/admin/send_interview_invite', methods=['POST'])
def send_interview_invite():
    if not session.get('admin_logged_in'):
        flash("Admin access required.", "error")
        return redirect(url_for('admin_login'))
    
    # Debug: Print all form data
    print("=== FORM DATA DEBUG ===")
    print("Form data:", request.form)
    print("Selected applicants:", request.form.getlist('selected_applicants'))
    
    selected_emails = request.form.getlist('selected_applicants')
    interview_link = request.form.get('interview_link')
    interview_datetime = request.form.get('interview_datetime')
    position = request.form.get('position', 'RUDRA Position')
    additional_message = request.form.get('additional_message', '')
    
    print(f"Selected emails: {selected_emails}")
    print(f"Interview link: {interview_link}")
    print(f"Interview datetime: {interview_datetime}")
    print(f"Position: {position}")
    
    if not selected_emails:
        flash("No candidates selected. Please select candidates before sending invitations.", "error")
        return redirect(url_for('admin_applications'))
    
    if not interview_link or not interview_datetime:
        flash("Please provide both interview link and date/time.", "error")
        return redirect(url_for('admin_applications'))
    
    try:
        # Update status in Google Sheets
        applications_sheet = client.open("Members Web").get_worksheet(3)
        applications = applications_sheet.get_all_records()
        
        updated_count = 0
        for i, app in enumerate(applications, start=2):  # Start from row 2 (header is row 1)
            if app.get('Email') in selected_emails:
                applications_sheet.update_cell(i, 24, "Interview Scheduled")  # Interview Status column
                updated_count += 1
                print(f"Updated status for: {app.get('Email')}")
        
        # Send interview emails
        email_sent_count = 0
        for email in selected_emails:
            try:
                send_interview_email(email, interview_link, interview_datetime, position, additional_message)
                email_sent_count += 1
                print(f"Email sent successfully to: {email}")
            except Exception as e:
                print(f"Failed to send email to {email}: {str(e)}")
                # Continue with other emails even if one fails
        
        if email_sent_count > 0:
            flash(f"Interview invitations sent to {email_sent_count} applicants for {position}. Status updated for {updated_count} applications.", "success")
        else:
            flash("Failed to send any interview invitations. Please check email configuration.", "error")
            
    except Exception as e:
        print(f"Error in send_interview_invite: {str(e)}")
        flash(f"Error processing interview invitations: {str(e)}", "error")
    
    return redirect(url_for('admin_applications'))

# Enhanced email sending function with better error handling
def send_interview_email(email, interview_link, interview_datetime, position, additional_message):
    """Send interview invitation email with enhanced error handling"""
    try:
        msg = Message(f'Interview Invitation - {position} Position at RUDRA', 
                      sender='contact.rudrarvu@gmail.com', 
                      recipients=[email])
        
        msg.body = f"""
Dear Candidate,

Congratulations! You have been shortlisted for an interview for the {position} position at RUDRA.

Interview Details:
📅 Date & Time: {interview_datetime}
🔗 Google Meet Link: {interview_link}
💼 Position: {position}

Interview Guidelines:
• Duration: 20-30 minutes
• Format: Technical and behavioral questions
• Please join 5 minutes early
• Ensure stable internet connection
• Keep your camera on during the interview
• Have a quiet environment ready

{additional_message}

Preparation Tips:
• Review your application responses
• Prepare examples of your relevant experience
• Think about how you can contribute to RUDRA's mission
• Be ready to discuss your technical skills and project experience

If you have any technical issues or need to reschedule, please contact us immediately at contact.rudrarvu@gmail.com.

We look forward to meeting you!

Best regards,
The RUDRA Team
Resourceful Unit for Data Research and Analytics
RV University
"""
        
        # Check if mail is configured
        if not mail:
            raise Exception("Flask-Mail not configured")
        
        mail.send(msg)
        print(f"Email sent successfully to {email}")
        return True
        
    except Exception as e:
        print(f"Error sending email to {email}: {str(e)}")
        raise e

# Add this function to test email configuration
@app.route('/admin/test_email')
def test_email():
    """Test email configuration"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Admin access required'})
    
    try:
        # Test email configuration
        test_email = session.get('user_email', 'test@rvu.edu.in')
        
        msg = Message('RUDRA Email Test', 
                      sender='contact.rudrarvu@gmail.com', 
                      recipients=[test_email])
        msg.body = "This is a test email to verify RUDRA email configuration."
        
        mail.send(msg)
        return jsonify({'success': True, 'message': f'Test email sent to {test_email}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Add debugging for Flask-Mail configuration
def check_email_config():
    """Check if email is properly configured"""
    required_config = [
        'MAIL_SERVER',
        'MAIL_PORT', 
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_USE_TLS'
    ]
    
    missing_config = []
    for config in required_config:
        if not app.config.get(config):
            missing_config.append(config)
    
    if missing_config:
        print(f"Missing email configuration: {missing_config}")
        return False
    
    print("Email configuration looks good")
    return True


# Call these functions when starting the app
if __name__ == '__main__':
    setup_applications_sheet()
    setup_admin_credentials_sheet()
    app.run(debug=True)
