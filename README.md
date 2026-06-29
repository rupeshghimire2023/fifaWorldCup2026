# FIFA World Cup 2026 Bracket Challenge

An interactive bracket challenge app for FIFA World Cup 2026 knockout stages built with Streamlit and Supabase.

## Features

- User authentication (sign up and login)
- Interactive bracket selection
- Automatic bracket progression based on selections
- Selection deadline: July 4, 2026 at 12:00 PM EST
- Admin dashboard to view all submissions
- Supabase backend for data storage
- One account per email (prevents duplicate signups)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Supabase Setup

1. Go to https://supabase.com/ and create a new account
2. Create a new project
3. Go to **Project Settings** > **API**
4. Copy your **Project URL** and **anon/public key**
5. Go to **SQL Editor** in the left sidebar
6. Copy the contents of `supabase_schema.sql` and run it to create the database tables

### 3. Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your values:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_anon_key_here
   ADMIN_PASSWORD=your_secure_admin_password
   ```

### 4. Run the App

```bash
streamlit run app.py
```

## Usage

### For Users

1. **Sign Up**: Create an account with your name and email
2. **Login**: Login with your email
3. **Make Selections**: 
   - Select winners for each match in the Round of 32
   - Winners automatically progress to next rounds
   - Continue selecting through Round of 16, Quarter Finals, Semi Finals, and Final
4. **Save**: Click "Save Bracket" to save your selections
5. **Modify**: You can change your selections until July 4, 2026 at 12:00 PM EST

### For Admin

1. Go to the "Admin" tab on login page
2. Enter admin password
3. View all user submissions and their bracket selections

## Project Structure

```
├── app.py                  # Main Streamlit application
├── supabase_config.py      # Supabase configuration and database operations
├── bracket_logic.py        # Bracket logic and validation
├── bracket_data.json       # Tournament bracket data
├── supabase_schema.sql     # Database schema for Supabase
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .env.example           # Example environment variables
├── .gitignore             # Git ignore file
└── README.md              # This file
```

## Database Structure

### Tables

**users**
```sql
id: UUID (primary key)
email: TEXT (unique)
name: TEXT
created_at: TIMESTAMPTZ
```

**brackets**
```sql
id: UUID (primary key)
user_id: UUID (foreign key to users)
selections: JSONB
champion: TEXT
updated_at: TIMESTAMPTZ
```

### Example Data

**brackets.selections** (JSONB):
```json
{
  "73": "Canada",
  "74": "Germany",
  "75": "Netherlands",
  ...
}
```

## Notes

- Users can only sign up once per email
- Selections are locked after July 4, 2026 at 12:00 PM EST
- All times are in Eastern Standard Time (EST)
- Admin password should be kept secure
- Supabase free tier includes 500MB database and 2GB file storage
