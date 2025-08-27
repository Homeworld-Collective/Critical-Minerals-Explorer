# Critical Mineral Explorer Website

A comprehensive web application for exploring critical mineral supply chain data for the US and allied nations.

## Features

### 🏗️ Dashboard
- **Overview of all 49+ critical minerals** from the MSHA analysis
- **Interactive filtering** by production level and confidence
- **Search functionality** to quickly find specific metals
- **Summary statistics** showing total mines, production, and employment
- **Color-coded production levels**: Significant, Moderate, Limited, Minimal, None, Byproduct, Emerging

### 📊 Detailed Reports
- **Comprehensive supply chain analysis** for each metal
- **Technical analysis** including discovery, extraction, separation, purification, and remediation technologies
- **Market analysis** with production volumes, demand forecasts, and bottlenecks
- **Source citations** and references
- **Markdown rendering** of the detailed reports

### 🏭 Mine Information
- **Detailed mine data** from the MSHA database
- **Mine-specific information**: location, operator, employees, production estimates
- **Interactive modals** with complete mine details
- **Confidence levels** and verification methods

### 📈 Analysis
- **Production level distribution** charts
- **Confidence level analysis**
- **Visual data representation** using Chart.js

## File Structure

```
GBT/
├── index.html                  # Main website file
├── styles.css                  # All styling and responsive design
├── script.js                   # Application logic and functionality
├── server.py                   # Local development server
├── README_website.md           # This file
│
├── detailed_reports/           # Generated metal reports
│   ├── aluminum_report.md
│   ├── antimony_report.md
│   ├── summary_aluminum.json
│   └── ...
│
└── msha_scraper/
    └── msha_critical_metals_analysis/
        └── analysis_results/
            ├── summary_reports/
            │   └── metals_summary.csv    # Main data source
            └── individual_metals/
                ├── aluminum_detailed.json
                ├── antimony_detailed.json
                └── ...
```

## Data Sources

1. **metals_summary.csv**: Primary data source containing:
   - Metal names and production levels
   - Mine counts and employment figures
   - Production estimates and confidence levels
   - Analysis methods used

2. **{metal}_detailed.json**: Individual mine data including:
   - Mine names, locations, and operators
   - Production estimates and employee counts
   - Mine types and operational status

3. **{metal}_report.md**: Comprehensive supply chain reports with:
   - Technical analysis of mining technologies
   - Market analysis and demand forecasts
   - Supply chain bottlenecks and challenges
   - References and citations

## Running the Website

### Option 1: Local Server (Recommended)
```bash
python server.py
```
This will:
- Start a local HTTP server on port 8080 (or next available)
- Automatically open your browser
- Handle CORS issues for local file access

### Option 2: Direct File Access
Open `index.html` directly in your browser. Note: Some features may not work due to browser security restrictions with local files.

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Custom CSS with Flexbox and Grid
- **Charts**: Chart.js for data visualization
- **Markdown**: Marked.js for report rendering
- **Icons**: Font Awesome
- **Server**: Python built-in HTTP server

## Browser Compatibility

- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

## Performance Notes

- Data is loaded asynchronously for better user experience
- Reports and mine data are cached after first load
- Responsive design works on mobile and desktop
- Charts are rendered only when needed

## Data Updates

To update the website with new data:

1. **Add new metal reports**: Place `{metal}_report.md` files in `detailed_reports/`
2. **Update mine data**: Place `{metal}_detailed.json` files in the appropriate directory
3. **Update summary**: Modify `metals_summary.csv` with new/updated metal data
4. **Refresh the website**: The application will automatically load the new data

## Troubleshooting

### CORS Errors
- Use the provided `server.py` instead of opening files directly
- Make sure all data files are in the correct directories

### Missing Data
- Check that CSV and JSON files are properly formatted
- Verify file paths match the expected structure
- Check browser console for specific error messages

### Performance Issues
- Clear browser cache if data seems outdated
- Check network tab for failed file loads
- Reduce number of metals if needed for testing

## Future Enhancements

- [ ] Export functionality for filtered data
- [ ] Advanced filtering and sorting options
- [ ] Geographic visualization of mines
- [ ] Comparison tools between metals
- [ ] Real-time data updates
- [ ] User preferences and saved views

