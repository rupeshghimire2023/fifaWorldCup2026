-- Create users table
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create brackets table
CREATE TABLE brackets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    selections JSONB NOT NULL,
    champion TEXT,
    final_score JSONB DEFAULT '{"home": "", "away": ""}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_brackets_user_id ON brackets(user_id);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE brackets ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Users can read their own data" ON users
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own data" ON users
    FOR INSERT WITH CHECK (true);

-- Create policies for brackets table
CREATE POLICY "Users can read all brackets" ON brackets
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own brackets" ON brackets
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their own brackets" ON brackets
    FOR UPDATE USING (true);

-- If you already have the brackets table, run this to add the final_score column:
-- ALTER TABLE brackets ADD COLUMN IF NOT EXISTS final_score JSONB DEFAULT '{"home": "", "away": ""}'::jsonb;
