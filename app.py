from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import base64
import os
import cv2
import numpy as np
from fer import FER  # Import the FER library
from smtpsender import send_otp_email, send_welcome_email, send_feedback_email  # Import the email sender functions
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Set paths for storing images and songs in the 'static' directory
UPLOAD_FOLDER_IMAGES = os.path.join('static', 'images')
UPLOAD_FOLDER_SONGS = os.path.join('static', 'songs')
app.config['UPLOAD_FOLDER_IMAGES'] = UPLOAD_FOLDER_IMAGES
app.config['UPLOAD_FOLDER_SONGS'] = UPLOAD_FOLDER_SONGS

# Ensure the upload directories exist
os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_SONGS, exist_ok=True)

# Connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect('sqlit.db')
    conn.row_factory = sqlite3.Row
    return conn

# Feedback table creation
def create_feedback_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS Feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES Shopag(id)
        )
    ''')
    conn.commit()
    conn.close()

create_feedback_table()  # Create feedback table if it doesn't exist

# Update the Shopag table to add fullname and role columns if they don't exist
def update_table():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE Shopag ADD COLUMN fullname TEXT;")
    except sqlite3.OperationalError as e:
        print(f"Fullname Error: {e}")

    try:
        c.execute("ALTER TABLE Shopag ADD COLUMN role TEXT DEFAULT 'user';")
    except sqlite3.OperationalError as e:
        print(f"Role Error: {e}")

    conn.commit()
    conn.close()

# Call this function once to update the table structure if needed
update_table()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        c = conn.cursor()
        try:
            # Assign default role 'user' on registration
            c.execute("INSERT INTO Shopag (fullname, username, email, password, role) VALUES (?, ?, ?, ?, ?)",
                      (fullname, username, email, hashed_password, 'user'))
            conn.commit()
            
            # Send welcome email
            send_welcome_email(email, fullname)

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
            return render_template('auth/register.html')
        finally:
            conn.close()

    return render_template('auth/register.html')

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM Shopag WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']  # Store user role in session
            flash('Login successful!', 'success')

            # Redirect based on role
            if user['role'] == 'admin':
                return redirect(url_for('admin_index'))  # Redirect admin to admin index
            else:
                return redirect(url_for('home'))  # Redirect regular user to home
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('auth/login.html')

# Home page route
@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('index.html')

# About page route
@app.route('/about')
def about():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('about.html')

# Songs page route
@app.route('/songs')
def songs():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM Songs")
    songs = c.fetchall()
    conn.close()
    return render_template('songs.html', songs=songs)

# Settings page route
@app.route('/setting')
def setting():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('auth/setting.html')

##########################################
##########################################
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    if request.method == 'POST':
        subject = request.form['subject']
        message = request.form['message']

        user_id = session.get('user_id')  # Get user ID from the session
        if not user_id:
            flash('Error: User not found.', 'danger')
            return redirect(url_for('feedback'))

        # Save feedback in the database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO Feedback (user_id, subject, message)
            VALUES (?, ?, ?)
        ''', (user_id, subject, message))
        conn.commit()
        conn.close()

        # Send confirmation email
        send_feedback_email(session['username'], subject, message)

        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('feedback'))

    return render_template('feedback.html')

