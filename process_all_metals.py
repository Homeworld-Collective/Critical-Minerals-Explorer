"""
process_all_metals.py
---------------------
Batch process all critical minerals except aluminum to generate reports.
"""

import os
import subprocess
import sys
from pathlib import Path
import time

def get_metal_list():
    """Get list of all metals from CSV files, excluding aluminum."""
    consolidated_dir = Path("msha_scraper/msha_critical_metals_analysis/analysis_results/individual_metals")
    
    metals = []
    for csv_file in consolidated_dir.glob("*_analysis.csv"):
        metal_name = csv_file.stem.replace("_analysis", "")
        if metal_name != "aluminum":  # Skip aluminum as it's already done
            metals.append(metal_name)
    
    return sorted(metals)

def run_metal_analysis(metal_name, total_count, current_index):
    """Run the analysis for a single metal."""
    print(f"\n{'='*60}")
    print(f"Processing {metal_name.upper()} ({current_index}/{total_count})")
    print(f"{'='*60}")
    print(f"Starting analysis for {metal_name}...")
    
    try:
        # Run the analysis script with real-time output
        result = subprocess.run([
            sys.executable, "generate_metal_report.py", metal_name
        ], timeout=7200)  # 2 hour timeout, no capture_output so we see real-time output
        
        if result.returncode == 0:
            print(f"✅ Successfully processed {metal_name}")
            return True
        else:
            print(f"❌ Failed to process {metal_name} (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout processing {metal_name} (2 hours)")
        return False
    except KeyboardInterrupt:
        print(f"🛑 Processing interrupted for {metal_name}")
        raise
    except Exception as e:
        print(f"💥 Exception processing {metal_name}: {e}")
        return False

def get_completed_metals():
    """Get list of metals that have already been processed."""
    reports_dir = Path("detailed_reports")
    if not reports_dir.exists():
        return []
    
    completed = []
    for report_file in reports_dir.glob("*_report.md"):
        metal_name = report_file.stem.replace("_report", "")
        if metal_name != "aluminum":  # aluminum was done separately
            completed.append(metal_name)
    
    return completed

def main():
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Get list of metals to process
    all_metals = get_metal_list()
    completed_metals = get_completed_metals()
    metals_to_process = [m for m in all_metals if m not in completed_metals]
    
    print(f"Total metals: {len(all_metals)}")
    print(f"Already completed: {len(completed_metals)} - {', '.join(completed_metals)}")
    print(f"Remaining to process: {len(metals_to_process)}")
    
    if not metals_to_process:
        print("🎉 All metals have already been processed!")
        return
        
    print(f"\nMetals to process:")
    for i, metal in enumerate(metals_to_process, 1):
        print(f"  {i:2d}. {metal}")
    
    # Create detailed_reports directory if it doesn't exist
    Path("detailed_reports").mkdir(exist_ok=True)
    
    # Process each metal
    total_count = len(metals_to_process)
    success_count = 0
    failed_metals = []
    
    start_time = time.time()
    
    for i, metal in enumerate(metals_to_process, 1):
        success = run_metal_analysis(metal, total_count, i)
        if success:
            success_count += 1
        else:
            failed_metals.append(metal)
        
        # Add delay between requests to be respectful to the API
        if i < total_count:
            print("Waiting 30 seconds before next metal...")
            time.sleep(30)
    
    # Summary
    end_time = time.time()
    elapsed_hours = (end_time - start_time) / 3600
    
    print(f"\n{'='*60}")
    print(f"BATCH PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total metals: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_metals)}")
    print(f"Total time: {elapsed_hours:.2f} hours")
    
    if failed_metals:
        print(f"\nFailed metals: {', '.join(failed_metals)}")
        
        # Create a retry script for failed metals
        retry_script = Path("retry_failed_metals.py")
        retry_content = f'''#!/usr/bin/env python3
"""Retry script for failed metals"""
import subprocess
import sys

failed_metals = {failed_metals}

for metal in failed_metals:
    print(f"Retrying {{metal}}...")
    result = subprocess.run([sys.executable, "generate_metal_report.py", metal])
    if result.returncode != 0:
        print(f"Failed again: {{metal}}")
'''
        retry_script.write_text(retry_content)
        print(f"Created retry script: {retry_script}")

if __name__ == "__main__":
    main()
