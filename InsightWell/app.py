import streamlit as st
import pandas as pd
import sqlite3
from transformers import pipeline
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the emotion detection model
try:
    classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)
    logging.info("New model (SamLowe/roberta-base-go_emotions) loaded successfully.")
except Exception as e:
    logging.error(f"Error loading model: {e}")
    st.error(f"Error loading model: {e}")

# Define text classification function (make sure it's not async in Streamlit)
def classify_text(text):
    try:
        outputs = classifier(text)
        best_prediction = max(outputs[0], key=lambda x: x['score'])
        return best_prediction['label'], best_prediction['score']
    except Exception as e:
        logging.error(f"Error in classify_text: {e}")
        return "Error", 0

# Database connection
conn = sqlite3.connect('journal_entries.db', check_same_thread=False)
c = conn.cursor()

# Create table to store student entries
c.execute('''CREATE TABLE IF NOT EXISTS entries (user TEXT, role TEXT, entry TEXT, emotion TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

# Emotions that define a "feeling low" state
low_emotions = {"sadness", "grief", "fear", "anger", "nervousness"}

# Dummy user database with roles
users_db = {
    "Najlaa": {"password": "password1", "role": "student"},
    "Mohamed": {"password": "password1", "role": "student"},
    "Pedro": {"password": "password2", "role": "doctor"},
    "kilian": {"password": "password2", "role": "doctor"},

}

# Authentication function
def authenticate(username, password):
    user = users_db.get(username)
    if user and user['password'] == password:
        return user['role']
    return None

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Function to check if a student is feeling low
def check_student_alerts():
    one_week_ago = datetime.now() - timedelta(days=7)
    students = pd.read_sql_query("SELECT DISTINCT user FROM entries WHERE role = 'student'", conn)['user'].tolist()
    alerts = []

    for student in students:
        # Query entries for the student from the past week
        query = f"SELECT emotion FROM entries WHERE user = '{student}' AND timestamp >= ?"
        student_entries = pd.read_sql_query(query, conn, params=(one_week_ago,))
        
        # Count "feeling low" emotions
        low_emotion_count = student_entries['emotion'].apply(lambda x: x in low_emotions).sum()
        
        # If the count exceeds the threshold, generate an alert
        if low_emotion_count >= 3 :  # Threshold can be adjusted as needed
            alerts.append(f"Student {student} is showing signs of distress ({low_emotion_count} low emotions in the past week).")

    return alerts

# Login form
if not st.session_state.authenticated:
    st.sidebar.subheader("Login")
    username_input = st.sidebar.text_input("Username")
    password_input = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")
    
    if login_button:
        role = authenticate(username_input, password_input)
        if role:
            st.session_state.authenticated = True
            st.session_state.role = role
            st.session_state.username = username_input
            st.success(f"Welcome, {username_input}!")
        else:
            st.error("Invalid username or password")

# If authenticated, render the appropriate interface
if st.session_state.authenticated:
    # Student Interface
    if st.session_state.role == 'student':
        st.title(f"Hello, {st.session_state.username}! How are you feeling today?")
        input_text = st.text_area("Enter your thoughts here:")
        
        if st.button("Submit"):
            if input_text.strip() == "":
                st.error("Text must not be empty!")
            else:
                # Classify emotion
                emotion, score = classify_text(input_text)
                # Store the entry in the database
                c.execute("INSERT INTO entries (user, role, entry, emotion) VALUES (?, ?, ?, ?)", 
                          (st.session_state.username, 'student', input_text, emotion))
                conn.commit()
                
                # Display soothing message
                st.write(f"We understand you're feeling {emotion}. Thank you for sharing. Your doctor is here to support you.")
    
    # Doctor Interface
    elif st.session_state.role == 'doctor':
        st.title("Doctor's Dashboard")
        
        # Display alerts
        st.subheader("Student Alerts")
        alerts = check_student_alerts()
        if alerts:
            for alert in alerts:
                st.warning(alert)
        else:
            st.success("No students are currently showing signs of distress.")
        
        # General distribution of emotions
        st.subheader("Overall Emotion Distribution")
        df = pd.read_sql_query("SELECT emotion, COUNT(*) as count FROM entries GROUP BY emotion", conn)
        st.bar_chart(df.set_index('emotion'))
        
        # Specific student inquiry
        st.subheader("View Student Entries")
        students = pd.read_sql_query("SELECT DISTINCT user FROM entries WHERE role = 'student'", conn)['user'].tolist()
        selected_student = st.selectbox("Select a student to view their entries:", students)
        
        if selected_student:
            student_entries = pd.read_sql_query(f"SELECT entry, emotion, timestamp FROM entries WHERE user = '{selected_student}'", conn)
            st.write(f"Entries for {selected_student}:")
            st.table(student_entries)

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
