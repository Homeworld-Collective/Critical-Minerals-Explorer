#!/usr/bin/env python3
"""
Generate MSHA analysis for the 4 missing metals: cadmium, rhenium, selenium, strontium
"""

import sys
import os
from pathlib import Path

# Change to msha_scraper directory for correct data paths
os.chdir(Path(__file__).parent / "msha_scraper")

# Add current directory to path for imports
sys.path.insert(0, ".")

from critical_metals_analyzer import CriticalMetalsAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Generate analysis files for missing metals"""
    missing_metals = ['cadmium', 'rhenium', 'selenium', 'strontium']
    
    print("="*80)
    print(f"GENERATING MISSING METAL ANALYSIS FILES")
    print("="*80)
    print(f"Missing metals: {', '.join(missing_metals)}")
    print("="*80)
    
    analyzer = CriticalMetalsAnalyzer()
    
    # Load MSHA data
    if not analyzer.load_msha_data():
        print("ERROR: Failed to load MSHA data")
        return False
    
    successful_metals = []
    
    for metal in missing_metals:
        try:
            print(f"\n--- Processing {metal.upper()} ---")
            
            # Find mines
            metal_mines = analyzer.find_metal_mines(metal)
            
            # Calculate production for active mines
            production_df = analyzer.calculate_production_estimates(metal_mines, metal)
            
            # Create summary
            summary = {
                'metal': metal,
                'total_mines_identified': len(metal_mines),
                'active_mines': len(production_df),
                'total_estimated_production_mt_per_year': production_df['estimated_annual_production_mt'].sum() if not production_df.empty else 0,
                'total_employment': production_df['employees'].sum() if not production_df.empty else 0,
                'confidence_level': analyzer.metal_configs[metal]['confidence'],
                'method': analyzer.metal_configs[metal]['method'],
                'notes': analyzer.metal_configs[metal]['notes']
            }
            
            # Always save files, even if no active mines found
            output_file = analyzer.consolidated_dir / f"{metal}_analysis.csv"
            
            if not production_df.empty:
                production_df.to_csv(output_file, index=False)
                print(f"✓ {metal}: {summary['active_mines']} active mines, {summary['total_estimated_production_mt_per_year']:,.0f} MT/year")
                
                # Show operations
                for _, mine in production_df.iterrows():
                    print(f"    {mine['mine_name'][:30]:<30} | {mine['state']} | {mine['estimated_annual_production_mt']:>8,.0f} MT/yr")
            else:
                # Create empty CSV with headers for consistency
                import pandas as pd
                empty_df = pd.DataFrame(columns=[
                    'rank', 'mine_id', 'mine_name', 'state', 'status', 'mine_type', 'operator',
                    'primary_sic', 'employees', 'estimated_annual_production_mt', 
                    'production_factor_mt_per_employee', 'confidence_level', 'longitude', 
                    'latitude', 'metal', 'verification_method', 'verification_notes'
                ])
                
                # Add one row indicating no active mines
                empty_df.loc[0] = [
                    1, '', f'No active {metal} mines in US', '', 'No Production', '', '',
                    '', 0, 0, 0, summary['confidence_level'], '', '', metal, 
                    summary['method'], summary['notes']
                ]
                
                empty_df.to_csv(output_file, index=False)
                print(f"✓ {metal}: No active mines found")
            
            # Save detailed JSON
            import json
            from datetime import datetime
            
            json_file = analyzer.consolidated_dir / f"{metal}_detailed.json"
            with open(json_file, 'w') as f:
                json.dump({
                    'metal': metal,
                    'analysis_date': datetime.now().isoformat(),
                    'summary': summary,
                    'mines': production_df.to_dict('records') if not production_df.empty else []
                }, f, indent=2, default=str)
            
            successful_metals.append(metal)
            print(f"✓ Generated files: {output_file.name} and {json_file.name}")
            
        except Exception as e:
            logger.error(f"Error processing {metal}: {e}")
            continue
    
    print(f"\n{'='*80}")
    print("MISSING METALS ANALYSIS COMPLETE")
    print(f"Successfully generated files for: {', '.join(successful_metals)}")
    print(f"Output directory: {analyzer.consolidated_dir}/")
    print("="*80)
    
    return len(successful_metals) == len(missing_metals)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)