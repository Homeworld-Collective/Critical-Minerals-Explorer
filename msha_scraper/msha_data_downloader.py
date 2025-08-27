#!/usr/bin/env python3
"""
MSHA Data Downloader - Downloads and processes actual MSHA datasets

This module downloads real MSHA data from their Open Government Data portal
and processes it to extract commodity-specific information.
"""

import requests
import pandas as pd
import zipfile
import io
import os
from typing import List, Dict, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MSHADataDownloader:
    """
    Downloads and processes MSHA datasets from official sources
    """
    
    def __init__(self, data_dir: str = "msha_critical_metals_analysis/raw_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # MSHA Open Government Data URLs
        self.data_urls = {
            'mines': 'https://arlweb.msha.gov/OpenGovernmentData/DataSets/Mines.zip',
            'quarterly_prod': 'https://www.msha.gov/OpenGovernmentData/DataSets/MinesProdQuarterly.zip',
            'contractor_prod': 'https://www.msha.gov/OpenGovernmentData/DataSets/ContractorProdQuarterly.zip',
            'violations': 'https://www.msha.gov/OpenGovernmentData/DataSets/Violations.zip',
            'accidents': 'https://www.msha.gov/OpenGovernmentData/DataSets/Accidents.zip'
        }
    
    def download_dataset(self, dataset_name: str) -> bool:
        """
        Download a specific MSHA dataset
        
        Args:
            dataset_name: Name of dataset ('mines', 'quarterly_prod', 'violations', 'accidents')
            
        Returns:
            True if successful, False otherwise
        """
        if dataset_name not in self.data_urls:
            logger.error(f"Unknown dataset: {dataset_name}")
            return False
        
        url = self.data_urls[dataset_name]
        logger.info(f"Downloading {dataset_name} from {url}")
        
        try:
            response = self.session.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            zip_path = self.data_dir / f"{dataset_name}.zip"
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract the ZIP file  
            if dataset_name == 'mines':
                extract_dir = self.data_dir / 'msha_mines_database'
            elif dataset_name == 'quarterly_prod':
                extract_dir = self.data_dir / 'msha_production_data'
            else:
                extract_dir = self.data_dir / dataset_name
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Clean up - delete the ZIP file after successful extraction
            zip_path.unlink()
            logger.info(f"Successfully downloaded, extracted, and cleaned up {dataset_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {dataset_name}: {e}")
            return False
    
    def load_mines_data(self) -> pd.DataFrame:
        """
        Load the mines dataset
        
        Returns:
            DataFrame with mine information
        """
        mines_dir = self.data_dir / 'msha_mines_database'
        if not mines_dir.exists():
            logger.info("Mines data not found, downloading...")
            if not self.download_dataset('mines'):
                return pd.DataFrame()
        
        # Find the main mines data file (CSV or TXT)
        data_files = list(mines_dir.glob('*.csv')) + list(mines_dir.glob('*.txt'))
        if not data_files:
            logger.error("No data files found in mines data")
            return pd.DataFrame()
        
        # Load the largest data file (likely the main dataset)
        main_file = max(data_files, key=lambda f: f.stat().st_size)
        logger.info(f"Loading mines data from {main_file}")
        
        try:
            # Try different encodings
            encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings_to_try:
                try:
                    with open(main_file, 'r', encoding=encoding) as f:
                        first_line = f.readline()
                    
                    separator = '|' if '|' in first_line else ','
                    
                    df = pd.read_csv(main_file, sep=separator, encoding=encoding, low_memory=False)
                    logger.info(f"Loaded {len(df)} mine records using encoding: {encoding}")
                    return df
                except UnicodeDecodeError:
                    continue
            
            logger.error("Failed to load mines data with any encoding")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Failed to load mines data: {e}")
            return pd.DataFrame()
    
    def load_production_data(self) -> pd.DataFrame:
        """
        Load the quarterly production dataset
        
        Returns:
            DataFrame with production data
        """
        prod_dir = self.data_dir / 'msha_production_data'
        if not prod_dir.exists():
            logger.info("Production data not found, downloading...")
            if not self.download_dataset('quarterly_prod'):
                return pd.DataFrame()
        
        # Find production data files (CSV or TXT)
        data_files = list(prod_dir.glob('*.csv')) + list(prod_dir.glob('*.txt'))
        if not data_files:
            logger.error("No data files found in production data")
            return pd.DataFrame()
        
        main_file = max(data_files, key=lambda f: f.stat().st_size)
        logger.info(f"Loading production data from {main_file}")
        
        try:
            # Try different encodings
            encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings_to_try:
                try:
                    with open(main_file, 'r', encoding=encoding) as f:
                        first_line = f.readline()
                    
                    separator = '|' if '|' in first_line else ','
                    
                    df = pd.read_csv(main_file, sep=separator, encoding=encoding, low_memory=False)
                    logger.info(f"Loaded {len(df)} production records using encoding: {encoding}")
                    return df
                except UnicodeDecodeError:
                    continue
            
            logger.error("Failed to load production data with any encoding")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Failed to load production data: {e}")
            return pd.DataFrame()
    
    def find_commodity_mines(self, commodity: str, mines_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Find mines that produce a specific commodity
        
        Args:
            commodity: Commodity to search for (e.g., 'aluminum', 'nickel')
            mines_df: Optional pre-loaded mines DataFrame
            
        Returns:
            DataFrame with matching mines
        """
        if mines_df is None:
            mines_df = self.load_mines_data()
        
        if mines_df.empty:
            return pd.DataFrame()
        
        # Search in multiple columns for commodity mentions
        commodity_lower = commodity.lower()
        search_columns = []
        
        # Identify columns that might contain commodity information
        for col in mines_df.columns:
            if any(term in col.lower() for term in ['commodity', 'product', 'material', 'type']):
                search_columns.append(col)
        
        if not search_columns:
            # If no specific commodity columns found, search in all string columns
            search_columns = [col for col in mines_df.columns if mines_df[col].dtype == 'object']
        
        logger.info(f"Searching for {commodity} in columns: {search_columns}")
        
        # Create boolean mask for commodity matches
        mask = pd.Series([False] * len(mines_df))
        
        for col in search_columns:
            if col in mines_df.columns:
                col_mask = mines_df[col].astype(str).str.lower().str.contains(
                    commodity_lower, na=False, regex=False
                )
                mask |= col_mask
        
        matching_mines = mines_df[mask]
        logger.info(f"Found {len(matching_mines)} mines producing {commodity}")
        
        return matching_mines
    
    def get_production_summary(self, mine_ids: List[str], production_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Get production summary for specific mines
        
        Args:
            mine_ids: List of MSHA mine IDs
            production_df: Optional pre-loaded production DataFrame
            
        Returns:
            DataFrame with production summary
        """
        if production_df is None:
            production_df = self.load_production_data()
        
        if production_df.empty:
            return pd.DataFrame()
        
        # Filter production data for specified mines
        mine_production = production_df[production_df['MINE_ID'].isin(mine_ids)]
        
        if mine_production.empty:
            logger.warning("No production data found for specified mines")
            return pd.DataFrame()
        
        logger.info(f"Found production data for {len(mine_production)} records")
        return mine_production
    
    def analyze_commodity_production(self, commodity: str, years: Optional[List[int]] = None) -> Dict:
        """
        Analyze production trends for a specific commodity
        
        Args:
            commodity: Commodity name
            years: Optional list of years to analyze
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Analyzing {commodity} production trends")
        
        # Load data
        mines_df = self.load_mines_data()
        production_df = self.load_production_data()
        
        if mines_df.empty or production_df.empty:
            return {}
        
        # Find commodity mines
        commodity_mines = self.find_commodity_mines(commodity, mines_df)
        
        if commodity_mines.empty:
            logger.warning(f"No mines found for commodity: {commodity}")
            return {}
        
        mine_ids = commodity_mines['MINE_ID'].tolist()
        
        # Get production data
        production_data = self.get_production_summary(mine_ids, production_df)
        
        if production_data.empty:
            return {}
        
        # Filter by years if specified
        if years and 'CAL_YR' in production_data.columns:
            production_data = production_data[production_data['CAL_YR'].isin(years)]
        
        # Analyze trends
        analysis = {
            'commodity': commodity,
            'total_mines': len(commodity_mines),
            'active_mines': len(commodity_mines[commodity_mines.get('CURRENT_STATUS_CD', '') == 'A']),
            'total_records': len(production_data),
            'years_covered': sorted(production_data['CAL_YR'].unique()) if 'CAL_YR' in production_data.columns else [],
            'states': commodity_mines['STATE'].value_counts().to_dict() if 'STATE' in commodity_mines.columns else {},
            'mine_details': commodity_mines.to_dict('records')[:10]  # First 10 mines
        }
        
        return analysis

def main():
    """
    Example usage of MSHA Data Downloader
    """
    downloader = MSHADataDownloader()
    
    # Analyze aluminum production
    print("Analyzing Aluminum mining...")
    aluminum_analysis = downloader.analyze_commodity_production('aluminum')
    
    if aluminum_analysis:
        print(f"Found {aluminum_analysis['total_mines']} aluminum-related mines")
        print(f"States with aluminum mines: {list(aluminum_analysis['states'].keys())}")
        print(f"Years with data: {aluminum_analysis['years_covered']}")
    
    # Analyze nickel production
    print("\nAnalyzing Nickel mining...")
    nickel_analysis = downloader.analyze_commodity_production('nickel')
    
    if nickel_analysis:
        print(f"Found {nickel_analysis['total_mines']} nickel-related mines")
        print(f"States with nickel mines: {list(nickel_analysis['states'].keys())}")
        print(f"Years with data: {nickel_analysis['years_covered']}")
    
    # Export analysis results
    if aluminum_analysis:
        import json
        with open('aluminum_mining_analysis.json', 'w') as f:
            json.dump(aluminum_analysis, f, indent=2, default=str)
        print("Aluminum analysis saved to aluminum_mining_analysis.json")
    
    if nickel_analysis:
        import json
        with open('nickel_mining_analysis.json', 'w') as f:
            json.dump(nickel_analysis, f, indent=2, default=str)
        print("Nickel analysis saved to nickel_mining_analysis.json")

if __name__ == "__main__":
    main()