# Critical Mineral Explorer

A comprehensive analysis tool for critical mineral supply chains with community feedback capabilities.

🌐 **Live Demo**: [https://critical-minerals-explorer.vercel.app](https://critical-minerals-explorer.vercel.app)

## Overview

This prototype analyzes 63 critical metals across 91,307+ US mining operations from the MSHA database to identify domestic production capacity and supply chain gaps. The tool includes an interactive commenting system for gathering community feedback on the analysis.

## New Features

### 💬 Community Commenting System
- **Medium-style comments**: Select text to add contextual feedback
- **Comment moderation**: All comments reviewed before publication  
- **Admin dashboard**: Easy-to-use moderation interface at `/admin.html`
- **Spam protection**: Rate limiting and IP tracking

## Features

- **Interactive dashboard** with filtering by production level and confidence
- **Mine-level data** including location, operator, employment, and production estimates  
- **Supply chain reports** for each metal with technology analysis and bottlenecks
- **Production estimates** based on employment data and industry benchmarks

## Data Processing Workflow

This project follows a 4-step pipeline to generate comprehensive critical mineral reports:

1. **Metal Selection** → USGS critical minerals list (63 metals)
2. **Data Collection** → MSHA database scraping for current US mining operations  
3. **Report Generation** → OpenAI 4o-mini-deep-research creates detailed supply chain reports
4. **Fact-Checking & Enhancement** → Claude Opus 4.1 validates accuracy and adds structured summaries

**Key Scripts:**
- `msha_scraper/` - Downloads and processes MSHA mining data
- `process_all_metals.py` - Batch generates initial reports using OpenAI
- `check_and_improve.py` - Fact-checks and enhances reports using Claude
- `report_review_reformat.py` - Integrates expert fact-checking critiques

## Quick Start

**View online**: [https://critical-minerals-explorer.vercel.app](https://critical-minerals-explorer.vercel.app)

**Run locally**:
```bash
git clone https://github.com/dgoodwin208/Critical-Minerals-Explorer.git
cd Critical-Minerals-Explorer
python server.py
```

## Data Sources

- **MSHA Mines Database**: 91,307+ US mining operations (both active and historical)
- **Metal Selection**: Based on 2025 USGS critical minerals list
- **Production Estimates**: Employment-based modeling with metal-specific factors
- **Confidence Levels**: High (exact SIC codes), Medium (keyword matching), Low (limited data)

## Key Findings

- **Strong US production**: Aluminum (1.9M MT/year), Zinc (8.9M MT/year), Barite (1.9M MT/year)
- **Limited production**: Most rare earth elements, platinum group metals  
- **No US production**: Tin (verified zero active operations)
- **Supply vulnerabilities**: Heavy import dependence for specialty metals

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Vercel Serverless Functions (Node.js)
- **Database**: Vercel KV (Redis)
- **Data processing**: Python (pandas)
- **Visualization**: Chart.js, DataTables
- **Deployment**: Vercel with Git integration

## Deployment Setup

### Environment Configuration

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Configure Vercel KV**:
   - Add Vercel KV to your project in the Vercel dashboard
   - `KV_REST_API_URL` and `KV_REST_API_TOKEN` will be set automatically

3. **Set Admin Secret**:
   ```bash
   # In Vercel dashboard or via CLI
   vercel env add ADMIN_SECRET production
   # Enter a secure password for comment moderation
   ```

4. **Optional Settings**:
   - `MAX_COMMENTS_PER_HOUR=3` (rate limiting)
   - `COMMENT_MAX_LENGTH=500` (comment length limit)

### Comment System Usage

- **Users**: Select text in detailed reports → Click comment icon → Submit feedback
- **Admins**: Visit `/admin.html` → Enter admin secret → Moderate comments
- **API**: RESTful endpoints for comments at `/api/comments/`

## Limitations

- Production estimates are modeled, not directly reported
- Some byproduct production may not be captured  
- MSHA data focuses on employment/safety, not production volumes
- Results should be verified against industry sources

## Citation

```
Critical Mineral Explorer
Data: Mine Safety and Health Administration (MSHA), August 2025
URL: https://github.com/dgoodwin208/Critical-Minerals-Explorer
```

Built by Daniel Goodwin and Jayme Feyhl-Buska as a research prototype.