# 📬 AI-Powered Email Assistant

An intelligent email assistant built with Streamlit and Gemini AI that helps you:
- 🔐 Log in using Gmail and App Password
- 📂 Fetch and classify up to 50 recent emails into predefined categories
- 🧠 Summarize email content using Google's Gemini model
- 🤖 Auto-generate professional replies
- 📤 Send replies directly from the app
- 🗃️ Organize your inbox visually using expandable category sections

---

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-email-assistant.git
   cd ai-email-assistant

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt

3. **Set up Gemini API Key**
   Replace "GEMINI_API_KEY" in the code with your actual Gemini API key.

4. **Run the app**
   ```bash
   streamlit run app.py

## 🔐 Gmail Setup (App Password)

**To use this app, you need to enable 2-step verification and generate an App Password for Gmail:**

1. Go to Google Account > Security

2. Enable 2-Step Verification

3. Generate an App Password

4. Use this App Password in the login form