@app.route('/all_feedback')
def all_feedback():
    if 'username' not in session or session['role'] != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))  # Redirect to login if not admin

    # Fetch all feedback from the database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT Feedback.*, Shopag.fullname
        FROM Feedback
        JOIN Shopag ON Feedback.user_id = Shopag.id
    ''')
    feedbacks = c.fetchall()
    conn.close()

    return render_template('ad/feedbacks.html', feedbacks=feedbacks)
##########################################
##########################################

# Playlist page route
@app.route('/playlist', methods=['GET', 'POST'])
def playlist():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    
    emotion = request.args.get('emotion', 'unknown')  # Get the emotion from the URL parameters, default to 'unknown'

    conn = get_db_connection()
    c = conn.cursor()
    # Query to fetch songs matching the captured emotion
    c.execute("SELECT * FROM Songs WHERE mode = ? OR mode = 'unknown'", (emotion,))
    songs = c.fetchall()  # Fetch all songs that match the emotion or are 'unknown'
    conn.close()
    return render_template('playlist.html', emotion=emotion, songs=songs)  # Pass the emotion and songs to the template

# Forget password page route
@app.route('/forget')
def forget():
    return render_template('auth/forget.html')

# Route to request OTP and send via email
@app.route('/request_otp', methods=['POST'])
def request_otp():
    if 'username' not in session:
        flash('You need to be logged in to change your password.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT email FROM Shopag WHERE username = ?", (session['username'],))
    user = c.fetchone()
    conn.close()

    if user:
        otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
        session['otp'] = str(otp)  # Store OTP in session for later verification
        session['otp_verified'] = False  # Initially, OTP is not verified

        # Send the OTP to the user's email
        send_otp_email(user['email'], session['username'], otp)
        flash('OTP has been sent to your email.', 'success')
    else:
        flash('Error retrieving user information.', 'danger')

    return redirect(url_for('setting'))  # Redirect to the settings page

# Route to handle OTP verification and password update
@app.route('/change_password', methods=['POST'])
def change_password():
    if 'username' not in session:
        flash('You need to be logged in to change your password.', 'danger')
        return redirect(url_for('login'))

    otp_input = request.form['otp']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    # Validate OTP
    if otp_input != session.get('otp'):
        flash('Invalid OTP. Please try again.', 'danger')
        return redirect(url_for('setting'))

    # Check if new passwords match
    if new_password != confirm_password:
        flash('Passwords do not match!', 'danger')
        return redirect(url_for('setting'))

    # Mark OTP as verified
    session['otp_verified'] = True

    # Update password in the database
    hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE Shopag SET password = ? WHERE username = ?", (hashed_password, session['username']))
    conn.commit()
    conn.close()

    flash('Password updated successfully!', 'success')
    return redirect(url_for('setting'))

# User logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Route to capture an image and analyze emotion
@app.route('/captured', methods=['POST'])
def captured():
    image_data = request.form['image']
    image_data = image_data.split(',')[1]  # Remove the part of the string before the comma (data URL prefix)
    image_bytes = base64.b64decode(image_data)
    np_image = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
    emotion = analyze_emotion(image)
    return redirect(url_for('playlist', emotion=emotion))  # Redirect to playlist with emotion

# Route to import an image and analyze emotion
@app.route('/imported', methods=['POST'])
def imported():
    image_data = request.form['image']
    image_data = image_data.split(',')[1]  # Remove the data URL prefix
    image_bytes = base64.b64decode(image_data)
    np_image = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
    emotion = analyze_emotion(image)
    return redirect(url_for('playlist', emotion=emotion))

# Function to analyze emotion using FER
def analyze_emotion(image):
    detector = FER(mtcnn=True)
    emotion, score = 'unknown', 0.0
    try:
        result = detector.top_emotion(image)
        if result:
            emotion, score = result
    except Exception as e:
        print(f"Error in emotion detection: {e}")
    return emotion

# Song upload route
# @app.route('/upload_song', methods=['POST'])
# def upload_song():
#     title = request.form['title']
#     artist = request.form['artist']
#     genre = request.form['genre']
#     mode = request.form['mode']

#     if 'file' not in request.files:
#         flash('No file part', 'danger')
#         return redirect(request.url)

#     file = request.files['file']
#     if file.filename == '':
#         flash('No selected file', 'danger')
#         return redirect(request.url)

#     if file:
#         filename = secure_filename(file.filename)
#         file.save(os.path.join(app.config['UPLOAD_FOLDER_SONGS'], filename))

#         conn = get_db_connection()
#         c = conn.cursor()
#         c.execute("INSERT INTO Songs (title, artist, genre, mode, file_path) VALUES (?, ?, ?, ?, ?)",
#                   (title, artist, genre, mode, filename))
#         conn.commit()
#         conn.close()

#         flash('Song uploaded successfully!', 'success')
#         return redirect(url_for('songs'))




# Admin index page route
@app.route('/admin')
def admin_index():
    if 'username' not in session or session['role'] != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))  # Redirect to home if not admin
    return render_template('ad/index.html')  # Admin dashboard


# Route to upload songs
@app.route('/upload_song', methods=['GET', 'POST'])
def upload_song():

    if 'username' not in session or session['role'] != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))  # Redirect to home if not admin
    
    if request.method == 'POST':
        title = request.form['title']
        artist = request.form['artist']
        mode = request.form.get('mode', 'unknown')  # Default mode is 'unknown'

        # Handle image (album cover) upload
        image_file = request.files['image']
        image_filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], image_filename)
        image_file.save(image_path)

        # Handle song file upload
        song_file = request.files['song']
        song_filename = secure_filename(song_file.filename)
        song_path = os.path.join(app.config['UPLOAD_FOLDER_SONGS'], song_filename)
        song_file.save(song_path)

        # Save song metadata to the database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO Songs (image, title, artist, song, mode)
            VALUES (?, ?, ?, ?, ?)
        ''', (image_filename, title, artist, song_filename, mode))
        conn.commit()
        conn.close()

        flash('Song uploaded successfully!', 'success')
        return redirect(url_for('upload_song'))

    return render_template('ad/add_song.html')


