import imaplib
import email
import datetime
from email.header import decode_header
from bs4 import BeautifulSoup
from dateparser import parse as parse_date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Define keywords for classification
CATEGORY_KEYWORDS = {
    "Work/Business": ["meeting", "project", "deadline", "work", "business"],
    "Education & Learning": ["course", "lecture", "exam", "class"],
    "Finance & Banking": ["bank", "transaction", "payment", "loan"],
    "Legal & Government": ["law", "policy", "govt", "compliance"],
    "E-commerce & Orders": ["order", "invoice", "shipment", "delivery"],
    "Healthcare & Medical": ["doctor", "appointment", "prescription", "medicine"],
    "Technical Support": ["bug", "issue", "support", "ticket"],
    "Travel & Hospitality": ["flight", "hotel", "booking"],
    "Newsletters & Subscriptions": ["newsletter", "subscribe", "subscription"],
    "Social Media Notifications": ["Facebook", "Twitter", "Instagram"],
    "Personal": ["family", "friends", "birthday"],
    "Promotions": ["sale", "offer", "discount", "deal"]
}

CATEGORY_PRIORITY = list(CATEGORY_KEYWORDS.keys()) + ["Uncategorized", "Spam"]

# Get today's date in required format
def get_today_date():
    return datetime.datetime.now().strftime("%d-%b-%Y")

# Extract body content from email
def extract_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                return part.get_payload(decode=True).decode(errors="ignore")
            elif content_type == "text/html" and "attachment" not in content_disposition:
                html = part.get_payload(decode=True).decode(errors="ignore")
                return BeautifulSoup(html, "html.parser").text
    else:
        return msg.get_payload(decode=True).decode(errors="ignore")
    return ""

# Classify email by subject + body
def classify_email(subject, body):
    combined = f"{subject} {body}".lower()
    for category in CATEGORY_KEYWORDS:
        for keyword in CATEGORY_KEYWORDS[category]:
            if keyword.lower() in combined:
                return category
    return "Uncategorized"

# Summarize emails for each category
def summarize_emails(classified_emails):
    summaries = {}
    for category in CATEGORY_PRIORITY:
        emails = classified_emails.get(category, [])
        if not emails:
            summaries[category] = "No emails in this category."
            continue

        valid_emails = [e for e in emails if isinstance(e, dict) and 'subject' in e]
        if not valid_emails:
            summaries[category] = "No valid email data available."
            continue

        summary = "\n".join([f"• {e['subject']}" for e in valid_emails[:3]])
        if len(valid_emails) > 3:
            summary += f"\n• ...and {len(valid_emails) - 3} more emails."
        summaries[category] = summary or "No summary available."
    
    return summaries

# Main function to fetch, parse, classify emails
def fetch_and_classify_emails(email_id, password):
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        imap.login(email_id, password)
    except imaplib.IMAP4.error:
        print("❌ Login failed. Please check your email or password.")
        return {}

    imap.select("inbox")
    status, messages = imap.search(None, "ALL")  # Fetch all emails regardless of read status or date
    email_ids = messages[0].split()[-50:]        # Get the latest 50 emails

    classified = {cat: [] for cat in CATEGORY_PRIORITY}

    for eid in email_ids:
        res, msg_data = imap.fetch(eid, "(RFC822)")
        raw = email.message_from_bytes(msg_data[0][1])

        subject_raw = raw["Subject"]
        if subject_raw:
            decoded = decode_header(subject_raw)[0]
            try:
                subject = decoded[0].decode(decoded[1]) if isinstance(decoded[0], bytes) else decoded[0]
            except (TypeError, LookupError) as e:
                subject = "Failed to decode subject"
        else:
            subject = "No Subject"

        sender = raw.get("From", "Unknown Sender")
        body = extract_body(raw)

        raw_date = raw.get("Date", "")
        parsed_date = parse_date(raw_date)

        if parsed_date:
            email_date = parsed_date.strftime("%Y-%m-%d")
            email_time = parsed_date.strftime("%H:%M:%S")
        else:
            email_date = "Unknown Date"
            email_time = "Unknown Time"

        category = classify_email(subject, body)

        classified[category].append({
            "subject": subject,
            "from": sender,
            "body": body,
            "date": email_date,
            "time": email_time
        })

    imap.logout()
    return classified

# Function to send auto-reply 
def send_auto_reply(user_email, password, to_email, message_body):
    try:
        msg = MIMEMultipart()
        msg['From'] = user_email
        msg['To'] = to_email
        msg['Subject'] = "Re: Your Email"

        msg.attach(MIMEText(message_body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user_email, password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Auto-reply sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send auto-reply to {to_email}: {e}")
