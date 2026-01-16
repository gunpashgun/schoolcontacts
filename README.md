# 🇮🇩 Indonesia EdTech Lead Gen Engine

**Automated lead enrichment tool for the Indonesian private school market.**

Find Decision Makers (Yayasan Chairmen, School Directors, Principals) and their contact details (WhatsApp/Email) from Indonesian schools.

## Features

- 🔍 **Smart Search** - Targeted Google searches via Serper API
- 🌐 **Web Scraping** - Crawl4AI optimized for LLM processing
- 🤖 **AI Extraction** - Claude 3.5 Sonnet or GPT-4o-mini
- 📊 **Indonesian Optimized** - Understands "Ketua Yayasan", "Kepala Sekolah", etc.
- 💬 **WhatsApp Priority** - Extracts wa.me links and +62 numbers
- 📁 **Export** - CSV and Excel output

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for fallback scraping)
playwright install chromium
```

### 2. Configure API Keys

```bash
# Copy example config
cp env.example .env

# Edit .env with your API keys
```

**Required API Keys:**

| Service | Purpose | Get it at |
|---------|---------|-----------|
| Serper.dev | Google Search | https://serper.dev (2500 free) |
| Anthropic | Claude LLM | https://console.anthropic.com |
| OpenAI (alt) | GPT-4 LLM | https://platform.openai.com |

### 3. Run

```bash
# Process priority schools (Surabaya - 5 schools)
python main.py

# Process all schools
python main.py --all

# Process single school
python main.py --school "PPPK Petra"

# Process by location
python main.py --location Jakarta

# Validate config
python main.py --validate
```

## Output

Results are saved to `output/` folder:

- `leads_YYYYMMDD_HHMMSS.csv`
- `leads_YYYYMMDD_HHMMSS.xlsx`

### Output Columns

| Column | Description |
|--------|-------------|
| School Name | Name of the school |
| School Type | Private Christian, International, etc. |
| Location | City/region |
| Foundation Name | Yayasan name |
| NPSN | National School ID (8 digits) |
| Official Website | School website URL |
| Official Email | General contact email |
| WhatsApp Business | Primary WhatsApp number |
| DM1-3 Name | Decision maker names |
| DM1-3 Role | Roles (Ketua Yayasan, etc.) |
| DM1-3 WhatsApp | Personal WhatsApp |
| DM1-3 LinkedIn | LinkedIn profiles |
| Data Quality | Score 0-100% |

## CLI Options

```
usage: main.py [-h] [--all] [--priority] [--location LOCATION]
               [--school SCHOOL] [--batch BATCH] [--offset OFFSET]
               [--delay DELAY] [--output {csv,excel,both}] [--validate]

Options:
  --all                 Process all schools in database
  --priority            Process priority schools only (default)
  --location LOCATION   Filter by location (Jakarta, Surabaya, etc.)
  --school SCHOOL       Process single school by name
  --batch BATCH         Batch size (default: 5)
  --offset OFFSET       Skip first N schools
  --delay DELAY         Delay between schools in seconds (default: 3)
  --output {csv,excel,both}  Output format (default: both)
  --validate            Validate config and exit
```

## Architecture

```
schoolcontacts/
├── main.py           # CLI & orchestration
├── config.py         # Configuration
├── models.py         # Pydantic data models
├── search.py         # Serper Google Search
├── scraper.py        # Web scraping (Crawl4AI/Playwright)
├── extractor.py      # LLM extraction (Claude/GPT)
├── schools_data.py   # Target school database
├── requirements.txt  # Dependencies
├── env.example       # Environment template
└── output/           # Export folder
```

## Indonesian-Specific Features

### Role Keywords (Highest to Lowest Priority)

1. **Ketua Yayasan** - Foundation Chairman (ultimate decision maker)
2. **Pembina** - Patron/Supervisor
3. **Direktur** - Director
4. **Kepala Sekolah** - School Principal
5. **Wakil Kepala** - Vice Principal
6. **Bendahara** - Treasurer

### Phone Number Handling

- Detects `wa.me/62xxx` links
- Detects `api.whatsapp.com` links
- Normalizes `08xxx` → `+62xxx`
- Recognizes landlines: `021` (Jakarta), `031` (Surabaya)

### NPSN Integration

- Extracts 8-digit National School ID
- Can lookup in `sekolah.data.kemdikbud.go.id`

## Target Schools

### Priority (Week 1 - Surabaya)
- PPPK Petra
- Yohanes Gabriel Foundation
- Santa Clara Catholic School
- Gloria Christian School
- Stella Maris School

### Total Database: 50+ Schools
- Jakarta B2B targets
- National groups (BINUS, BPK Penabur, Tarakanita)
- Regional schools (Semarang, Bali)

## Rate Limiting

Default settings (configurable in `.env`):

- Serper API: 30 requests/minute
- Scraping delay: 2 seconds/page
- School delay: 3 seconds between schools

## Troubleshooting

### "SERPER_API_KEY not set"
```bash
cp env.example .env
# Edit .env and add your Serper API key
```

### "Crawl4AI not installed"
```bash
pip install crawl4ai
# Falls back to Playwright automatically
```

### "Playwright error"
```bash
playwright install chromium
```

## Cost Estimation

| Service | Free Tier | Per School (est.) |
|---------|-----------|-------------------|
| Serper | 2500 searches | ~5 searches |
| Claude | Pay-as-you-go | ~$0.02 |
| OpenAI | Pay-as-you-go | ~$0.01 |

**Processing 50 schools ≈ $1-2 total**

## License

MIT

## Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

---

Built for the Indonesian EdTech market 🇮🇩