@app.route('/all_songs')
def all_songs():
    if 'username' not in session or session['role'] != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))  # Redirect to home if not admin

    # Fetch all songs from the database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM Songs")  # Fetch all songs from the Songs table
    songs = c.fetchall()
    conn.close()

    # Pass songs to the template
    return render_template('ad/all_song.html', songs=songs)


@app.route('/ad_setting')
def ad_setting():
    if 'username' not in session or session['role'] != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))  # Redirect to home if not admin
    
    return render_template('ad/ad_setting.html')


@app.route('/edit-song/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    if 'username' not in session or session['role'] != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))  # Redirect to home if not admin

    conn = get_db_connection()

    if request.method == 'POST':
        # Get the updated song information from the form
        title = request.form['title']
        artist = request.form['artist']
        mode = request.form.get('mode', 'unknown')  # Default mode is 'unknown'
        image_file = request.files.get('image')
        
        # Check if an image file was uploaded
        if image_file:
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], image_filename)
            image_file.save(image_path)
        else:
            # Fetch existing image filename if no new file was uploaded
            song = conn.execute("SELECT * FROM Songs WHERE id = ?", (song_id,)).fetchone()
            image_filename = song['image']

        # Update the song in the database
        conn.execute('''
            UPDATE Songs
            SET title = ?, artist = ?, image = ?, mode = ?
            WHERE id = ?
        ''', (title, artist, image_filename, mode, song_id))
        conn.commit()
        conn.close()

        flash('Song updated successfully!', 'success')
        return redirect(url_for('all_songs'))

    # If GET request, fetch existing song data to populate the form
    song = conn.execute("SELECT * FROM Songs WHERE id = ?", (song_id,)).fetchone()
    conn.close()
    return render_template('ad/edit_song.html', song=song)


@app.route('/delete-song/<int:song_id>', methods=['POST'])
def delete_song(song_id):
    if 'username' not in session or session['role'] != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))  # Redirect to home if not admin

    conn = get_db_connection()
    conn.execute("DELETE FROM Songs WHERE id = ?", (song_id,))
    conn.commit()
    conn.close()

    flash('Song deleted successfully!', 'success')
    return redirect(url_for('all_songs'))

@app.route('/all_user')
def all_user():
    if 'username' not in session or session['role'] != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))  # Redirect to home if not admin

    # Fetch all users from the database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM Shopag WHERE role = 'user'")  # Fetch all users from the Shopag table
    users = c.fetchall()
    conn.close()

    # Pass users to the template
    return render_template('ad/all_user.html', users=users)

@app.route('/emailtemp')
def temp():
    return render_template("email_template.html")


# Run the app
if __name__ == '__main__':
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16 MB
    app.run(host="0.0.0.0", debug=True)
