import streamlit as st
from email_classifier import (
    fetch_and_classify_emails,
    CATEGORY_PRIORITY
)
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText

# Configure Gemini API key
genai.configure(api_key="GEMINI_API_KEY")  # Replace with your Gemini API key

# Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

# Set Streamlit page config
st.set_page_config(page_title="AI-Powered Email Assistant", layout="wide")
st.markdown("<h1>📬 Welcome to the AI Email Assistant</h1>", unsafe_allow_html=True)
#st.markdown('<div class="main-title">📬 AI-Powered Email Assistant</div>', unsafe_allow_html=True)

# Initialize all session state variables at the beginning
if 'classified_emails' not in st.session_state:
    st.session_state.classified_emails = None
if 'generated_replies' not in st.session_state:
    st.session_state.generated_replies = {}
if 'user_credentials' not in st.session_state:
    st.session_state.user_credentials = {'email': '', 'password': ''}

# Sidebar for credentials
with st.sidebar:
    st.header("🔐 Email Credentials")
    # Use different keys for widgets than session state
    email_input = st.text_input("Gmail Address", 
                              placeholder="example@gmail.com", 
                              key="email_input")
    password_input = st.text_input("App Password", 
                                 type="password", 
                                 placeholder="App-specific password", 
                                 key="password_input")
    
    if st.button("Fetch Today's Emails"):
        if email_input and password_input:
            with st.spinner("Fetching and classifying up to 50 emails..."):
                try:
                    classified_emails = fetch_and_classify_emails(email_input, password_input)
                    st.session_state.classified_emails = classified_emails
                    st.session_state.user_credentials = {
                        'email': email_input,
                        'password': password_input
                    }
                    st.success("Emails fetched successfully!")
                except Exception as e:
                    st.error(f"Error fetching emails: {str(e)}")
        else:
            st.warning("Please enter both your email and app password.")

# Function to summarize with Gemini
@st.cache_data(show_spinner=False)
def summarize_with_gemini(text):
    try:
        prompt = f"Summarize this email in 1-2 sentences:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "⚠️ Could not generate summary."

# Function to generate reply with Gemini
def generate_reply(email_body, sender_name, email_subject):
    try:
        prompt = f"""Compose a professional email reply to this message. Be concise (2-3 sentences max). 
        The original email was from {sender_name} with subject '{email_subject}'.
        
        Original email content:
        {email_body}
        
        Suggested reply:"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Could not generate reply. Error: {str(e)}"

# Function to send email
def send_email(reply_content, recipient, subject):
    try:
        msg = MIMEText(reply_content)
        msg['Subject'] = f"Re: {subject}"
        msg['From'] = st.session_state.user_credentials['email']
        msg['To'] = recipient
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(
                st.session_state.user_credentials['email'],
                st.session_state.user_credentials['password']
            )
            smtp_server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

# Show emails (without body) + Gemini summary
if st.session_state.classified_emails:
    st.subheader("📥 Classified Emails")
    for category in CATEGORY_PRIORITY:
        emails = st.session_state.classified_emails.get(category, [])
        if emails:
            with st.expander(f"📂 {category} ({len(emails)} email{'s' if len(emails) != 1 else ''})", expanded=False):
                for idx, email_data in enumerate(emails):
                    email_key = f"{category}_{idx}"
                    with st.container():
                        st.markdown('<div class="email-card">', unsafe_allow_html=True)
                        st.markdown(f"**✉️ Subject:** {email_data['subject']}")
                        st.markdown(f"**From:** {email_data['from']}")
                        st.markdown(f"**Date:** {email_data['date']} | **Time:** {email_data['time']}")
                        st.markdown("---")
                        summary = summarize_with_gemini(email_data['body'])
                        st.markdown(f"✅ **Summary:** {summary}")
                        
                        # Generate reply section
                        if email_key not in st.session_state.generated_replies:
                            st.session_state.generated_replies[email_key] = None
                        
                        if st.button(f"Generate Reply", key=f"generate_{email_key}"):
                            with st.spinner("Generating reply..."):
                                reply = generate_reply(
                                    email_data['body'],
                                    email_data['from'],
                                    email_data['subject']
                                )
                                st.session_state.generated_replies[email_key] = reply
                                st.rerun()
                        
                        if st.session_state.generated_replies[email_key]:
                            st.markdown("---")
                            st.markdown("**Generated Reply:**")
                            st.write(st.session_state.generated_replies[email_key])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(f"📤 Send Reply", key=f"send_{email_key}"):
                                    if send_email(
                                        st.session_state.generated_replies[email_key],
                                        email_data['from'],
                                        email_data['subject']
                                    ):
                                        st.success("Reply sent successfully!")
                                        st.session_state.generated_replies[email_key] = None
                                        st.rerun()
                            with col2:
                                if st.button(f"🗑️ Discard Reply", key=f"discard_{email_key}"):
                                    st.session_state.generated_replies[email_key] = None
                                    st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)
