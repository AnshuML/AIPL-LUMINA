# 🚀 Streamlit Cloud Deployment Guide

## AIPL Lumina HR Chatbot - Cloud Deployment

### 📋 Prerequisites
1. **GitHub Repository** - Push your code to GitHub
2. **Streamlit Cloud Account** - Sign up at share.streamlit.io
3. **OpenAI API Key** - Get from platform.openai.com

### 🔧 Deployment Steps

#### 1. Push to GitHub
```bash
git add .
git commit -m "AIPL Lumina HR Chatbot - Ready for deployment"
git push origin main
```

#### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub repository
4. Set the following:
   - **Repository:** `your-username/your-repo-name`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
   - **App URL:** `aipl-lumina-hr-chatbot` (or your preferred name)

#### 3. Configure Secrets
In Streamlit Cloud dashboard, go to "Settings" → "Secrets" and add:
```toml
OPENAI_API_KEY = "your_openai_api_key_here"
```

#### 4. Deploy
Click "Deploy!" and wait for the deployment to complete.

### 🌐 Access Your App
Your app will be available at:
`https://aipl-lumina-hr-chatbot.streamlit.app`

### ✨ Features
- **Simple Login** - Company email validation (@aiplabro.com, @ajitindustries.com)
- **User Name** - Full name input
- **One-Click Login** - Direct access to chatbot
- **Dark Theme** - Professional interface
- **File-Based System** - No database required
- **Complete Logging** - User activity tracking

### 🔒 Security
- **Company Email Validation** - Only allows company domains
- **Session Management** - Secure user sessions
- **Activity Logging** - Complete user tracking

### 📊 Admin Panel
For admin access, run locally:
```bash
python simple_launcher.py admin
```
Access: http://localhost:8502

### 🛠️ Troubleshooting
- **App not loading?** Check if all files are pushed to GitHub
- **API errors?** Verify OpenAI API key in secrets
- **Login issues?** Check email domain validation

### 📱 User Experience
1. **Open App** - User visits the URL
2. **Enter Email** - Company email (@aiplabro.com or @ajitindustries.com)
3. **Enter Name** - Full name
4. **Click Login** - One-click access
5. **Start Chatting** - Ask questions about company policies

---

**Ready for deployment! Your AIPL Lumina HR Chatbot will work perfectly on Streamlit Cloud!** 🎉
