# 🇮🇩 Indonesia EdTech Lead Gen Engine

**Full-stack automated lead enrichment tool for the Indonesian private school market.**

Find Decision Makers (Yayasan Chairmen, School Directors, Principals) and their verified contact details (WhatsApp/Email) from Indonesian schools.

## 🚀 Features

- ✅ **Contact Validation** - Verify WhatsApp numbers and email addresses
- 🔍 **Smart Search** - Targeted Google searches via Serper API + DAPODIK portal
- 🌐 **Web Scraping** - Crawl4AI optimized for LLM processing + Google Maps integration
- 🤖 **AI Extraction** - Claude 3.5 Sonnet or GPT-4o-mini with persona-focused prompts
- 📊 **Indonesian Optimized** - Understands "Ketua Yayasan", "Operator Sekolah", "Nomor HP", etc.
- 💬 **WhatsApp Priority** - Extracts wa.me links and +62 numbers with verification
- 📁 **Multi-format Export** - CSV, Excel, JSON output
- 🎨 **Modern UI** - Next.js frontend with shadcn/ui (dark theme, violet color)
- 📦 **Supabase Integration** - History tracking and data persistence

## 🏗️ Architecture

```
schoolcontacts/
├── api/                    # FastAPI backend
│   ├── main.py            # FastAPI app
│   ├── routes/            # API endpoints
│   ├── services/          # Business logic
│   └── database/          # Supabase client
├── frontend/              # Next.js frontend
│   ├── app/               # Pages
│   ├── components/        # React components
│   └── lib/               # Utilities
├── validator.py           # Contact validation
├── models.py              # Data models
├── search.py              # Search logic
├── scraper.py             # Web scraping
├── extractor.py           # LLM extraction
└── main.py                # CLI orchestrator
```

## 📦 Setup

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure environment
cp env.example .env
# Edit .env with your API keys
```

### Frontend

```bash
cd frontend
npm install
```

### Supabase

1. Create a Supabase project at https://supabase.com
2. Run `supabase_schema.sql` in your Supabase SQL editor
3. Add `SUPABASE_URL` and `SUPABASE_KEY` to `.env`

## 🔑 Required API Keys

| Service | Purpose | Get it at |
|---------|---------|-----------|
| Serper.dev | Google Search | https://serper.dev (2500 free) |
| OpenRouter | LLM Access | https://openrouter.ai |
| Supabase | Database | https://supabase.com (free tier) |

## 🚀 Running

### Backend API

```bash
cd api
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm run dev
```

### CLI (Original)

```bash
# Process priority schools
python main.py

# Process all schools
python main.py --all
```

## 📝 Input Formats

The system supports multiple input formats:

### Text Format
```
PPPK Petra - Private Christian (Elementary to High School, Education Board/Group)
Yohanes Gabriel Foundation - Private Catholic (Elementary to High School, Religious Foundation)
```

### CSV
```csv
name,type,location
PPPK Petra,Private Christian,Surabaya
```

### JSON
```json
[
  {"name": "PPPK Petra", "type": "Private Christian", "location": "Surabaya"}
]
```

### Excel
Upload Excel file with columns: name, type, location

## 🎯 New Features

### Contact Validation
- WhatsApp format validation
- Email syntax + MX record + SMTP handshake
- Personal vs general email classification
- Verification status in exports

### Enhanced Search
- DAPODIK portal search for Operator Sekolah and Bendahara
- Google Maps integration for up-to-date phone numbers
- Instagram bio discovery for Linktree/Bio.fm links

### Persona-Focused Extraction
- Priority hierarchy: Ketua Yayasan → Operator Sekolah → Kepala Sekolah
- "Nomor HP" and "WA" pattern detection
- Direct contact extraction per person

## 📊 Output

Results include:
- School information (NPSN, foundation, website)
- Decision makers with verified contacts
- Tech stack (LMS platforms detected)
- Quality score (with verification bonus)
- Source URLs for each contact

## 🌐 Deployment

### Vercel (Frontend)

1. Connect your GitHub repository to Vercel
2. Set environment variables:
   - `NEXT_PUBLIC_API_URL` - Your FastAPI backend URL
   - `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key

3. Deploy

### Backend (Railway/Render/Fly.io)

Deploy FastAPI backend separately and update `NEXT_PUBLIC_API_URL`.

## 📈 Cost Estimation

| Service | Free Tier | Per School (est.) |
|---------|-----------|-------------------|
| Serper | 2500 searches | ~5 searches |
| Claude (OpenRouter) | Pay-as-you-go | ~$0.02 |
| Supabase | 500MB database | Free for small projects |

**Processing 50 schools ≈ $1-2 total**

## 🔒 Security

- Row Level Security (RLS) enabled in Supabase
- Environment variables for sensitive keys
- CORS configured for API

## 📄 License

MIT

---

Built for the Indonesian EdTech market 🇮🇩
