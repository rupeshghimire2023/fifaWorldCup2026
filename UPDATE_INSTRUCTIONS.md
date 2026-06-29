# Database Update Required

Since we added a new feature (final score input), you need to update your Supabase database:

## Steps:

1. Go to your Supabase project: https://supabase.com/dashboard
2. Click on **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy and paste this SQL command:

```sql
ALTER TABLE brackets ADD COLUMN IF NOT EXISTS final_score JSONB DEFAULT '{"home": "", "away": ""}'::jsonb;
```

5. Click **Run** or press `Ctrl+Enter`

That's it! Your database is now ready to store final match scores.

## New Features Added:

✅ March Madness style bracket layout (horizontal flow)
✅ Country flags for all teams
✅ Final match score input (home and away)
✅ Better visual spacing between rounds
✅ Improved color scheme with gradient backgrounds
✅ Champion display with flag

Refresh your Streamlit app to see the new bracket design!
