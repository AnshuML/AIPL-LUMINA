# 🚀 Streamlit Cloud Deployment Guide

## Prerequisites
1. GitHub account
2. Streamlit Cloud account (free at share.streamlit.io)
3. OpenAI API key

## Step-by-Step Deployment

### 1. Prepare Your Repository
- Push your code to GitHub
- Ensure all files are committed

### 2. Deploy on Streamlit Cloud

1. **Go to Streamlit Cloud**: Visit https://share.streamlit.io
2. **Sign in** with your GitHub account
3. **Click "New app"**
4. **Fill in the details**:
   - **Repository**: `your-username/baatchitt`
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `hr-chatbot/streamlit_app.py`
   - **App URL**: Choose a custom URL (optional)

### 3. Configure Environment Variables

In the Streamlit Cloud dashboard, add these secrets:

```
OPENAI_API_KEY = your-actual-openai-api-key
SECRET_KEY = your-secret-key-for-jwt-tokens
```

### 4. Advanced Settings (Optional)

- **Python version**: 3.9 or 3.10
- **Memory**: 1GB (default should work)
- **Timeout**: 300 seconds

### 5. Deploy

Click "Deploy!" and wait for the build to complete.

## Important Notes

### File Structure
```
hr-chatbot/
├── streamlit_app.py          # Main entry point
├── app.py                    # Your main app
├── requirements.txt          # Dependencies
├── .streamlit/
│   └── config.toml          # Streamlit config
├── env.example              # Environment template
└── ... (other files)
```

### Environment Variables Required
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: Random string for JWT tokens

### Database
- The app uses SQLite by default
- Data will persist between deployments
- For production, consider upgrading to PostgreSQL

### Troubleshooting

**Common Issues:**
1. **Import errors**: Check that all dependencies are in requirements.txt
2. **API key issues**: Verify environment variables are set correctly
3. **Memory issues**: Upgrade to higher memory tier if needed
4. **Timeout errors**: Optimize your RAG pipeline for faster responses

**Logs:**
- Check the logs in Streamlit Cloud dashboard
- Look for error messages in the terminal output

### Post-Deployment

1. **Test the app**: Verify all features work
2. **Monitor usage**: Check Streamlit Cloud analytics
3. **Update regularly**: Push changes to trigger redeployment

## Security Considerations

- Never commit API keys to GitHub
- Use environment variables for sensitive data
- Regularly rotate your SECRET_KEY
- Consider implementing rate limiting for production

## Support

If you encounter issues:
1. Check the Streamlit Cloud documentation
2. Review the logs in your dashboard
3. Test locally first with `streamlit run streamlit_app.py`
