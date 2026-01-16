# Supabase Setup Instructions

## 1. Project Information

- **Project URL**: `https://tzcdzyqhadczxsvvfdhg.supabase.co`
- **Publishable API Key**: `sb_publishable_mBHUGJABWYTE4PahfMcmSA_MOUETx-I`

## 2. Database Setup

1. Go to your Supabase project: https://supabase.com/dashboard/project/tzcdzyqhadczxsvvfdhg
2. Navigate to **SQL Editor**
3. Create a new query
4. Copy and paste the entire contents of `supabase_schema.sql`
5. Click **Run** to execute the SQL

This will create:
- `jobs` table - for tracking processing jobs
- `school_results` table - for storing school enrichment results
- `person_leads` table - for storing person-centric leads
- Indexes for performance
- Row Level Security (RLS) policies

## 3. Get Service Role Key (for Backend)

1. Go to **Settings** → **API**
2. Find **service_role** key (secret key)
3. Copy it - this is needed for the backend to bypass RLS

## 4. Environment Variables

### Backend (.env)
```env
SUPABASE_URL=https://tzcdzyqhadczxsvvfdhg.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=https://tzcdzyqhadczxsvvfdhg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_mBHUGJABWYTE4PahfMcmSA_MOUETx-I
```

## 5. Verify Setup

After running the SQL schema, verify tables were created:
1. Go to **Table Editor**
2. You should see: `jobs`, `school_results`, `person_leads`

## 6. RLS Policies

The schema includes RLS policies that:
- Allow users to see their own jobs (if authenticated)
- Allow public read access (for demo - you can restrict this later)

To restrict access:
1. Go to **Authentication** → **Policies**
2. Modify policies as needed

## Notes

- **Publishable Key** (anon key) is safe for frontend use with RLS enabled
- **Service Role Key** should ONLY be used in backend/server code
- Never commit service role keys to Git

