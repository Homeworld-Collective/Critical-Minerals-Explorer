#!/usr/bin/env python3
"""
check_and_improve.py

Script to fact-check and improve detailed mineral reports using Anthropic's Claude Opus 4.1.
Can generate feedback only, or both feedback and improved reports in one step.

Usage:
    python check_and_improve.py --metal aluminum                    # Improve single report
    python check_and_improve.py --metal aluminum --feedback-only    # Feedback only
    python check_and_improve.py --feedback-all                      # Feedback for all reports
    python check_and_improve.py --improve-all                       # Improve all reports
    python check_and_improve.py --list                              # List available reports
"""

import os
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

import anthropic


class ReportFactChecker:
    """Fact-check reports using Claude and generate feedback files."""
    
    def __init__(self, 
                 model_name: str = "claude-opus-4-1-20250805",
                 reports_dir: str = "detailed_reports",
                 feedback_dir: str = "detailed_reports_feedback"):
        
        self.model_name = model_name
        self.reports_dir = Path(reports_dir)
        self.feedback_dir = Path(feedback_dir)
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        # Create feedback directory
        self.feedback_dir.mkdir(exist_ok=True)
            
        print(f"Initialized ReportFactChecker with model: {model_name}")
    
    def _build_fact_check_prompt(self, report_content: str, metal_name: str) -> str:
        """Build the prompt for Claude to fact-check the report."""
        
        prompt = f"""Please fact-check this critical mineral supply chain report for {metal_name.title()} and return BOTH the fact-check findings AND an improved version of the report.

REPORT TO FACT-CHECK:
{report_content}

INSTRUCTIONS:
1. First, conduct a rigorous fact-check identifying:
   - Factual inaccuracies (wrong numbers, dates, company names, locations)
   - Dead or broken links/references
   - Unsupported claims that need citations
   - Outdated information that should be updated
   - Questionable technical statements
   - Missing context that affects accuracy

2. Then, return a corrected version of the report that:
   - Fixes all identified factual errors
   - Removes or properly qualifies unsupported claims
   - Updates outdated information where possible
   - Maintains the exact same section structure and markdown formatting
   - Preserves the biotechnology focus and technical depth
   - Uses the same professional writing style
   - Adds italicized summary lines under quantitative headers (e.g., "*Summary: 35,000 tons/year*")
   - Adds italicized brief summary lines under technology headers (e.g., "*Summary: open‑pit bauxite; dredge for laterite; red‑mud dry stacking*")
   - Moves the "Key Bottleneck technology for US and Allies Domestic Production" section to the top of the report (right after the introduction)

FORMAT YOUR RESPONSE AS:

# Fact-Check: {metal_name.title()}

## Inaccuracies Found:
• [Specific issue with quote from report]

## Dead/Questionable Links:
• [List any broken or questionable references]

## Unsupported Claims:
• [Claims that need better citations]

## Outdated Information:
• [Information that needs updating with current data]

## Technical Concerns:
• [Questionable technical statements or missing context]

---

# IMPROVED REPORT

[Return the complete corrected report with these enhancements:
1. All fact-check issues fixed
2. Summary lines added under headers:
   - For quantitative headers (production, demand, etc.): "Summary: X tons/year" or "Summary: X facilities"
   - For technology headers: "Summary: brief tech list separated by semicolons"
3. "Key Bottleneck technology" section moved to top (right after introduction)
4. Same markdown structure and professional style maintained]"""

        return prompt
    
    def _call_claude(self, prompt: str, max_retries: int = 3) -> str:
        """Call Claude API with retry logic and streaming for long requests."""
        
        for attempt in range(max_retries):
            try:
                print("   📡 Starting streaming response...")
                
                # Use streaming for long requests to avoid timeouts
                with self.client.messages.stream(
                    model=self.model_name,
                    max_tokens=32000,  # Large enough for feedback + complete improved report
                    temperature=0.1,  # Low temperature for consistency
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                ) as stream:
                    response_text = ""
                    for text in stream.text_stream:
                        response_text += text
                        # Show progress every 1000 characters
                        if len(response_text) % 1000 == 0:
                            print(f"   📝 Received {len(response_text):,} characters...", end='\r')
                
                print(f"   ✅ Streaming complete: {len(response_text):,} characters")
                return response_text.strip()
                
            except Exception as e:
                print(f"API call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise
    
    def _create_backup(self, report_path: Path) -> Path:
        """Create a backup of the original report."""
        backup_dir = Path("detailed_reports_backup")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{report_path.stem}_{timestamp}_claude.md"
        backup_path = backup_dir / backup_name
        
        backup_path.write_text(report_path.read_text(encoding='utf-8'), encoding='utf-8')
        return backup_path
    
    def fact_check_single_report(self, metal_name: str, dry_run: bool = False, feedback_only: bool = False) -> bool:
        """Fact-check a single metal report, save feedback, and optionally improve the report."""
        
        # Normalize metal name
        metal_name_clean = metal_name.lower().strip()
        report_path = self.reports_dir / f"{metal_name_clean}_report.md"
        feedback_path = self.feedback_dir / f"{metal_name_clean}_feedback.md"
        
        if not report_path.exists():
            print(f"❌ Report not found: {report_path}")
            return False
        
        action = "Fact-checking" if feedback_only else "Fact-checking and improving"
        print(f"\n🔍 {action} {metal_name_clean} report...")
        
        # Load original report
        report_content = report_path.read_text(encoding='utf-8')
        print(f"   Report length: {len(report_content):,} characters")
        
        if dry_run:
            print(f"   [DRY RUN] Would call Claude for {action.lower()}")
            return True
        
        try:
            prompt = self._build_fact_check_prompt(report_content, metal_name_clean)
            print(f"   🤖 Calling {self.model_name}...")
            
            response_content = self._call_claude(prompt)
            
            print(f"   ✅ Received response: {len(response_content):,} characters")
            
            # Parse response to separate feedback and improved report
            if "# IMPROVED REPORT" in response_content:
                parts = response_content.split("# IMPROVED REPORT")
                feedback_content = parts[0].strip().rstrip("-").strip()
                improved_report = parts[1].strip()
                
                print(f"   📝 Extracted feedback: {len(feedback_content):,} characters")
                print(f"   📝 Extracted improved report: {len(improved_report):,} characters")
                
                # Save feedback
                feedback_path.write_text(feedback_content, encoding='utf-8')
                print(f"   💾 Saved feedback: {feedback_path}")
                
                if not feedback_only and improved_report:
                    # Create backup
                    backup_path = self._create_backup(report_path)
                    print(f"   📁 Created backup: {backup_path}")
                    
                    # Save improved report
                    report_path.write_text(improved_report, encoding='utf-8')
                    print(f"   💾 Updated report: {report_path}")
                
            else:
                # Fallback: save entire response as feedback
                feedback_path.write_text(response_content, encoding='utf-8')
                print(f"   💾 Saved feedback: {feedback_path}")
                print("   ⚠️  No improved report section found in response")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error processing {metal_name_clean}: {e}")
            return False
    
    def fact_check_all_reports(self, dry_run: bool = False, feedback_only: bool = False) -> Dict[str, bool]:
        """Fact-check all available reports and optionally improve them."""
        
        results = {}
        
        # Get all report files
        report_files = list(self.reports_dir.glob("*_report.md"))
        
        if not report_files:
            print("No report files found")
            return results
        
        all_metals = [f.stem.replace("_report", "") for f in report_files]
        
        # Filter out metals that already have feedback files
        metals_to_process = []
        skipped_metals = []
        
        for metal in all_metals:
            feedback_path = self.feedback_dir / f"{metal}_feedback.md"
            if feedback_path.exists():
                skipped_metals.append(metal)
            else:
                metals_to_process.append(metal)
        
        action = "fact-check" if feedback_only else "fact-check and improve"
        
        if skipped_metals:
            print(f"Skipping {len(skipped_metals)} metals with existing feedback:")
            for metal in sorted(skipped_metals):
                print(f"  ⏭️  {metal}")
        
        if not metals_to_process:
            print("No reports to process (all have existing feedback)")
            return results
        
        print(f"\nFound {len(metals_to_process)} reports to {action}:")
        for metal in sorted(metals_to_process):
            print(f"  • {metal}")
        
        # Process each metal
        for metal in sorted(metals_to_process):
            results[metal] = self.fact_check_single_report(metal, dry_run=dry_run, feedback_only=feedback_only)
            
            # Delay to be respectful to API
            if not dry_run:
                time.sleep(3)  # Slightly longer delay for more complex requests
        
        # Print summary
        successful = sum(1 for success in results.values() if success)
        action_past = "fact-checked" if feedback_only else "fact-checked and improved"
        print(f"\n📊 Summary: {successful}/{len(results)} reports {action_past} successfully")
        
        if skipped_metals:
            print(f"📋 Skipped {len(skipped_metals)} metals with existing feedback")
        
        return results
    
    def list_available_reports(self) -> List[str]:
        """List all available reports."""
        
        report_files = list(self.reports_dir.glob("*_report.md"))
        metals = sorted([f.stem.replace("_report", "") for f in report_files])
        
        return metals


def main():
    """Main function with command line interface."""
    
    parser = argparse.ArgumentParser(
        description="Fact-check critical mineral reports using Anthropic Claude"
    )
    
    parser.add_argument(
        "--metal", 
        help="Fact-check only this specific metal (e.g., 'aluminum')"
    )
    
    parser.add_argument(
        "--feedback-all", 
        action="store_true",
        help="Generate feedback for all available reports (feedback only)"
    )
    
    parser.add_argument(
        "--improve-all", 
        action="store_true",
        help="Fact-check and improve all available reports"
    )
    
    parser.add_argument(
        "--feedback-only", 
        action="store_true",
        help="Generate feedback only, don't modify reports"
    )
    
    parser.add_argument(
        "--model", 
        default="claude-opus-4-1-20250805",
        help="Anthropic model to use (default: claude-opus-4-1-20250805)"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be processed without making API calls"
    )
    
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List available reports"
    )
    
    args = parser.parse_args()
    
    try:
        checker = ReportFactChecker(model_name=args.model)
        
        if args.list:
            metals = checker.list_available_reports()
            
            print(f"\n📋 Available Reports ({len(metals)} total):")
            for metal in metals:
                print(f"   • {metal}")
            
            return
        
        if args.metal:
            # Process single metal
            feedback_only = args.feedback_only
            success = checker.fact_check_single_report(
                args.metal, 
                dry_run=args.dry_run, 
                feedback_only=feedback_only
            )
            exit(0 if success else 1)
            
        elif args.feedback_all:
            # Fact-check all metals (feedback only)
            results = checker.fact_check_all_reports(dry_run=args.dry_run, feedback_only=True)
            
            failed = [metal for metal, success in results.items() if not success]
            if failed:
                print(f"\n⚠️  Failed metals: {', '.join(failed)}")
                exit(1)
                
        elif args.improve_all:
            # Fact-check and improve all metals
            results = checker.fact_check_all_reports(dry_run=args.dry_run, feedback_only=False)
            
            failed = [metal for metal, success in results.items() if not success]
            if failed:
                print(f"\n⚠️  Failed metals: {', '.join(failed)}")
                exit(1)
        
        else:
            print("Please specify --metal, --feedback-all, --improve-all, or --list")
            parser.print_help()
            exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
        exit(130)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()