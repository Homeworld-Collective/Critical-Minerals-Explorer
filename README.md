# Critical Mineral Explorer

A comprehensive web application for exploring critical mineral supply chain data for the US and allied nations, built on top of official MSHA (Mine Safety and Health Administration) mining data.

🌐 **Live Demo**: [https://critical-minerals-explorer.vercel.app](https://critical-minerals-explorer.vercel.app)

## Overview

This project analyzes **63 critical metals** across **91,307+ US mining operations** to identify domestic mining capacity, production estimates, and strategic supply chain information. The analysis focuses on metals critical to national security, clean energy, and high-tech manufacturing.

**Key Focus**: Where can biotechnology help critical minerals production in the US? Each report identifies specific constraints limiting domestic production and processing capacity, highlighting opportunities where biological systems could address processing, separation, or environmental challenges.

### What Makes This Unique

- **Comprehensive Data**: Built on the complete MSHA mining database - both active and historical operations
- **Interactive Exploration**: Web-based dashboard with filtering, search, and detailed mine information
- **Biotechnology Focus**: Analysis specifically identifies opportunities for biotech applications in mining and processing
- **Strategic Intelligence**: Identifies domestic production gaps and supply chain vulnerabilities
- **Production Estimates**: Employment-based modeling provides production capacity estimates

## Features

### 🏗️ Interactive Dashboard
- **Overview of 63 critical metals** with production-level filtering
- **Search functionality** to quickly find specific metals
- **Summary statistics** showing total mines, production, and employment
- **Color-coded production levels**: Significant, Moderate, Limited, Minimal, None, Byproduct, Emerging

### 📊 Detailed Supply Chain Reports
- **Comprehensive analysis** for each metal including:
  - Key discovery, extraction, separation, and purification technologies
  - Production volumes, demand forecasts, and market analysis
  - Supply chain bottlenecks and technical challenges
  - **Biotechnology opportunities** where biological systems could improve processes
- **Source citations** and technical references
- **Last updated dates** for data freshness

### 🏭 Mine Information Database
- **Detailed mine data** from MSHA database (91,307+ operations)
- **Mine-specific information**: location, operator, employees, production estimates
- **Interactive modals** with complete operational details
- **Geographic coordinates** for mapping applications
- **Confidence levels** and verification methodologies

### 📈 Analysis & Visualization
- **Production level distribution** charts
- **Confidence level analysis** 
- **Visual data representation** using Chart.js
- **Employment and capacity metrics**

## Data Sources & Methodology

### MSHA Mining Database
- **Source**: Official MSHA Open Government Data Portal
- **Coverage**: Complete US mining registry (91,307+ operations)
- **Includes**: Both active (5%) and historical/abandoned (95%) mines
- **Data Fields**: 59 fields including location, employment, SIC codes, operational status

### Critical Metals Selection
The 63 metals analyzed are based on the August 2025 USGS report "Methodology and Technical Input for the 2025 U.S. List of Critical Minerals" ([USGS OFR 2025-1047](https://pubs.usgs.gov/of/2025/1047/ofr20251047.pdf)).

### Analysis Methods
1. **Exact SIC Code Matching** (Highest confidence)
2. **Controlled Keyword Matching** (Medium confidence)  
3. **Rare Earth Element Group Analysis**
4. **Employment-Based Production Estimation**

## Quick Start

### Option 1: View Online
Visit [https://critical-minerals-explorer.vercel.app](https://critical-minerals-explorer.vercel.app) to explore the data immediately.

### Option 2: Run Locally
```bash
# Clone the repository
git clone https://github.com/dgoodwin208/Critical-Minerals-Explorer.git
cd Critical-Minerals-Explorer

# Start local server
python server.py

# Open browser to http://localhost:8080
```

### Option 3: Static Files
Open `index.html` directly in your browser (some features may not work due to CORS restrictions).

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Data Processing**: Python analysis scripts using pandas
- **Visualization**: Chart.js for interactive charts
- **Markdown Rendering**: markdown-it for report display
- **Icons**: Font Awesome
- **Deployment**: Vercel for hosting

## Project Structure

```
Critical-Minerals-Explorer/
├── index.html                          # Main web application
├── script.js                          # Application logic
├── styles.css                         # Styling and responsive design
├── server.py                          # Local development server
├── introduction.md                     # Biotechnology analysis introduction
│
├── detailed_reports/                   # Generated supply chain reports
│   ├── aluminum_report.md             # Technical analysis per metal
│   ├── lithium_report.md              # Market analysis & bottlenecks
│   └── ... (63 metal reports)
│
└── msha_scraper/                      # Data analysis backend
    ├── critical_metals_analyzer.py    # Main analysis engine (63 metals)
    ├── msha_data_downloader.py       # MSHA data acquisition
    └── msha_critical_metals_analysis/
        └── analysis_results/
            ├── summary_reports/
            │   └── metals_summary.csv    # Cross-metal statistics
            └── individual_metals/
                ├── aluminum_detailed.json  # Mine-level data
                └── ... (63 metal files)
```

## Key Findings

### Metals with Strong US Production
- **Aluminum**: 8 active operations (1.9M MT/year) - major refineries
- **Zinc**: 15 active mines (8.9M MT/year) - distributed production  
- **Barite**: 24 active operations (1.9M MT/year) - industrial mineral
- **Lithium**: Emerging capacity in Nevada and Arkansas

### Critical Supply Chain Gaps
- **Rare Earth Elements**: Only 17 US operations, concentrated production
- **Platinum Group Metals**: Limited to Stillwater Complex (Montana)
- **Strategic Metals**: Heavy import dependence for most specialty metals
- **Tin**: Zero active US production (verified)

### Biotechnology Opportunities
The analysis identifies where biological systems could address:
- **Separation challenges** in rare earth processing
- **Environmental remediation** of mining waste
- **Metal recovery** from low-grade ores
- **Sustainable processing** alternatives to harsh chemicals

## Applications

### Supply Chain Intelligence
- Identify domestic production capacity by metal
- Map geographic distribution of critical operations
- Assess strategic supply vulnerabilities
- Track industry consolidation trends

### Investment & Policy Analysis  
- Critical minerals supply security assessment
- Domestic production capacity gap analysis
- Regional economic impact evaluation
- Trade policy scenario planning

### Biotechnology Research
- Target identification for bio-processing applications
- Market sizing for biotech mining solutions
- Technical challenge prioritization
- Partnership opportunity mapping

## Browser Compatibility

- ✅ Chrome (recommended)
- ✅ Firefox  
- ✅ Safari
- ✅ Edge

## Contributing

We welcome contributions! Areas of particular interest:
- Additional biotechnology opportunity analysis
- Enhanced data visualization features
- Mobile responsiveness improvements
- Data accuracy verification and updates

## Data Updates

To update with new data:
1. Run the MSHA analysis scripts: `python run_analysis.py`
2. Update metal reports in `detailed_reports/`
3. Refresh summary statistics in `metals_summary.csv`
4. Deploy updated files

## Limitations & Accuracy

### Strengths
- Official MSHA regulatory data source
- Comprehensive US mining operations coverage
- Multiple verification methods with confidence scoring
- Employment-based methodology using industry benchmarks

### Limitations
- Production estimates are modeling-based, not directly reported
- Some byproduct production may not be captured
- MSHA focuses on safety/employment, not production volumes
- Timing lags in database updates

## Citation

When using this analysis:
```
Critical Mineral Explorer - MSHA Mining Analysis
Data Source: Mine Safety and Health Administration (MSHA)
Analysis Date: August 2025
Methodology: Employment-based production estimation with metal-specific factors
URL: https://github.com/dgoodwin208/Critical-Minerals-Explorer
```

## License

This project analyzes publicly available MSHA government data. The analysis code and methodologies are provided for research and strategic planning purposes.

---

**Built by Daniel Goodwin and Jayme Feyhl-Buska** | [GitHub Repository](https://github.com/dgoodwin208/Critical-Minerals-Explorer)