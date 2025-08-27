#!/usr/bin/env python3
"""
report_review_reformat.py

Script to review and reformat detailed mineral reports using fact-checking critiques.
Uses a strong OpenAI model to integrate feedback and improve report accuracy.

Usage:
    python report_review_reformat.py
    python report_review_reformat.py --metal aluminum --dry-run
    python report_review_reformat.py --model gpt-4o --backup
"""

import os
import re
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple

import openai


class ReportReviewer:
    """Main class to handle report review and reformatting."""
    
    def __init__(self, 
                 model_name: str = "gpt-4o",
                 fact_check_file: str = "Critical Minerals Explorer Fact-Checking.md",
                 reports_dir: str = "detailed_reports",
                 backup_dir: str = "detailed_reports_backup"):
        
        self.model_name = model_name
        self.fact_check_file = Path(fact_check_file)
        self.reports_dir = Path(reports_dir)
        self.backup_dir = Path(backup_dir)
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        # Load fact-checking document
        self.fact_check_critiques = self._load_fact_check_document()
        
        print(f"Initialized ReportReviewer with model: {model_name}")
        print(f"Loaded {len(self.fact_check_critiques)} fact-check critiques")
    
    def _load_fact_check_document(self) -> Dict[str, str]:
        """Parse the fact-checking markdown document by metal headers."""
        if not self.fact_check_file.exists():
            raise FileNotFoundError(f"Fact-checking file not found: {self.fact_check_file}")
        
        content = self.fact_check_file.read_text(encoding='utf-8')
        critiques = {}
        
        # Split by top-level headers (# Metal Name)
        sections = re.split(r'\n# ([^\n]+)\n', content)
        
        # Skip the first section (document title)
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                metal_name = sections[i].strip().lower()
                critique_content = sections[i + 1].strip()
                
                if critique_content and metal_name:
                    critiques[metal_name] = critique_content
                    print(f"Loaded critique for: {metal_name}")
        
        return critiques
    
    def _get_available_models(self) -> List[str]:
        """Get list of available OpenAI models, prioritizing strongest ones."""
        try:
            models = self.client.models.list()
            model_names = [model.id for model in models.data]
            
            # Prioritize strongest models
            priority_order = [
                "o3-pro", "o3", "gpt-5", "gpt-4o", "gpt-4-turbo", 
                "gpt-4", "gpt-3.5-turbo"
            ]
            
            available_priority = [m for m in priority_order if m in model_names]
            return available_priority + [m for m in model_names if m not in priority_order]
            
        except Exception as e:
            print(f"Warning: Could not fetch model list: {e}")
            return [self.model_name]
    
    def _create_backup(self, report_path: Path) -> Path:
        """Create a backup of the original report."""
        self.backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{report_path.stem}_{timestamp}.md"
        backup_path = self.backup_dir / backup_name
        
        backup_path.write_text(report_path.read_text(encoding='utf-8'), encoding='utf-8')
        return backup_path
    
    def _build_review_prompt(self, original_report: str, critique: str, metal_name: str) -> str:
        """Build the prompt for the AI model to review and integrate feedback."""
        
        prompt = f"""You are a technical reviewer for critical mineral supply chain reports. Your task is to carefully review an existing report, validate fact-checking feedback, and integrate valid corrections to produce an improved version.

METAL: {metal_name.title()}

ORIGINAL REPORT:
{original_report}

FACT-CHECKING FEEDBACK:
{critique}

INSTRUCTIONS:

1. **Validate the feedback**: Carefully assess each point in the fact-checking feedback. Some critiques may be:
   - ✅ Valid corrections (wrong numbers, outdated info, misstatements)
   - 🔎 Clarifications needed (vague claims, missing context)  
   - ⚠️ Important corrections (factual errors, overstated claims)
   - ❌ Invalid/irrelevant (if feedback doesn't apply or is wrong)

2. **Integrate valid feedback**: For each valid point:
   - Correct factual errors and update outdated information
   - Add missing context and clarifications
   - Remove unsupported claims or mark them as speculative
   - Update references and citations as suggested
   - Preserve the original report structure and style

3. **Maintain report quality**:
   - Keep the same section structure and formatting
   - Preserve technical accuracy and depth
   - Maintain professional, concise writing style
   - Ensure all claims are properly supported
   - Keep focus on biotechnology opportunities where relevant

4. **Output the complete revised report**: Return the full updated report with all valid feedback integrated. Do not provide a summary - return the complete revised markdown report.

REVISED REPORT:"""

        return prompt
    
    def _call_ai_model(self, prompt: str, max_retries: int = 3) -> str:
        """Call the AI model with retry logic."""
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert technical reviewer specializing in critical mineral supply chains and mining industry analysis."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=16000,  # Large enough for full reports
                    temperature=0.1,   # Low temperature for consistency
                    timeout=180        # 3 minute timeout
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"API call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise
    
    def review_single_report(self, metal_name: str, dry_run: bool = False, 
                           create_backup: bool = True) -> bool:
        """Review and reformat a single metal report."""
        
        # Normalize metal name
        metal_name_clean = metal_name.lower().strip()
        report_path = self.reports_dir / f"{metal_name_clean}_report.md"
        
        if not report_path.exists():
            print(f"❌ Report not found: {report_path}")
            return False
        
        # Check if we have critique for this metal
        if metal_name_clean not in self.fact_check_critiques:
            print(f"⚠️  No fact-check critique found for: {metal_name_clean}")
            return False
        
        print(f"\n🔍 Reviewing {metal_name_clean} report...")
        
        # Load original report
        original_content = report_path.read_text(encoding='utf-8')
        critique = self.fact_check_critiques[metal_name_clean]
        
        print(f"   Original report: {len(original_content):,} characters")
        print(f"   Critique: {len(critique):,} characters")
        
        if dry_run:
            print("   [DRY RUN] Would call AI model for review")
            return True
        
        # Create backup if requested
        if create_backup:
            backup_path = self._create_backup(report_path)
            print(f"   📁 Created backup: {backup_path}")
        
        # Build prompt and call AI
        try:
            prompt = self._build_review_prompt(original_content, critique, metal_name_clean)
            print(f"   🤖 Calling {self.model_name}...")
            
            revised_content = self._call_ai_model(prompt)
            
            print(f"   ✅ Received revised report: {len(revised_content):,} characters")
            
            # Write revised report
            report_path.write_text(revised_content, encoding='utf-8')
            print(f"   💾 Updated: {report_path}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error processing {metal_name_clean}: {e}")
            return False
    
    def review_all_reports(self, dry_run: bool = False, create_backup: bool = True) -> Dict[str, bool]:
        """Review and reformat all available reports."""
        
        results = {}
        
        # Get all metals that have both reports and critiques
        available_metals = set()
        for report_file in self.reports_dir.glob("*_report.md"):
            metal = report_file.stem.replace("_report", "")
            if metal in self.fact_check_critiques:
                available_metals.add(metal)
        
        if not available_metals:
            print("No metals found with both reports and critiques")
            return results
        
        print(f"Found {len(available_metals)} metals to process:")
        for metal in sorted(available_metals):
            print(f"  • {metal}")
        
        # Process each metal
        for metal in sorted(available_metals):
            results[metal] = self.review_single_report(
                metal, dry_run=dry_run, create_backup=create_backup
            )
            
            # Small delay to be respectful to API
            if not dry_run:
                time.sleep(1)
        
        # Print summary
        successful = sum(1 for success in results.values() if success)
        print(f"\n📊 Summary: {successful}/{len(results)} reports processed successfully")
        
        return results
    
    def list_available_metals(self) -> Tuple[List[str], List[str], List[str]]:
        """List available metals categorized by data availability."""
        
        # Get all report files
        report_metals = set()
        for report_file in self.reports_dir.glob("*_report.md"):
            metal = report_file.stem.replace("_report", "")
            report_metals.add(metal)
        
        # Get all critique metals
        critique_metals = set(self.fact_check_critiques.keys())
        
        # Categorize
        both = sorted(report_metals & critique_metals)
        report_only = sorted(report_metals - critique_metals)
        critique_only = sorted(critique_metals - report_metals)
        
        return both, report_only, critique_only


