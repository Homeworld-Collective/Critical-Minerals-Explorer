# Report Maker Tools

This directory contains scripts for generating, improving, and extracting data from critical mineral reports.

## Scripts

### Report Generation
- **`generate_metal_report.py`** - Generates detailed reports for individual metals using OpenAI GPT-4
- **`process_all_metals.py`** - Batch processes all 63 critical minerals to generate reports
- **`deep_research_tool.py`** - Deep research functionality for comprehensive analysis

### Report Improvement
- **`check_and_improve.py`** - Fact-checks and improves reports using Anthropic Claude Opus 4.1
- **`report_review_reformat.py`** - Reviews and reformats reports for consistency

### Data Extraction
- **`smart_extract_detailedreports.py`** - Extracts data from detailed reports using Claude AI to intelligently handle unit conversions and create enhanced CSV files

## Usage

### Generate reports for all metals:
```bash
python report_maker/process_all_metals.py
```

### Generate report for a single metal:
```bash
python report_maker/generate_metal_report.py aluminum
```

### Fact-check and improve reports:
```bash
python report_maker/check_and_improve.py --metal aluminum
python report_maker/check_and_improve.py --improve-all
```

### Extract data to enhanced CSV:
```bash
python report_maker/smart_extract_detailedreports.py
```

## Requirements
- OpenAI API key (for report generation)
- Anthropic API key (for fact-checking and smart extraction)
- Python packages: openai, anthropic

## Output
- Reports are saved to `detailed_reports/` directory
- Feedback is saved to `detailed_reports_feedback/` directory
- Enhanced CSV is saved as `enhanced-criticalminerals-2030estimates-GDP.csv`