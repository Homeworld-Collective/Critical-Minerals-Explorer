#!/usr/bin/env python3
"""
Critical Metals MSHA Analysis - Main Entry Point

This script runs the complete analysis of 64 critical metals using MSHA data.
It will automatically download data if needed and generate all output files.

Usage:
    python run_analysis.py

Output:
    - critical_metals_analysis/consolidated_tables/ - Individual metal analysis files
    - critical_metals_analysis/summary_reports/ - Summary reports and analysis
"""

import sys
from pathlib import Path
import logging

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from msha_data_downloader import MSHADataDownloader
from critical_metals_analyzer import CriticalMetalsAnalyzer

def main():
    """Main analysis pipeline"""
    print("="*80)
    print("CRITICAL METALS MSHA ANALYSIS")
    print("="*80)
    print("This analysis will:")
    print("• Download/verify MSHA data")
    print("• Analyze 63 critical metals") 
    print("• Generate production estimates")
    print("• Create consolidated tables and reports")
    print("="*80)
    
    # Step 1: Ensure MSHA data is available
    print("\n1. Checking MSHA data availability...")
    downloader = MSHADataDownloader()
    
    mines_file = Path("msha_critical_metals_analysis/raw_data/msha_mines_database/Mines.txt")
    if not mines_file.exists():
        print("   Downloading MSHA mines database...")
        if not downloader.download_dataset('mines'):
            print("   ERROR: Failed to download MSHA data")
            return False
    else:
        print(f"   ✓ MSHA mines data available ({mines_file.stat().st_size:,} bytes)")
    
    # Optional: Download production data for enhanced analysis
    prod_dir = Path("msha_critical_metals_analysis/raw_data/msha_production_data")
    if not prod_dir.exists():
        print("   Downloading quarterly production data (optional)...")
        downloader.download_dataset('quarterly_prod')
    
    # Step 2: Run critical metals analysis
    print("\n2. Running critical metals analysis...")
    analyzer = CriticalMetalsAnalyzer()
    
    try:
        results_df, successful_metals = analyzer.analyze_all_metals()
        
        if results_df is not None and not results_df.empty:
            print(f"\n3. Analysis completed successfully!")
            print(f"   ✓ Analyzed {len(analyzer.metal_configs)} critical metals")
            print(f"   ✓ Generated files for {len(successful_metals)} metals with active operations")
            
            # Show summary
            active_results = results_df[results_df['active_mines'] > 0]
            if not active_results.empty:
                total_production = active_results['total_estimated_production_mt_per_year'].sum()
                total_employment = active_results['total_employment'].sum()
                print(f"   ✓ Total estimated production: {total_production:,.0f} MT/year")
                print(f"   ✓ Total employment: {total_employment:,.0f} workers")
            
            print(f"\n4. Output files created:")
            print(f"   • Individual metal tables: msha_critical_metals_analysis/analysis_results/individual_metals/")
            print(f"   • Summary reports: msha_critical_metals_analysis/analysis_results/summary_reports/")
            print(f"   • Main summary: msha_critical_metals_analysis/analysis_results/summary_reports/metals_summary.csv")
            
            return True
        else:
            print("   ERROR: Analysis failed to produce results")
            return False
            
    except Exception as e:
        print(f"   ERROR: Analysis failed: {e}")
        logging.exception("Analysis error")
        return False

if __name__ == "__main__":
    # Configure logging for any errors
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='critical_metals_analysis.log'
    )
    
    success = main()
    
    if success:
        print("\n" + "="*80)
        print("ANALYSIS COMPLETED SUCCESSFULLY")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80) 
        print("ANALYSIS FAILED - Check critical_metals_analysis.log for details")
        print("="*80)
        sys.exit(1)