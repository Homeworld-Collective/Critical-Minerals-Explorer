# Critical Mineral Explorer

A web application for exploring critical mineral mining capacity in the US using MSHA data.

🌐 **Live Demo**: [https://critical-minerals-explorer.vercel.app](https://critical-minerals-explorer.vercel.app)

## Overview

This prototype analyzes 63 critical metals across 91,307+ US mining operations from the MSHA database to identify domestic production capacity and supply chain gaps. The tool is designed to help researchers and policymakers understand where biotechnology might assist with mining and processing challenges.

## Features

- **Interactive dashboard** with filtering by production level and confidence
- **Mine-level data** including location, operator, employment, and production estimates  
- **Supply chain reports** for each metal with technology analysis and bottlenecks
- **Production estimates** based on employment data and industry benchmarks

## Quick Start

**View online**: [https://critical-minerals-explorer.vercel.app](https://critical-minerals-explorer.vercel.app)

**Run locally**:
```bash
git clone https://github.com/dgoodwin208/Critical-Minerals-Explorer.git
cd Critical-Minerals-Explorer
python server.py
```

## Data Sources

- **MSHA Mines Database**: 91,307+ US mining operations (both active and historical)
- **Metal Selection**: Based on 2025 USGS critical minerals list
- **Production Estimates**: Employment-based modeling with metal-specific factors
- **Confidence Levels**: High (exact SIC codes), Medium (keyword matching), Low (limited data)

## Key Findings

- **Strong US production**: Aluminum (1.9M MT/year), Zinc (8.9M MT/year), Barite (1.9M MT/year)
- **Limited production**: Most rare earth elements, platinum group metals  
- **No US production**: Tin (verified zero active operations)
- **Supply vulnerabilities**: Heavy import dependence for specialty metals

## Technology Stack

- Frontend: HTML5, CSS3, JavaScript
- Data processing: Python (pandas)
- Visualization: Chart.js
- Deployment: Vercel

## Limitations

- Production estimates are modeled, not directly reported
- Some byproduct production may not be captured  
- MSHA data focuses on employment/safety, not production volumes
- Results should be verified against industry sources

## Citation

```
Critical Mineral Explorer
Data: Mine Safety and Health Administration (MSHA), August 2025
URL: https://github.com/dgoodwin208/Critical-Minerals-Explorer
```

Built by Daniel Goodwin and Jayme Feyhl-Buska as a research prototype.