# MSHA Critical Metals Mining Analysis

A comprehensive analysis tool for identifying and analyzing critical metals mining operations in the United States using official MSHA (Mine Safety and Health Administration) data.

## Overview

This project analyzes **63 critical metals** across **91,307+ US mining operations** to identify domestic mining capacity, production estimates, and strategic supply chain information. The analysis focuses on metals critical to national security, clean energy, and high-tech manufacturing.

**Note**: The 63 metals were chosen based on the August 2025 report from the USGS titled "Methodology and Technical Input for the 2025 U.S. List of Critical Minerals—Assessing the Potential Effects of Mineral Commodity Supply Chain Disruptions on the U.S. Economy" ([USGS OFR 2025-1047](https://pubs.usgs.gov/of/2025/1047/ofr20251047.pdf)).

### Analysis Capabilities
- **63 critical metals analyzed** (see complete list below)
- Employment-based production estimation
- Geographic distribution mapping
- Supply chain vulnerability assessment
- Strategic metals identification

## Data Sources

### MSHA Mines Database (`Mines.txt`)
- **Source**: MSHA Open Government Data Portal (`https://arlweb.msha.gov/OpenGovernmentData/DataSets/Mines.zip`)
- **Records**: 91,307+ total mining operations
- **Coverage**: Complete US mining registry - both active AND historical operations
- **Time Span**: Decades of mining activity across all commodities

**What's Included:**
- **ALL mining operations** MSHA has ever regulated
- **Both active (5%) and historical/abandoned (93%) mines**
- **Both coal (76%) and metal/nonmetal (24%) operations**
- **59 data fields** per mine including:
  - Basic info (ID, name, location, status)
  - Regulatory data (SIC codes, safety compliance)
  - Operational data (employment, shifts, capacity)
  - Geographic data (GPS coordinates, county, state)
  - Technical specs (mine type, gas category)

**Mine Status Distribution:**
- **Abandoned**: ~93% (historical operations)
- **Active**: ~5% (currently operating)
- **Abandoned and Sealed**: ~1%
- **Other statuses**: <1% (NonProducing, Temporarily Idled, Intermittent)

**Key Insight**: This gives the most complete picture of US mining capacity - both current production and historical capability. The analysis correctly searches this comprehensive database to identify potential critical metals operations, then filters to active mines for production estimates.

### Optional: MSHA Quarterly Production Data
- **MSHA Quarterly Employment/Production Reports**: 2.67+ million quarterly records
- **Enhanced Analysis**: Provides actual employment and hours worked data
- **Automatic Download**: System downloads if available

## Critical Metals Analyzed

The system analyzes these **63 critical metals** using the configuration defined in `critical_metals_analyzer.py`:

### Complete Metals List
1. **Aluminum** - Primary aluminum refining and bauxite mining
2. **Antimony** - Minimal US antimony production  
3. **Arsenic** - Mostly byproduct, no dedicated arsenic mines
4. **Barite** - Barium sulfate mining for drilling mud
5. **Bauxite** - Aluminum ore (bauxite) mining operations
6. **Beryllium** - Beryllium mining - highly specialized
7. **Bismuth** - Very limited US bismuth operations
8. **Cadmium** - Byproduct of zinc refining
9. **Cerium** - Most abundant rare earth element
10. **Cesium** - Extremely limited US cesium production
11. **Chromium** - No significant US chromium mining
12. **Cobalt** - Cobalt as byproduct of copper/nickel mining
13. **Copper** - Major copper mining operations
14. **Dysprosium** - Critical heavy REE
15. **Erbium** - Heavy REE for fiber optics
16. **Europium** - Most expensive REE
17. **Feldspar** - Feldspar mining for ceramics and glass
18. **Fluorspar** - Fluorite mining for chemical industry
19. **Gadolinium** - Heavy REE with specialized uses
20. **Gallium** - Byproduct of aluminum processing
21. **Germanium** - Byproduct of zinc processing
22. **Graphite** - Natural graphite mining
23. **Hafnium** - Byproduct of zirconium processing
24. **Holmium** - Rare heavy REE
25. **Indium** - Byproduct of zinc processing
26. **Iridium** - Rarest PGM
27. **Lanthanum** - Second most abundant REE
28. **Lead** - Lead mining and lead-zinc operations
29. **Lithium** - Lithium mineral extraction and brine operations
30. **Lutetium** - Rarest and most expensive REE
31. **Magnesium** - Magnesium compounds and mineral extraction
32. **Manganese** - Mostly imported, limited US operations
33. **Mica** - Mica mining for electrical and cosmetic industries
34. **Neodymium** - Critical for permanent magnets
35. **Nickel** - Primary nickel ore mining
36. **Niobium** - No significant US niobium production
37. **Palladium** - Platinum group metal, limited US production
38. **Phosphates** - Phosphate rock mining for fertilizers
39. **Platinum** - Stillwater Complex primary PGM operation
40. **Potash** - Potash mining for fertilizer production
41. **Praseodymium** - Light rare earth element
42. **Rhenium** - Byproduct of molybdenum processing
43. **Rhodium** - Rare PGM, mostly byproduct
44. **Rubidium** - Very limited commercial production
45. **Ruthenium** - PGM with limited production
46. **Samarium** - Used in permanent magnets
47. **Scandium** - Not technically REE but grouped with them
48. **Selenium** - Byproduct of copper refining
49. **Silicon** - High-purity silica and silicon production
50. **Silver** - Silver mining operations
51. **Strontium** - Limited US strontium mineral production
52. **Tantalum** - Very limited US tantalum operations
53. **Tellurium** - Byproduct of copper refining
54. **Terbium** - Critical heavy REE
55. **Thulium** - Second rarest REE
56. **Tin** - No active US tin mines since 1990s
57. **Titanium** - Titanium minerals and processing
58. **Tungsten** - Very limited US tungsten production
59. **Vanadium** - Vanadium from uranium operations and steel slag
60. **Ytterbium** - Heavy REE with limited uses
61. **Yttrium** - Heavy rare earth element
62. **Zinc** - Lead-zinc districts and zinc operations
63. **Zirconium** - Zircon sands and zirconium compounds

### Metal Categories

**Major Base Metals** (High confidence, exact SIC codes):
- Aluminum, Bauxite, Copper, Lead, Zinc, Nickel, Lithium, Silver, Platinum

**Industrial Minerals** (Medium confidence, controlled keyword matching):
- Barite, Feldspar, Fluorspar, Magnesium, Mica, Phosphates, Potash, Silicon

**Strategic Metals** (Variable confidence):
- Titanium, Zirconium, Beryllium, Cobalt, Vanadium, Tungsten, Manganese, Chromium

**Rare Earth Elements** (17 elements, grouped analysis):
- Light REE: Cerium, Lanthanum, Neodymium, Praseodymium
- Heavy REE: Yttrium, Dysprosium, Erbium, Europium, Gadolinium, Holmium, Lutetium, Samarium, Terbium, Thulium, Ytterbium
- Related: Scandium

**Platinum Group Metals** (6 elements):
- Platinum, Palladium, Rhodium, Ruthenium, Iridium

**Specialty/Byproduct Metals** (Low confidence, limited US production):
- Antimony, Arsenic, Bismuth, Cadmium, Cesium, Gallium, Germanium, Hafnium, Indium, Niobium, Rhenium, Rubidium, Selenium, Strontium, Tantalum, Tellurium

**No US Production** (Industry verified):
- Tin

## Project Structure

```
msha_scraper/
├── README.md                                    # This file
├── requirements.txt                             # Python dependencies  
├── run_analysis.py                             # Main entry point script
│
├── Core Analysis Scripts
├── critical_metals_analyzer.py                 # Main analysis engine (63 metals)
├── msha_data_downloader.py                    # Downloads official MSHA datasets
├── msha_scraper.py                             # Base MSHA scraper framework
│
└── Analysis Output Directory
    └── msha_critical_metals_analysis/
        ├── raw_data/                           # Source data from MSHA
        │   ├── msha_mines_database/
        │   │   └── Mines.txt                   # 91,307+ mine records
        │   └── msha_production_data/           # Optional quarterly data
        │
        ├── analysis_results/                   # Current analysis outputs
        │   ├── individual_metals/              # Per-metal analysis (126 files)
        │   │   ├── aluminum_analysis.csv       # Mine listings with production estimates
        │   │   ├── aluminum_detailed.json     # Detailed mine metadata
        │   │   └── ... (63 metals × 2 files each)
        │   └── summary_reports/
        │       ├── metals_summary.csv          # Cross-metal summary statistics
        │       └── analysis_report.json       # Full methodology and metadata
        │
        └── legacy_analysis/                    # Previous analysis results  
            └── complete_all_metals_analysis/   # 50-metal system outputs (preserved)
```

## Installation & Setup

1. **Clone the repository**
```bash
git clone [repository-url]
cd msha_scraper
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the complete analysis** (downloads data automatically)
```bash
python run_analysis.py
```

## Usage

### Quick Start - Run Everything
```bash
python run_analysis.py
```
This single command will:
- Download MSHA data if needed (to `raw_data/`)
- Analyze all 63 critical metals
- Generate production estimates  
- Create consolidated tables and reports (in `analysis_results/`)

### Individual Components

**Download Fresh MSHA Data Only:**
```bash
python msha_data_downloader.py
```

**Run Analysis with Existing Data:**
```bash
python critical_metals_analyzer.py
```

### Programmatic Usage
```python
from critical_metals_analyzer import CriticalMetalsAnalyzer

# Initialize analyzer
analyzer = CriticalMetalsAnalyzer()
analyzer.load_msha_data()

# Analyze specific metal
lithium_mines = analyzer.find_metal_mines('lithium')
lithium_production = analyzer.calculate_production_estimates(lithium_mines, 'lithium')

# Run full analysis
results_df, successful_metals = analyzer.analyze_all_metals()
```

## Analysis Methodology

### Metal Identification Methods

1. **Exact SIC Code Matching** (Highest Confidence)
   - Uses official Standard Industrial Classification codes
   - Examples: "Aluminum Ore-Bauxite", "Nickel Ore", "Gold Ore"

2. **Controlled Keyword Matching** (Medium Confidence)  
   - Searches mine names and operators for metal-specific terms
   - Includes exclusion filters to avoid false positives
   - Example: "lithium" but exclude "lithium battery recycling"

3. **Rare Earth Element Group Analysis**
   - Searches for "rare earth" operations then classifies by element
   - Cross-references with known REE operations

4. **Industry Knowledge Verification**
   - Some metals (like tin) have zero expected US production
   - Documented with verification notes

### Production Estimation

Uses employment-based estimation with metal-specific productivity factors:

```
Estimated Annual Production = Employees × Production Factor (MT per employee per year)
```

Production factors calibrated by:
- Industry productivity benchmarks
- Historical production data
- Metal-specific processing requirements
- Mine size and operation type

## Output Files

### Consolidated Tables (50 metals)
Each metal gets two output files:
- `{metal}_complete.csv` - Mine-by-mine production analysis
- `{metal}_detailed_mines.json` - Full mine details with metadata

#### CSV Columns Include:
- **rank** - Production ranking within metal
- **mine_id** - MSHA unique identifier  
- **mine_name** - Operation name
- **state** - Location
- **operator** - Operating company
- **estimated_annual_production_mt** - Production volume estimate
- **employees** - Current employment
- **confidence_level** - Estimate reliability (High/Medium/Low)
- **longitude/latitude** - GPS coordinates
- **verification_method** - How the mine was identified
- **verification_notes** - Analysis methodology notes
- **primary_sic** - Primary Standard Industrial Classification code

### Summary Reports
- `metals_summary.csv` - Summary statistics by metal
- `analysis_report.json` - Full analysis metadata and methodology

## Key Findings

### Metals with Strong US Production
- **Aluminum**: 8 active operations (1.9M MT/year) - major refineries in TX, LA
- **Zinc**: 15 active mines (8.9M MT/year) - distributed across multiple states  
- **Barite**: 24 active operations (1.9M MT/year) - industrial mineral
- **Lithium**: Emerging capacity in Nevada and Arkansas

### Limited US Production
- **Tin**: Zero active US production (verified)
- **Rare Earth Elements**: 17 operations total, concentrated production
- **Platinum Group Metals**: Limited to Stillwater Complex (Montana)

### Supply Chain Vulnerabilities
- Heavy import dependence for most specialty metals
- Geographic concentration in specific states/operators
- Significant abandoned capacity across all metals

## Applications

### Supply Chain Analysis
- Identify domestic mining capacity by metal
- Map geographic distribution of operations  
- Track quarterly production trends
- Assess strategic supply vulnerabilities

### Economic Impact Assessment
- Employment metrics by metal and region
- Production value estimation
- Industry consolidation analysis
- Regional economic dependencies

### Strategic Planning
- Critical minerals supply security
- Domestic production capacity gaps
- Investment opportunity identification
- Trade policy impact analysis

## Data Accuracy & Limitations

### Strengths
- Official MSHA data source (regulatory reporting)
- Comprehensive coverage of US mining operations
- Employment-based methodology using industry benchmarks
- Multiple verification methods with confidence scoring

### Limitations
- Production estimates are modeling-based, not directly reported
- Some metals may have byproduct production not captured
- MSHA data focuses on safety/employment, not production volumes
- Timing lags in MSHA database updates

### Confidence Levels
- **High**: Exact SIC codes + known major operators
- **Medium**: Controlled keyword matching with verification
- **Low**: Limited search results or uncertain identification

## Dependencies

See `requirements.txt`:
- `pandas>=1.5.0` - Data manipulation
- `requests>=2.28.0` - MSHA data download  
- `beautifulsoup4>=4.11.0` - HTML parsing
- `openpyxl>=3.0.0` - Excel export capability

## Contributing

When contributing:
1. Maintain the 50-metal configuration structure
2. Update production factors based on industry data
3. Add verification notes for new identification methods
4. Test with recent MSHA data downloads
5. Update confidence levels appropriately

## License

This project analyzes publicly available MSHA government data. The analysis code and methodologies are provided for research and strategic planning purposes.

## Citation

When using this analysis:
```
MSHA Critical Metals Mining Analysis
Data Source: Mine Safety and Health Administration (MSHA)
Analysis Date: [Current Date]
Methodology: Employment-based production estimation with metal-specific productivity factors
```

---

**For questions about specific metals or analysis methodology, see the configuration details in `critical_metals_analyzer.py:33-567`.**