import streamlit as st
import pandas as pd
import sqlite3
import logging
from datetime import datetime, timedelta
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the backend API URL
BACKEND_URL = "http://localhost:8000"  # Ensure this matches your actual backend address

# Database connection
conn = sqlite3.connect('journal_entries.db', check_same_thread=False)
c = conn.cursor()

# Create table to store student entries
c.execute('''CREATE TABLE IF NOT EXISTS entries (
    user TEXT, 
    role TEXT, 
    entry TEXT, 
    emotion TEXT, 
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)''')
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
    students = pd.read_sql_query(
        "SELECT DISTINCT user FROM entries WHERE role = 'student'", conn
    )['user'].tolist()
    alerts = []

    for student in students:
        # Query entries for the student from the past week
        query = "SELECT emotion FROM entries WHERE user = ? AND timestamp >= ?"
        student_entries = pd.read_sql_query(query, conn, params=(student, one_week_ago))
        
        # Count "feeling low" emotions
        low_emotion_count = student_entries['emotion'].apply(lambda x: x in low_emotions).sum()
        
        # If the count exceeds the threshold, generate an alert
        if low_emotion_count >= 3:  # Threshold can be adjusted as needed
            alerts.append(f"Student {student} is showing signs of distress ({low_emotion_count} low emotions in the past week).")

    return alerts

# Function to classify text by calling the backend API
def classify_text_api(text):
    try:
        response = requests.post(f"{BACKEND_URL}/classify", json={"text": text})
        if response.status_code == 200:
            data = response.json()  # Ensure the response is parsed as JSON
            return data.get('label', 'Error'), data.get('score', 0)
        elif response.status_code == 422:
            data = response.json()
            error_messages = data.get('detail', [])
            # Join multiple error messages into one string
            error_message = " ".join(error_messages)
            return "ValidationError", error_message
        else:
            logging.error(f"Error in classify_text_api: {response.status_code} - {response.text}")
            return "Error", f"Error {response.status_code}: {response.text}"
    except Exception as e:
        logging.error(f"Exception in classify_text_api: {e}")
        return "Error", f"Exception occurred: {e}"

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
                # Classify emotion by calling the backend API
                emotion, message = classify_text_api(input_text)
                if emotion == "ValidationError":
                    st.error(message)
                elif emotion == "Error":
                    st.error(f"An error occurred: {message}")
                else:
                    # Store the entry in the database
                    c.execute(
                        "INSERT INTO entries (user, role, entry, emotion) VALUES (?, ?, ?, ?)", 
                        (st.session_state.username, 'student', input_text, emotion)
                    )
                    conn.commit()
                    
                    # Display soothing message
                    st.write(f"We understand you're feeling {emotion}. Thank you for sharing, we're here to support you through it all!")
        
        # **New Feature: Display Student's Emotion History**
        st.subheader("Your Emotion History")
        # Fetch the student's entries
        query = "SELECT entry, emotion, timestamp FROM entries WHERE user = ? ORDER BY timestamp DESC"
        student_entries = pd.read_sql_query(query, conn, params=(st.session_state.username,))
        if not student_entries.empty:
            # Display entries in a table
            st.table(student_entries)
        else:
            st.info("You have no previous entries.")

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
        df = pd.read_sql_query(
            "SELECT emotion, COUNT(*) as count FROM entries GROUP BY emotion", conn
        )
        st.bar_chart(df.set_index('emotion'))
        
        # Specific student inquiry
        st.subheader("View Student Entries")
        students = pd.read_sql_query(
            "SELECT DISTINCT user FROM entries WHERE role = 'student'", conn
        )['user'].tolist()
        selected_student = st.selectbox("Select a student to view their entries:", students)
        
        if selected_student:
            query = "SELECT entry, emotion, timestamp FROM entries WHERE user = ?"
            student_entries = pd.read_sql_query(query, conn, params=(selected_student,))
            st.write(f"Entries for {selected_student}:")
            st.table(student_entries)

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None