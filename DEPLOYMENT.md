# Streamlit Cloud Deployment Guide

## Prerequisites
1. GitHub account
2. Streamlit Cloud account (free at https://streamlit.io/cloud)
3. Supabase project setup and credentials

## Deployment Steps

### 1. Push to GitHub

```bash
cd /Users/rghimire6/Documents/AI_Cool_Projects/FifaWorldCupBracket

# Add all files
git add .

# Commit
git commit -m "Initial commit - FIFA World Cup 2026 Bracket Challenge"

# Create a new repository on GitHub (https://github.com/new)
# Then connect and push:
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Connect your GitHub account if not already connected
4. Select:
   - **Repository**: YOUR_USERNAME/YOUR_REPO_NAME
   - **Branch**: main
   - **Main file path**: app.py
5. Click "Advanced settings"
6. Add **Secrets** (copy from your .env file):

```toml
SUPABASE_URL = "your-actual-supabase-url"
SUPABASE_KEY = "your-actual-supabase-anon-key"
ADMIN_PASSWORD = "your-actual-admin-password"
```

7. Click "Deploy!"

### 3. Access Your App

Once deployed, you'll get a URL like:
- `https://YOUR_APP_NAME.streamlit.app`

**Admin Access:**
- `https://YOUR_APP_NAME.streamlit.app?page=admin`

### 4. Configure Supabase

Make sure your Supabase tables are set up:

1. Run the SQL from `supabase_schema.sql` in Supabase SQL Editor
2. Verify Row Level Security (RLS) is configured appropriately
3. Test the connection from deployed app

### 5. Important Notes

- **Secrets Management**: Secrets are configured in Streamlit Cloud dashboard, NOT in code
- **Database**: Make sure Supabase is accessible from internet (not localhost)
- **Session Persistence**: Uses URL query parameters, works across refreshes
- **Admin Password**: Set a strong password in secrets

### 6. Post-Deployment

- Test user registration and login
- Test bracket selection and saving
- Test admin access with `?page=admin`
- Verify deadline lock functionality (currently set to July 4, 2026 12:00 PM EST)

### 7. Updating the App

To update after deployment:

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

Streamlit Cloud will automatically rebuild and redeploy within a few minutes.

## Troubleshooting

### App won't start
- Check logs in Streamlit Cloud dashboard
- Verify all secrets are set correctly
- Ensure requirements.txt has all dependencies

### Database connection errors
- Verify SUPABASE_URL and SUPABASE_KEY in secrets
- Check Supabase project is active
- Verify tables exist and are accessible

### Session not persisting
- Clear browser cache and cookies
- Check that query parameters are in URL
- Verify timestamps are being updated

## Features

✅ User authentication (email-based, no password)
✅ Bracket selection with visual tournament tree
✅ Team advancement with connector lines
✅ Session persistence (15-minute timeout)
✅ Admin dashboard (hidden, accessible via URL)
✅ Deadline lock (July 4, 2026 12:00 PM EST)
✅ Final score prediction
✅ Real-time bracket saving

## Support

For issues or questions:
- Check Streamlit Cloud logs
- Review Supabase logs
- Verify environment variables/secrets