def main():
    """Main function with command line interface."""
    
    parser = argparse.ArgumentParser(
        description="Review and reformat critical mineral reports using fact-checking feedback"
    )
    
    parser.add_argument(
        "--metal", 
        help="Process only this specific metal (e.g., 'aluminum')"
    )
    
    parser.add_argument(
        "--model", 
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be processed without making API calls"
    )
    
    parser.add_argument(
        "--no-backup", 
        action="store_true",
        help="Skip creating backup files"
    )
    
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List available metals and their data status"
    )
    
    args = parser.parse_args()
    
    try:
        reviewer = ReportReviewer(model_name=args.model)
        
        if args.list:
            both, report_only, critique_only = reviewer.list_available_metals()
            
            print("\n📋 Metal Data Status:")
            print(f"\n✅ Ready for processing ({len(both)} metals):")
            for metal in both:
                print(f"   • {metal}")
            
            print(f"\n📄 Reports only - no critique ({len(report_only)} metals):")
            for metal in report_only:
                print(f"   • {metal}")
            
            print(f"\n🔍 Critiques only - no report ({len(critique_only)} metals):")
            for metal in critique_only:
                print(f"   • {metal}")
            
            return
        
        create_backup = not args.no_backup
        
        if args.metal:
            # Process single metal
            success = reviewer.review_single_report(
                args.metal, 
                dry_run=args.dry_run, 
                create_backup=create_backup
            )
            exit(0 if success else 1)
        else:
            # Process all metals
            results = reviewer.review_all_reports(
                dry_run=args.dry_run, 
                create_backup=create_backup
            )
            
            failed = [metal for metal, success in results.items() if not success]
            if failed:
                print(f"\n⚠️  Failed metals: {', '.join(failed)}")
                exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
        exit(130)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()