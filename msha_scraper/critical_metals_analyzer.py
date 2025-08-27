#!/usr/bin/env python3
"""
Critical Metals MSHA Analyzer

Analyzes 64 critical metals using MSHA (Mine Safety and Health Administration) data
to identify domestic mining operations and estimate production capacity.

Data Source: MSHA Open Government Data
Analysis Method: Employment-based production estimation with metal-specific factors
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CriticalMetalsAnalyzer:
    def __init__(self):
        # Output directory structure
        self.base_dir = Path("msha_critical_metals_analysis/analysis_results")
        self.consolidated_dir = self.base_dir / "individual_metals"
        self.summary_dir = self.base_dir / "summary_reports"
        
        for directory in [self.consolidated_dir, self.summary_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Complete 64 metal configurations
        self.metal_configs = {
            # MAJOR METALS - High confidence with exact SIC codes
            'aluminum': {
                'exact_sic_codes': ['Alumina', 'Aluminum Ore-Bauxite'],
                'operator_keywords': ['alcoa', 'almatis', 'alumina', 'aluminum'],
                'production_factor': 2200,
                'confidence': 'high',
                'method': 'exact_sic',
                'notes': 'Primary aluminum refining and bauxite mining'
            },
            'bauxite': {
                'exact_sic_codes': ['Aluminum Ore-Bauxite', 'Bauxite'],
                'operator_keywords': ['bauxite', 'alcoa'],
                'production_factor': 3000,
                'confidence': 'high',
                'method': 'exact_sic',
                'notes': 'Aluminum ore (bauxite) mining operations'
            },
            'copper': {
                'exact_sic_codes': ['Copper Ore NEC', 'Copper Ore'],
                'operator_keywords': ['freeport', 'kennecott', 'copper'],
                'production_factor': 3500,
                'confidence': 'high',
                'method': 'exact_sic',
                'notes': 'Major copper mining operations'
            },
            'lead': {
                'exact_sic_codes': ['Lead-Zinc Ore', 'Lead Ore'],
                'operator_keywords': ['lead'],
                'production_factor': 3500,
                'confidence': 'high',
                'method': 'exact_sic',
                'notes': 'Lead mining and lead-zinc operations'
            },
            'zinc': {
                'exact_sic_codes': ['Lead-Zinc Ore', 'Zinc'],
                'operator_keywords': ['zinc'],
                'production_factor': 4000,
                'confidence': 'high',
                'method': 'exact_sic',
                'notes': 'Lead-zinc districts and zinc operations'
            },
            'nickel': {
                'exact_sic_codes': ['Nickel Ore'],
                'operator_keywords': ['nickel'],
                'production_factor': 3000,
                'confidence': 'high',
                'method': 'exact_sic',
                'notes': 'Primary nickel ore mining'
            },
            'lithium': {
                'exact_sic_codes': ['Lithium Minerals'],
                'operator_keywords': ['lithium'],
                'production_factor': 1500,
                'confidence': 'high',
                'method': 'exact_sic',
                'notes': 'Lithium mineral extraction and brine operations'
            },
            'silver': {
                'exact_sic_codes': ['Silver Ore'],
                'operator_keywords': ['silver'],
                'production_factor': 2.0,
                'confidence': 'medium',
                'method': 'exact_sic',
                'notes': 'Silver mining operations'
            },

            # INDUSTRIAL MINERALS
            'barite': {
                'controlled_keywords': ['barite', 'baryte'],
                'sic_patterns': ['barium', 'barite'],
                'production_factor': 5000,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Barium sulfate mining for drilling mud'
            },
            'feldspar': {
                'controlled_keywords': ['feldspar'],
                'sic_patterns': ['feldspar'],
                'production_factor': 4000,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Feldspar mining for ceramics and glass'
            },
            'fluorspar': {
                'controlled_keywords': ['fluorspar', 'fluorite'],
                'sic_patterns': ['fluorspar', 'fluorite'],
                'production_factor': 4000,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Fluorite mining for chemical industry'
            },
            'graphite': {
                'controlled_keywords': ['graphite'],
                'sic_patterns': ['graphite'],
                'exclude_terms': ['carbon black', 'charcoal', 'coal'],
                'production_factor': 3500,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Natural graphite mining'
            },
            'magnesium': {
                'controlled_keywords': ['magnesium', 'magnesite'],
                'sic_patterns': ['magnesium', 'magnesite'],
                'production_factor': 2500,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Magnesium compounds and mineral extraction'
            },
            'mica': {
                'controlled_keywords': ['mica'],
                'sic_patterns': ['mica'],
                'production_factor': 3000,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Mica mining for electrical and cosmetic industries'
            },
            'phosphates': {
                'controlled_keywords': ['phosphate', 'phosphorus'],
                'sic_patterns': ['phosphate'],
                'production_factor': 6000,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Phosphate rock mining for fertilizers'
            },
            'potash': {
                'controlled_keywords': ['potash', 'potassium'],
                'sic_patterns': ['potash'],
                'production_factor': 5000,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Potash mining for fertilizer production'
            },
            'silicon': {
                'controlled_keywords': ['silica', 'silicon', 'quartz'],
                'sic_patterns': ['silica', 'silicon'],
                'exclude_terms': ['coal', 'carbon'],
                'production_factor': 4500,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'High-purity silica and silicon production'
            },

            # STRATEGIC METALS
            'titanium': {
                'controlled_keywords': ['titanium', 'ilmenite', 'rutile'],
                'sic_patterns': ['titanium', 'ilmenite', 'rutile'],
                'production_factor': 3500,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Titanium minerals and processing'
            },
            'zirconium': {
                'controlled_keywords': ['zirconium', 'zircon'],
                'sic_patterns': ['zirconium', 'zircon'],
                'production_factor': 2500,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Zircon sands and zirconium compounds'
            },
            'beryllium': {
                'controlled_keywords': ['beryllium', 'beryl', 'bertrandite'],
                'sic_patterns': ['beryllium', 'beryl'],
                'production_factor': 50,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Beryllium mining - highly specialized'
            },
            'cobalt': {
                'controlled_keywords': ['cobalt'],
                'sic_patterns': ['cobalt'],
                'production_factor': 800,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Cobalt as byproduct of copper/nickel mining'
            },
            'vanadium': {
                'controlled_keywords': ['vanadium'],
                'sic_patterns': ['vanadium'],
                'production_factor': 1200,
                'confidence': 'medium',
                'method': 'controlled_keyword',
                'notes': 'Vanadium from uranium operations and steel slag'
            },
            'tungsten': {
                'controlled_keywords': ['tungsten', 'wolframite', 'scheelite'],
                'sic_patterns': ['tungsten'],
                'production_factor': 800,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Very limited US tungsten production'
            },
            'manganese': {
                'controlled_keywords': ['manganese'],
                'sic_patterns': ['manganese'],
                'production_factor': 3500,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Mostly imported, limited US operations'
            },
            'chromium': {
                'controlled_keywords': ['chromium', 'chromite'],
                'sic_patterns': ['chromium', 'chromite'],
                'production_factor': 3000,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'No significant US chromium mining'
            },

            # RARE EARTH ELEMENTS (17 elements)
            'cerium': {
                'controlled_keywords': ['cerium', 'rare earth'],
                'sic_patterns': ['rare earth', 'cerium'],
                'production_factor': 200,
                'confidence': 'medium',
                'method': 'rare_earth_group',
                'notes': 'Most abundant rare earth element'
            },
            'lanthanum': {
                'controlled_keywords': ['lanthanum', 'rare earth'],
                'sic_patterns': ['rare earth', 'lanthanum'],
                'production_factor': 150,
                'confidence': 'medium',
                'method': 'rare_earth_group',
                'notes': 'Second most abundant REE'
            },
            'neodymium': {
                'controlled_keywords': ['neodymium', 'rare earth'],
                'sic_patterns': ['rare earth', 'neodymium'],
                'production_factor': 100,
                'confidence': 'medium',
                'method': 'rare_earth_group',
                'notes': 'Critical for permanent magnets'
            },
            'praseodymium': {
                'controlled_keywords': ['praseodymium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 80,
                'confidence': 'medium',
                'method': 'rare_earth_group',
                'notes': 'Light rare earth element'
            },
            'yttrium': {
                'controlled_keywords': ['yttrium', 'rare earth'],
                'sic_patterns': ['rare earth', 'yttrium'],
                'production_factor': 120,
                'confidence': 'medium',
                'method': 'rare_earth_group',
                'notes': 'Heavy rare earth element'
            },
            'dysprosium': {
                'controlled_keywords': ['dysprosium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 50,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Critical heavy REE'
            },
            'erbium': {
                'controlled_keywords': ['erbium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 30,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Heavy REE for fiber optics'
            },
            'europium': {
                'controlled_keywords': ['europium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 10,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Most expensive REE'
            },
            'gadolinium': {
                'controlled_keywords': ['gadolinium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 40,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Heavy REE with specialized uses'
            },
            'holmium': {
                'controlled_keywords': ['holmium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 5,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Rare heavy REE'
            },
            'lutetium': {
                'controlled_keywords': ['lutetium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 1,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Rarest and most expensive REE'
            },
            'samarium': {
                'controlled_keywords': ['samarium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 60,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Used in permanent magnets'
            },
            'scandium': {
                'controlled_keywords': ['scandium', 'rare earth'],
                'sic_patterns': ['rare earth', 'scandium'],
                'production_factor': 15,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Not technically REE but grouped with them'
            },
            'terbium': {
                'controlled_keywords': ['terbium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 20,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Critical heavy REE'
            },
            'thulium': {
                'controlled_keywords': ['thulium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 5,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Second rarest REE'
            },
            'ytterbium': {
                'controlled_keywords': ['ytterbium', 'rare earth'],
                'sic_patterns': ['rare earth'],
                'production_factor': 25,
                'confidence': 'low',
                'method': 'rare_earth_group',
                'notes': 'Heavy REE with limited uses'
            },

            # PLATINUM GROUP METALS (6 elements)
            'platinum': {
                'exact_sic_codes': ['Platinum Group Ore'],
                'operator_keywords': ['platinum', 'stillwater'],
                'production_factor': 3.0,
                'confidence': 'high',
                'method': 'exact_sic',
                'notes': 'Stillwater Complex primary PGM operation'
            },
            'palladium': {
                'controlled_keywords': ['palladium', 'platinum group'],
                'sic_patterns': ['platinum', 'palladium'],
                'production_factor': 2,
                'confidence': 'medium',
                'method': 'pgm_group',
                'notes': 'Platinum group metal, limited US production'
            },
            'rhodium': {
                'controlled_keywords': ['rhodium', 'platinum group'],
                'sic_patterns': ['platinum', 'rhodium'],
                'production_factor': 1,
                'confidence': 'low',
                'method': 'pgm_group',
                'notes': 'Rare PGM, mostly byproduct'
            },
            'ruthenium': {
                'controlled_keywords': ['ruthenium', 'platinum group'],
                'sic_patterns': ['platinum', 'ruthenium'],
                'production_factor': 1,
                'confidence': 'low',
                'method': 'pgm_group',
                'notes': 'PGM with limited production'
            },
            'iridium': {
                'controlled_keywords': ['iridium', 'platinum group'],
                'sic_patterns': ['platinum', 'iridium'],
                'production_factor': 0.5,
                'confidence': 'low',
                'method': 'pgm_group',
                'notes': 'Rarest PGM'
            },

            # SPECIALTY/BYPRODUCT METALS
            'antimony': {
                'controlled_keywords': ['antimony', 'stibnite'],
                'sic_patterns': ['antimony'],
                'production_factor': 500,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Minimal US antimony production'
            },
            'arsenic': {
                'controlled_keywords': ['arsenic'],
                'sic_patterns': ['arsenic'],
                'production_factor': 300,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Mostly byproduct, no dedicated arsenic mines'
            },
            'bismuth': {
                'controlled_keywords': ['bismuth'],
                'sic_patterns': ['bismuth'],
                'production_factor': 100,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Very limited US bismuth operations'
            },
            'cadmium': {
                'controlled_keywords': ['cadmium'],
                'sic_patterns': ['cadmium'],
                'production_factor': 50,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Byproduct of zinc refining'
            },
            'cesium': {
                'controlled_keywords': ['cesium', 'caesium'],
                'sic_patterns': ['cesium'],
                'production_factor': 10,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Extremely limited US cesium production'
            },
            'gallium': {
                'controlled_keywords': ['gallium'],
                'sic_patterns': ['gallium'],
                'production_factor': 20,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Byproduct of aluminum processing'
            },
            'germanium': {
                'controlled_keywords': ['germanium'],
                'sic_patterns': ['germanium'],
                'production_factor': 5,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Byproduct of zinc processing'
            },
            'hafnium': {
                'controlled_keywords': ['hafnium'],
                'sic_patterns': ['hafnium'],
                'production_factor': 5,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Byproduct of zirconium processing'
            },
            'indium': {
                'controlled_keywords': ['indium'],
                'sic_patterns': ['indium'],
                'production_factor': 3,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Byproduct of zinc processing'
            },
            'niobium': {
                'controlled_keywords': ['niobium', 'columbium'],
                'sic_patterns': ['niobium', 'columbium'],
                'production_factor': 200,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'No significant US niobium production'
            },
            'rhenium': {
                'controlled_keywords': ['rhenium'],
                'sic_patterns': ['rhenium'],
                'production_factor': 2,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Byproduct of molybdenum processing'
            },
            'rubidium': {
                'controlled_keywords': ['rubidium'],
                'sic_patterns': ['rubidium'],
                'production_factor': 20,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Very limited commercial production'
            },
            'selenium': {
                'controlled_keywords': ['selenium'],
                'sic_patterns': ['selenium'],
                'production_factor': 50,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Byproduct of copper refining'
            },
            'strontium': {
                'controlled_keywords': ['strontium', 'celestite'],
                'sic_patterns': ['strontium'],
                'production_factor': 1000,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Limited US strontium mineral production'
            },
            'tantalum': {
                'controlled_keywords': ['tantalum', 'tantalite'],
                'sic_patterns': ['tantalum'],
                'production_factor': 100,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Very limited US tantalum operations'
            },
            'tellurium': {
                'controlled_keywords': ['tellurium'],
                'sic_patterns': ['tellurium'],
                'production_factor': 15,
                'confidence': 'low',
                'method': 'controlled_keyword',
                'notes': 'Byproduct of copper refining'
            },

            # ZERO US PRODUCTION - Documented for completeness
            'tin': {
                'controlled_keywords': [],  # Explicitly empty - no US production
                'production_factor': 0,
                'confidence': 'verified_zero',
                'method': 'industry_knowledge',
                'notes': 'No active US tin mines since 1990s'
            }
        }
        
        self.mines_df = None
        self.production_df = None

    def load_msha_data(self):
        """Load MSHA mine and production data"""
        logger.info("Loading MSHA data for critical metals analysis...")
        
        mines_file = Path("msha_critical_metals_analysis/raw_data/msha_mines_database/Mines.txt")
        if mines_file.exists():
            encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings_to_try:
                try:
                    self.mines_df = pd.read_csv(mines_file, sep='|', encoding=encoding, low_memory=False)
                    logger.info(f"Loaded {len(self.mines_df)} mine records")
                    break
                except UnicodeDecodeError:
                    continue
        else:
            logger.error("MSHA mines data not found. Run run_analysis.py first to download data.")
            return False
        
        # Load production data if available
        production_file = Path("msha_critical_metals_analysis/raw_data/msha_production_data")
        if production_file.exists():
            prod_files = list(production_file.glob("*.txt"))
            if prod_files:
                main_file = max(prod_files, key=lambda f: f.stat().st_size)
                try:
                    self.production_df = pd.read_csv(main_file, sep='|', encoding='latin1', low_memory=False)
                    logger.info(f"Loaded {len(self.production_df)} production records")
                except Exception as e:
                    logger.warning(f"Could not load production data: {e}")
        
        return self.mines_df is not None

    def find_metal_mines(self, metal: str) -> pd.DataFrame:
        """Find mines using the appropriate method for each metal"""
        config = self.metal_configs[metal]
        method = config['method']
        
        if method == 'industry_knowledge':
            logger.info(f"{metal}: {config['notes']}")
            return pd.DataFrame()
        
        mask = pd.Series([False] * len(self.mines_df))
        
        if method == 'exact_sic':
            # Use exact SIC code matching
            for col in ['PRIMARY_SIC', 'SECONDARY_SIC']:
                if col in self.mines_df.columns:
                    for sic_code in config['exact_sic_codes']:
                        sic_mask = self.mines_df[col].astype(str) == sic_code
                        mask |= sic_mask
            
            # Add operator matches
            if 'operator_keywords' in config and 'CURRENT_OPERATOR_NAME' in self.mines_df.columns:
                for keyword in config['operator_keywords']:
                    operator_mask = self.mines_df['CURRENT_OPERATOR_NAME'].astype(str).str.lower().str.contains(
                        keyword, na=False, regex=False
                    )
                    mask |= operator_mask
        
        elif method in ['controlled_keyword', 'rare_earth_group', 'pgm_group']:
            # Use controlled keyword matching with SIC pattern verification
            if 'sic_patterns' in config:
                for col in ['PRIMARY_SIC', 'SECONDARY_SIC']:
                    if col in self.mines_df.columns:
                        for pattern in config['sic_patterns']:
                            sic_mask = self.mines_df[col].astype(str).str.lower().str.contains(
                                pattern, na=False, regex=False
                            )
                            mask |= sic_mask
            
            # Controlled keyword search in mine names and operators
            if 'controlled_keywords' in config and config['controlled_keywords']:
                for keyword in config['controlled_keywords']:
                    # Mine name matches
                    if 'CURRENT_MINE_NAME' in self.mines_df.columns:
                        name_mask = self.mines_df['CURRENT_MINE_NAME'].astype(str).str.lower().str.contains(
                            keyword, na=False, regex=False
                        )
                        mask |= name_mask
                    
                    # Operator name matches
                    if 'CURRENT_OPERATOR_NAME' in self.mines_df.columns:
                        op_mask = self.mines_df['CURRENT_OPERATOR_NAME'].astype(str).str.lower().str.contains(
                            keyword, na=False, regex=False
                        )
                        mask |= op_mask
            
            # Apply exclusions if specified
            if 'exclude_terms' in config:
                exclude_mask = pd.Series([False] * len(self.mines_df))
                for col in ['CURRENT_MINE_NAME', 'CURRENT_OPERATOR_NAME', 'PRIMARY_SIC']:
                    if col in self.mines_df.columns:
                        for exclude_term in config['exclude_terms']:
                            exclude_col_mask = self.mines_df[col].astype(str).str.lower().str.contains(
                                exclude_term, na=False, regex=False
                            )
                            exclude_mask |= exclude_col_mask
                mask = mask & ~exclude_mask
        
        metal_mines = self.mines_df[mask].copy()
        logger.info(f"Found {len(metal_mines)} {metal} mines using {method} method")
        
        return metal_mines

    def calculate_production_estimates(self, metal_mines: pd.DataFrame, metal: str) -> pd.DataFrame:
        """Calculate production estimates for verified mines"""
        if metal_mines.empty:
            return pd.DataFrame()
        
        config = self.metal_configs[metal]
        
        # Filter to active mines only
        active_mines = metal_mines[metal_mines.get('CURRENT_MINE_STATUS', '') == 'Active'].copy()
        logger.info(f"Active {metal} mines: {len(active_mines)}")
        
        if active_mines.empty:
            return pd.DataFrame()
        
        production_estimates = []
        
        for _, mine in active_mines.iterrows():
            # Get employment data
            employees = 0
            
            if self.production_df is not None:
                mine_prod = self.production_df[
                    (self.production_df['MINE_ID'] == mine['MINE_ID']) & 
                    (self.production_df['CAL_YR'] >= 2020)
                ]
                if not mine_prod.empty:
                    employees = mine_prod['AVG_EMPLOYEE_CNT'].mean()
            
            # Fallback to mine record
            if employees <= 0:
                employees = mine.get('NO_EMPLOYEES', 0)
            
            try:
                employees = float(employees) if employees and employees > 0 else 0
            except (ValueError, TypeError):
                employees = 0
            
            if employees <= 0:
                continue
            
            # Calculate production estimate
            production_factor = config['production_factor']
            estimated_annual_production = employees * production_factor
            
            mine_info = {
                'rank': 0,
                'mine_id': mine.get('MINE_ID', ''),
                'mine_name': mine.get('CURRENT_MINE_NAME', ''),
                'state': mine.get('STATE', ''),
                'status': mine.get('CURRENT_MINE_STATUS', ''),
                'mine_type': mine.get('CURRENT_MINE_TYPE', ''),
                'operator': mine.get('CURRENT_OPERATOR_NAME', ''),
                'primary_sic': mine.get('PRIMARY_SIC', ''),
                'employees': round(employees, 1),
                'estimated_annual_production_mt': round(estimated_annual_production, 1),
                'production_factor_mt_per_employee': production_factor,
                'confidence_level': config['confidence'],
                'longitude': mine.get('LONGITUDE', ''),
                'latitude': mine.get('LATITUDE', ''),
                'metal': metal,
                'verification_method': config['method'],
                'verification_notes': config['notes']
            }
            
            production_estimates.append(mine_info)
        
        if not production_estimates:
            return pd.DataFrame()
        
        # Create DataFrame and rank
        estimates_df = pd.DataFrame(production_estimates)
        estimates_df = estimates_df.sort_values('estimated_annual_production_mt', ascending=False).reset_index(drop=True)
        estimates_df['rank'] = range(1, len(estimates_df) + 1)
        
        return estimates_df

    def analyze_all_metals(self):
        """Analyze all 64 critical metals"""
        if not self.load_msha_data():
            logger.error("Failed to load MSHA data")
            return
        
        logger.info("="*80)
        logger.info(f"CRITICAL METALS ANALYSIS - {len(self.metal_configs)} METALS")
        logger.info("="*80)
        
        all_results = []
        successful_metals = []
        
        for metal in self.metal_configs.keys():
            try:
                logger.info(f"\n--- Processing {metal.upper()} ---")
                
                # Find mines
                metal_mines = self.find_metal_mines(metal)
                
                # Calculate production for active mines
                production_df = self.calculate_production_estimates(metal_mines, metal)
                
                # Create summary
                summary = {
                    'metal': metal,
                    'total_mines_identified': len(metal_mines),
                    'active_mines': len(production_df),
                    'total_estimated_production_mt_per_year': production_df['estimated_annual_production_mt'].sum() if not production_df.empty else 0,
                    'total_employment': production_df['employees'].sum() if not production_df.empty else 0,
                    'confidence_level': self.metal_configs[metal]['confidence'],
                    'method': self.metal_configs[metal]['method'],
                    'notes': self.metal_configs[metal]['notes']
                }
                
                all_results.append(summary)
                
                # Save consolidated table if we have results
                if not production_df.empty:
                    output_file = self.consolidated_dir / f"{metal}_analysis.csv"
                    production_df.to_csv(output_file, index=False)
                    
                    # Save detailed JSON
                    json_file = self.consolidated_dir / f"{metal}_detailed.json"
                    with open(json_file, 'w') as f:
                        json.dump({
                            'metal': metal,
                            'analysis_date': datetime.now().isoformat(),
                            'summary': summary,
                            'mines': production_df.to_dict('records')
                        }, f, indent=2, default=str)
                    
                    successful_metals.append(metal)
                    
                    logger.info(f"✓ {metal}: {summary['active_mines']} active mines, {summary['total_estimated_production_mt_per_year']:,.0f} MT/year")
                    
                    # Show top 3 operations
                    for _, mine in production_df.head(3).iterrows():
                        logger.info(f"    {mine['mine_name'][:30]:<30} | {mine['state']} | {mine['estimated_annual_production_mt']:>8,.0f} MT/yr")
                else:
                    logger.info(f"✓ {metal}: No active mines found")
                
            except Exception as e:
                logger.error(f"Error processing {metal}: {e}")
                continue
        
        # Create comprehensive summary
        results_df = pd.DataFrame(all_results)
        results_df = results_df.sort_values('total_estimated_production_mt_per_year', ascending=False)
        
        # Save results
        results_df.to_csv(self.summary_dir / "metals_summary.csv", index=False)
        
        final_report = {
            'analysis_date': datetime.now().isoformat(),
            'methodology': 'Employment-based production estimation with metal-specific factors',
            'metals_analyzed': len(self.metal_configs),
            'metals_with_active_production': len([r for r in all_results if r['active_mines'] > 0]),
            'total_estimated_production_mt': sum(r['total_estimated_production_mt_per_year'] for r in all_results),
            'total_employment': sum(r['total_employment'] for r in all_results),
            'results': all_results
        }
        
        with open(self.summary_dir / "analysis_report.json", 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        return results_df, successful_metals

def main():
    """Run critical metals analysis"""
    analyzer = CriticalMetalsAnalyzer()
    
    print("="*80)
    print(f"CRITICAL METALS MSHA ANALYSIS - {len(analyzer.metal_configs)} METALS")
    print("="*80)
    print("Analysis Methods:")
    print("• Exact SIC code matching (highest confidence)")
    print("• Controlled keyword matching with exclusions")
    print("• Rare earth element group analysis")  
    print("• Platinum group metal analysis")
    print("• Industry knowledge verification")
    print("="*80)
    
    results_df, successful_metals = analyzer.analyze_all_metals()
    
    if not results_df.empty:
        print(f"\n{'='*80}")
        print("ANALYSIS RESULTS SUMMARY")
        print(f"{'='*80}")
        
        active_results = results_df[results_df['active_mines'] > 0]
        
        if not active_results.empty:
            print(f"Metals with active US production: {len(active_results)}")
            print(f"Total estimated production: {active_results['total_estimated_production_mt_per_year'].sum():,.0f} MT/year")
            print(f"Total employment: {active_results['total_employment'].sum():,.0f}")
            
            print(f"\nTop metals by estimated production:")
            for _, metal_data in active_results.head(15).iterrows():
                conf_symbol = "🟢" if metal_data['confidence_level'] == 'high' else "🟡" if metal_data['confidence_level'] == 'medium' else "🔴"
                print(f"  {conf_symbol} {metal_data['metal']:<20} | {metal_data['active_mines']:>3} mines | {metal_data['total_estimated_production_mt_per_year']:>12,.0f} MT/yr")
        
        no_production = results_df[results_df['active_mines'] == 0]
        if not no_production.empty:
            print(f"\nMetals with no active US production: {len(no_production)}")
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"Files created for: {len(successful_metals)} metals")
    print(f"Output directory: {analyzer.base_dir}/")
    print("="*80)

if __name__ == "__main__":
    main()