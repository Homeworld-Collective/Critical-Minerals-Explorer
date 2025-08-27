# Fact-Check and Report Improvement Workflow

This document describes the two-step process for improving the accuracy of detailed mineral reports using AI models.

## Step 1: Generate Fact-Check Feedback (Claude)

Use `check_and_improve.py` to generate rigorous fact-checking feedback:

### Setup
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
pip install -r msha_scraper/requirements.txt
```

### Usage Examples
```bash
# List all available reports
python check_and_improve.py --list

# Fact-check a single report (creates aluminum_feedback.md)
python check_and_improve.py --metal aluminum

# Generate feedback for all reports (creates {metal}_feedback.md for each)
python check_and_improve.py --feedback-all

# Dry run to see what would be processed
python check_and_improve.py --metal aluminum --dry-run
```

### Output
- Creates `detailed_reports_feedback/{metal}_feedback.md` files
- Contains bullet-pointed lists of:
  - Factual inaccuracies
  - Dead/questionable links  
  - Unsupported claims
  - Outdated information
  - Technical concerns

## Step 2: Integrate Feedback into Reports (OpenAI)

Use `report_review_reformat.py` to integrate feedback and improve reports:

### Setup
```bash
export OPENAI_API_KEY="your-openai-key"
# (requirements already installed from step 1)
```

### Current Status
- Works with existing fact-check critiques from `Critical Minerals Explorer Fact-Checking.md`
- 19 metals ready for processing (have both reports and critiques)
- Can be extended to work with Claude-generated feedback files

### Usage Examples
```bash
# List metals with existing fact-check critiques
python report_review_reformat.py --list

# Review single metal with existing critique
python report_review_reformat.py --metal samarium

# Review all metals with existing critiques
python report_review_reformat.py
```

## Recommended Workflow

### Option A: Process metals with existing critiques
1. Use `report_review_reformat.py` for the 19 metals that already have critiques
2. This integrates expert-reviewed feedback immediately

### Option B: Generate new feedback first
1. Use `check_and_improve.py --feedback-all` to fact-check all 54 reports
2. Review the generated feedback files manually
3. Extend `report_review_reformat.py` to work with Claude feedback files
4. Process all reports with AI-integrated improvements

### Option C: Hybrid approach
1. Process the 19 metals with existing critiques using `report_review_reformat.py`
2. Generate Claude feedback for remaining 35 metals using `check_and_improve.py`
3. Use Claude feedback to improve those reports

## File Structure After Processing

```
detailed_reports/
├── aluminum_report.md          # Updated with improvements
├── samarium_report.md          # Updated with improvements
└── ...

detailed_reports_feedback/      # New directory
├── aluminum_feedback.md        # Claude fact-check findings
├── samarium_feedback.md        # Claude fact-check findings  
└── ...

detailed_reports_backup/        # Automatic backups
├── aluminum_report_20250827_143022.md
├── samarium_report_20250827_143155.md
└── ...
```

## Cost Estimation

- **Claude fact-checking**: ~$0.20-0.50 per report
- **OpenAI integration**: ~$0.50-2.00 per report  
- **Total for all 54 reports**: ~$40-135

Use `--dry-run` first to verify scope before processing.

## Safety Features

- ✅ Automatic timestamped backups before any changes
- ✅ Dry-run mode to preview processing
- ✅ Error handling with retry logic
- ✅ Individual file processing (can stop/resume anytime)
- ✅ Separate feedback files (can review before integration)