-- Supabase schema for Indonesia EdTech Lead Gen Engine

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id),
  input_format TEXT NOT NULL,
  schools_count INTEGER NOT NULL,
  processed_count INTEGER DEFAULT 0,
  successful_count INTEGER DEFAULT 0,
  failed_count INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  error_message TEXT
);

-- School results
CREATE TABLE IF NOT EXISTS school_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  school_name TEXT NOT NULL,
  school_type TEXT,
  location TEXT,
  npsn TEXT,
  foundation_name TEXT,
  official_website TEXT,
  official_email TEXT,
  whatsapp_business TEXT,
  data_quality_score FLOAT DEFAULT 0,
  decision_makers JSONB DEFAULT '[]'::jsonb,
  tech_stack TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMP DEFAULT NOW()
);

-- Person leads
CREATE TABLE IF NOT EXISTS person_leads (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  school_name TEXT NOT NULL,
  person_name TEXT NOT NULL,
  role TEXT,
  role_indonesian TEXT,
  priority_tier INTEGER DEFAULT 5,
  direct_whatsapp TEXT,
  whatsapp_verified BOOLEAN DEFAULT FALSE,
  direct_email TEXT,
  email_verified BOOLEAN DEFAULT FALSE,
  email_is_personal BOOLEAN DEFAULT FALSE,
  linkedin TEXT,
  tech_stack TEXT,
  source_url TEXT,
  confidence FLOAT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_school_results_job_id ON school_results(job_id);
CREATE INDEX IF NOT EXISTS idx_person_leads_job_id ON person_leads(job_id);
CREATE INDEX IF NOT EXISTS idx_person_leads_school_name ON person_leads(school_name);

-- Row Level Security (RLS)
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE person_leads ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only see their own jobs)
CREATE POLICY "Users can view their own jobs"
  ON jobs FOR SELECT
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can view their own school results"
  ON school_results FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM jobs
      WHERE jobs.id = school_results.job_id
      AND (jobs.user_id = auth.uid() OR jobs.user_id IS NULL)
    )
  );

CREATE POLICY "Users can view their own person leads"
  ON person_leads FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM jobs
      WHERE jobs.id = person_leads.job_id
      AND (jobs.user_id = auth.uid() OR jobs.user_id IS NULL)
    )
  );

-- For public access (demo mode), you can use:
-- CREATE POLICY "Public read access" ON jobs FOR SELECT USING (true);
-- CREATE POLICY "Public read access" ON school_results FOR SELECT USING (true);
-- CREATE POLICY "Public read access" ON person_leads FOR SELECT USING (true);

