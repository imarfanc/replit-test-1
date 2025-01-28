-- Create launcher_apps table
CREATE TABLE launcher_apps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    category TEXT DEFAULT 'uncategorized',
    icon_url TEXT,
    app_store_link TEXT,
    launch_count INTEGER DEFAULT 0,
    last_modified TIMESTAMPTZ DEFAULT NOW(),
    last_launched TIMESTAMPTZ
);

-- Create launcher_settings table
CREATE TABLE launcher_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metadata JSONB NOT NULL,
    settings JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create launcher_categories table
CREATE TABLE launcher_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger for launcher_settings
CREATE TRIGGER update_launcher_settings_updated_at
    BEFORE UPDATE ON launcher_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 