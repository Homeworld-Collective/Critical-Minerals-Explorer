// Critical Mineral Explorer JavaScript
class CriticalMineralExplorer {
    constructor() {
        this.metalsData = [];
        this.filteredData = [];
        this.reportsCache = {};
        this.mineDataCache = {};
        this.introductionCache = null;
        this.currentMetal = null;
        this.criticalMineralsData = [];
        this.dataTable = null;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadData();
        await this.loadCriticalMineralsData(); // Load the CSV data for domestic supply percentages
        this.hideLoading();
        this.renderDashboard();
        this.renderMetalList();
        this.updateSummaryStats();
        
        // Handle initial URL or default to introduction
        this.handleUrlChange();
        
        // Listen for browser back/forward buttons
        window.addEventListener('popstate', () => {
            this.handleUrlChange();
        });
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Search and filters
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.filterMetals();
        });
        
        document.getElementById('production-filter').addEventListener('change', () => {
            this.filterMetals();
        });
        
        document.getElementById('confidence-filter').addEventListener('change', () => {
            this.filterMetals();
        });

        // Modal close
        document.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal();
        });
        
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal();
            }
        });
    }

    async loadData() {
        try {
            // Load the CSV data
            const csvResponse = await fetch('msha_scraper/msha_critical_metals_analysis/analysis_results/summary_reports/metals_summary.csv');
            const csvText = await csvResponse.text();
            this.metalsData = this.parseCSV(csvText);
            this.filteredData = [...this.metalsData];
            
            console.log('Loaded data for', this.metalsData.length, 'metals');
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load mineral data');
        }
    }

    async loadCriticalMineralsData() {
        try {
            const response = await fetch('./static-criticalminerals-2030estimates-GDP.csv');
            if (response.ok) {
                const csvText = await response.text();
                this.criticalMineralsData = this.parseCriticalMineralsCSV(csvText);
                
                // Create a lookup map for domestic supply percentages
                this.domesticSupplyMap = {};
                this.criticalMineralsData.forEach(row => {
                    const metalName = row.Metal?.toLowerCase();
                    const domesticSupply = row['Percentage on Domestic Supply for Demand 2030'];
                    if (metalName && domesticSupply) {
                        this.domesticSupplyMap[metalName] = domesticSupply;
                    }
                });
                
                console.log('Loaded critical minerals data for domestic supply percentages');
            }
        } catch (error) {
            console.error('Error loading critical minerals data:', error);
            // Don't fail initialization if this data isn't available
        }
    }

    parseCSV(text) {
        const lines = text.trim().split('\n');
        const headers = lines[0].split(',');
        
        return lines.slice(1).map(line => {
            if (!line.trim()) return null;
            
            const values = this.parseCSVLine(line);
            const row = {};
            
            headers.forEach((header, index) => {
                row[header.trim()] = values[index] ? values[index].trim() : '';
            });
            
            // Convert numeric fields
            row.total_mines_identified = parseInt(row.total_mines_identified) || 0;
            row.active_mines = parseInt(row.active_mines) || 0;
            row.total_estimated_production_mt_per_year = parseFloat(row.total_estimated_production_mt_per_year) || 0;
            row.total_employment = parseInt(row.total_employment) || 0;
            
            return row;
        }).filter(row => row !== null);
    }

    parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(current);
                current = '';
            } else {
                current += char;
            }
        }
        
        result.push(current);
        return result;
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    showError(message) {
        const loading = document.getElementById('loading');
        loading.innerHTML = `
            <div style="color: #e74c3c;">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>${message}</p>
            </div>
        `;
    }

    switchTab(tabName, metalName = null, updateHistory = true) {
        // Deactivate commenting system when switching away from reports
        if (window.commentingSystem && tabName !== 'reports') {
            window.commentingSystem.deactivate();
        }
        
        // Update URL hash if updating history
        if (updateHistory) {
            const hash = metalName ? `#${tabName}/${metalName}` : `#${tabName}`;
            history.pushState({tab: tabName, metal: metalName}, '', hash);
        }
        
        // Update nav tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load tab-specific content if needed
        if (tabName === 'analysis') {
            this.loadCriticalMineralsTable();
        } else if (tabName === 'introduction') {
            this.loadIntroduction();
        } else if (tabName === 'reports' && metalName) {
            this.loadReport(metalName, false); // Don't update history again
        }
    }
    
    handleUrlChange() {
        const hash = window.location.hash.slice(1); // Remove #
        
        if (!hash) {
            // Default to introduction
            this.switchTab('introduction', null, false);
            return;
        }
        
        const parts = hash.split('/');
        const tabName = parts[0];
        const metalName = parts[1];
        
        if (tabName === 'reports' && metalName) {
            this.switchTab('reports', metalName, false);
        } else {
            this.switchTab(tabName, null, false);
        }
    }

    filterMetals() {
        const searchTerm = document.getElementById('search-input').value.toLowerCase();
        const productionFilter = document.getElementById('production-filter').value;
        const confidenceFilter = document.getElementById('confidence-filter').value;

        this.filteredData = this.metalsData.filter(metal => {
            const matchesSearch = metal.metal.toLowerCase().includes(searchTerm);
            const matchesProduction = !productionFilter || metal.expected_us_production === productionFilter;
            const matchesConfidence = !confidenceFilter || metal.confidence_level === confidenceFilter;

            return matchesSearch && matchesProduction && matchesConfidence;
        });

        this.renderDashboard();
        this.updateSummaryStats();
    }

    updateSummaryStats() {
        const totalMetals = this.filteredData.length;
        const activeMines = this.filteredData.reduce((sum, metal) => sum + metal.active_mines, 0);
        const totalEmployment = this.filteredData.reduce((sum, metal) => sum + metal.total_employment, 0);

        document.getElementById('total-metals').textContent = totalMetals.toLocaleString();
        document.getElementById('active-mines').textContent = activeMines.toLocaleString();
        document.getElementById('total-employment').textContent = totalEmployment.toLocaleString();
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toLocaleString();
    }

    renderDashboard() {
        const grid = document.getElementById('metals-grid');
        
        if (this.filteredData.length === 0) {
            grid.innerHTML = `
                <div class="text-center" style="grid-column: 1 / -1; padding: 4rem;">
                    <i class="fas fa-search" style="font-size: 3rem; color: #bdc3c7; margin-bottom: 1rem;"></i>
                    <h3 style="color: #7f8c8d;">No metals found</h3>
                    <p style="color: #7f8c8d;">Try adjusting your search criteria</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.filteredData.map(metal => this.createMetalCard(metal)).join('');
    }

    createMetalCard(metal) {
        const productionClass = `production-${metal.expected_us_production}`;
        const confidenceClass = `confidence-${metal.confidence_level}`;
        
        // Get domestic supply percentage from the critical minerals data
        const domesticSupplyPct = this.domesticSupplyMap?.[metal.metal.toLowerCase()] || 'N/A';
        
        // Calculate color based on percentage
        const percentageColor = this.getPercentageColor(domesticSupplyPct);
        
        return `
            <div class="metal-card" onclick="explorer.showMineDetails('${metal.metal}')">
                <div class="metal-header">
                    <h3 class="metal-name">${metal.metal}</h3>
                    <span class="production-badge" style="background-color: ${percentageColor}; color: #fff; font-weight: bold;">${domesticSupplyPct}</span>
                </div>
                
                <div class="metal-stats">
                    <div class="stat">
                        <div class="stat-value" style="color: #000;">${metal.active_mines}</div>
                        <div class="stat-label" style="color: #333;">Active Mines</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" style="color: #000;">${this.formatNumber(metal.total_estimated_production_mt_per_year)}</div>
                        <div class="stat-label" style="color: #333;">Est. Production (MT/yr)</div>
                    </div>
                </div>
                
                <div class="metal-details">
                    <div class="detail-item">
                        <span>Total Mines:</span>
                        <span>${metal.total_mines_identified}</span>
                    </div>
                    <div class="detail-item">
                        <span>Employment:</span>
                        <span>${metal.total_employment.toLocaleString()}</span>
                    </div>
                    <div class="detail-item">
                        <span>Method:</span>
                        <span>${metal.method}</span>
                    </div>
                    <div class="detail-item">
                        <span>Confidence:</span>
                        <span>${metal.confidence_level}<span class="confidence-indicator ${confidenceClass}"></span></span>
                    </div>
                </div>
                
                <button class="mines-button" onclick="event.stopPropagation(); explorer.showMineDetails('${metal.metal}')">
                    <i class="fas fa-info-circle"></i> View Mine Details
                </button>
            </div>
        `;
    }

    renderMetalList() {
        const metalList = document.getElementById('metal-list');
        
        // Sort metals alphabetically by name
        const sortedMetals = [...this.metalsData].sort((a, b) => 
            a.metal.toLowerCase().localeCompare(b.metal.toLowerCase())
        );
        
        metalList.innerHTML = sortedMetals.map(metal => `
            <div class="metal-list-item" onclick="app.switchToMetalReport('${metal.metal}')">
                ${metal.metal}
            </div>
        `).join('');
    }

    async loadReport(metalName, updateHistory = true) {
        console.log('loadReport called for:', metalName);
        
        // Update active metal in sidebar
        document.querySelectorAll('.metal-list-item').forEach(item => {
            item.classList.remove('active');
        });
        // Find and activate the corresponding metal item
        const targetItem = document.querySelector(`[data-metal="${metalName}"]`);
        if (targetItem) {
            targetItem.classList.add('active');
        }

        // Check cache first
        if (this.reportsCache[metalName]) {
            console.log('Loading from cache for:', metalName);
            const cached = this.reportsCache[metalName];
            this.displayReport(metalName, cached.content, cached.lastModified);
            return;
        }

        // Show loading
        const reportContent = document.getElementById('report-content');
        const placeholder = document.querySelector('.report-placeholder');
        
        placeholder.style.display = 'none';
        reportContent.style.display = 'block';
        reportContent.innerHTML = `
            <div class="text-center" style="padding: 4rem;">
                <div class="loading-spinner"></div>
                <p>Loading ${metalName} report...</p>
            </div>
        `;

        try {
            console.log('Fetching report for:', metalName);
            const response = await fetch(`./detailed_reports/${metalName}_report.md`);
            if (!response.ok) {
                throw new Error(`Report not found for ${metalName}`);
            }
            
            const markdownText = await response.text();
            console.log('Fetched markdown, length:', markdownText.length);
            
            // Get the last modified date from the response headers
            const lastModified = response.headers.get('Last-Modified');
            let lastModifiedDate = null;
            if (lastModified) {
                const date = new Date(lastModified);
                lastModifiedDate = date.toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                });
            }
            
            this.reportsCache[metalName] = { 
                content: markdownText, 
                lastModified: lastModifiedDate 
            };
            this.displayReport(metalName, markdownText, lastModifiedDate);
            
        } catch (error) {
            console.error('Error loading report:', error);
            reportContent.innerHTML = `
                <div class="text-center" style="padding: 4rem; color: #e74c3c;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <h3>Report not available</h3>
                    <p>The detailed report for ${metalName} could not be loaded.</p>
                    <p style="font-size: 0.9rem; color: #7f8c8d;">Error: ${error.message}</p>
                </div>
            `;
        }
    }

    displayReport(metalName, markdownText, lastModifiedDate) {
        const reportContent = document.getElementById('report-content');
        
        // Initialize markdown-it with options for better link handling
        const md = window.markdownit({
            html: true,
            linkify: true,
            typographer: false,
            breaks: true
        });
        
        // Add custom renderer for headers to include IDs
        md.renderer.rules.heading_open = (tokens, idx, options, env, renderer) => {
            const token = tokens[idx];
            const level = token.tag.substr(1); // Extract number from h1, h2, etc.
            
            if (level === '2' || level === '3') {
                // Find the next token which should be the inline text
                const nextToken = tokens[idx + 1];
                if (nextToken && nextToken.type === 'inline') {
                    const headerId = this.createHeaderId(nextToken.content);
                    return `<${token.tag} id="${headerId}">`;
                }
            }
            
            return `<${token.tag}>`;
        };
        
        // Insert the last updated date at the beginning of the markdown content before conversion
        let modifiedMarkdown = markdownText;
        if (lastModifiedDate) {
            const lastUpdatedLine = `<p style="color: #7f8c8d; font-style: italic; margin-top: 0.5rem; margin-bottom: 1rem;">Last updated on: ${lastModifiedDate}</p>\n\n---\n\n`;
            modifiedMarkdown = lastUpdatedLine + markdownText;
        }
        
        // Generate Table of Contents
        const tocHtml = this.generateTableOfContents(markdownText);
        
        // Convert markdown to HTML using markdown-it
        const htmlContent = md.render(modifiedMarkdown);
        
        // Insert TOC after the horizontal line
        const htmlWithToc = this.insertTableOfContents(htmlContent, tocHtml);
        
        reportContent.innerHTML = `
            <h1 style="border-bottom: none; margin-bottom: 0;"><i class="fas fa-gem"></i> ${metalName.charAt(0).toUpperCase() + metalName.slice(1)} Supply Chain Analysis</h1>
            <div>${htmlWithToc}</div>
        `;
        
        // Add smooth scrolling to TOC links
        this.setupSmoothScrolling();
        
        // Activate commenting system for reports
        if (window.commentingSystem) {
            window.commentingSystem.activate();
            // Load and display existing comments after a short delay to ensure DOM is ready
            setTimeout(async () => {
                await window.commentingSystem.loadCommentsFromAPI();
                window.commentingSystem.displayComments();
            }, 100);
        }
    }

    generateTableOfContents(markdownText) {
        // Extract headers from markdown content (## and ###)
        const headerRegex = /^(#{2,3})\s+(.+)$/gm;
        const headers = [];
        let match;
        
        while ((match = headerRegex.exec(markdownText)) !== null) {
            const level = match[1].length; // 2 for ##, 3 for ###
            const text = match[2].trim();
            const id = this.createHeaderId(text);
            
            headers.push({
                level: level,
                text: text,
                id: id
            });
        }
        
        if (headers.length === 0) {
            return '';
        }
        
        // Generate TOC HTML with minimal styling to match report text
        let tocHtml = `
            <div class="table-of-contents" style="margin: 1rem 0;">
                <h2>Table of Contents</h2>
                <ul style="list-style: none; padding-left: 0; margin: 0;">
        `;
        
        headers.forEach(header => {
            const indentStyle = header.level === 3 ? 'padding-left: 1.5rem;' : '';
            tocHtml += `
                <li style="${indentStyle} margin: 0; line-height: 1.3;">
                    <a href="#${header.id}" class="toc-link" style="color: inherit; text-decoration: underline;">
                        ${header.text}
                    </a>
                </li>
            `;
        });
        
        tocHtml += `
                </ul>
            </div>
        `;
        
        return tocHtml;
    }

    getPercentageColor(percentageStr) {
        // Handle non-numeric values
        if (percentageStr === 'N/A' || !percentageStr) {
            return '#6b7280'; // Gray for unknown values
        }
        
        // Extract numeric value from percentage string
        const numericValue = parseFloat(percentageStr.toString().replace('%', ''));
        
        if (isNaN(numericValue)) {
            return '#6b7280'; // Gray for invalid values
        }
        
        // Clamp value between 0 and 100 for color calculation
        const clampedValue = Math.min(100, Math.max(0, numericValue));
        
        // Calculate color based on percentage
        if (clampedValue <= 50) {
            // Red to Yellow (0% to 50%)
            const ratio = clampedValue / 50;
            const red = 220; // Keep red high
            const green = Math.round(ratio * 200); // Increase green from 0 to 200
            const blue = 0;
            return `rgb(${red}, ${green}, ${blue})`;
        } else {
            // Yellow to Green (50% to 100%)
            const ratio = (clampedValue - 50) / 50;
            const red = Math.round(220 - (ratio * 180)); // Decrease red from 220 to 40
            const green = Math.round(200 + (ratio * 55)); // Increase green from 200 to 255
            const blue = 0;
            return `rgb(${red}, ${green}, ${blue})`;
        }
    }

    createHeaderId(text) {
        // Create a URL-safe ID from header text
        return text
            .toLowerCase()
            .replace(/[^\w\s-]/g, '') // Remove non-alphanumeric characters except spaces and hyphens
            .replace(/\s+/g, '-')      // Replace spaces with hyphens
            .replace(/-+/g, '-')       // Replace multiple hyphens with single hyphen
            .trim();
    }

    insertTableOfContents(htmlContent, tocHtml) {
        // Find the first <hr> tag (horizontal line) and insert TOC after it
        const hrRegex = /<hr\s*\/?>/i;
        const match = htmlContent.match(hrRegex);
        
        if (match && tocHtml) {
            const hrIndex = match.index + match[0].length;
            return htmlContent.slice(0, hrIndex) + tocHtml + htmlContent.slice(hrIndex);
        }
        
        return htmlContent;
    }

    setupSmoothScrolling() {
        // Add smooth scrolling behavior to TOC links
        document.querySelectorAll('.toc-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    
                    // Add a visual highlight to the target header
                    targetElement.style.transition = 'background-color 0.3s';
                    targetElement.style.backgroundColor = '#e3f2fd';
                    setTimeout(() => {
                        targetElement.style.backgroundColor = '';
                    }, 1500);
                }
            });
            
            // Simple hover effect - just change text decoration
            link.addEventListener('mouseenter', () => {
                link.style.textDecoration = 'none';
            });
            
            link.addEventListener('mouseleave', () => {
                link.style.textDecoration = 'underline';
            });
        });
    }

    async loadIntroduction() {
        const introContent = document.getElementById('introduction-content');
        
        // Show loading if not already cached
        if (!this.introductionCache) {
            introContent.innerHTML = `
                <div class="text-center" style="padding: 4rem;">
                    <div class="loading-spinner"></div>
                    <p>Loading introduction...</p>
                </div>
            `;
        }

        try {
            if (!this.introductionCache) {
                const response = await fetch('introduction.md');
                if (!response.ok) {
                    throw new Error('Introduction file not found');
                }
                
                const markdownText = await response.text();
                this.introductionCache = markdownText;
            }
            
            // Initialize markdown-it
            const md = window.markdownit({
                html: true,
                linkify: true,
                typographer: false,
                breaks: true
            });
            
            // Convert markdown to HTML and make links clickable for detailed reports
            let processedMarkdown = this.introductionCache;
            
            // Replace [metal](metalname) links with clickable report links
            processedMarkdown = processedMarkdown.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, metalName) => {
                // Convert the metal name to lowercase for consistency with file names
                const normalizedMetalName = metalName.toLowerCase().trim();
                return `<a href="#reports/${normalizedMetalName}" onclick="app.switchToMetalReport('${normalizedMetalName}'); return false;" style="color: #3498db; text-decoration: underline;">${text}</a>`;
            });
            
            const htmlContent = md.render(processedMarkdown);
            
            introContent.innerHTML = htmlContent;
            
        } catch (error) {
            console.error('Error loading introduction:', error);
            introContent.innerHTML = `
                <div class="text-center" style="padding: 4rem; color: #e74c3c;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <h3>Introduction not available</h3>
                    <p>The introduction content could not be loaded.</p>
                    <p style="font-size: 0.9rem; color: #7f8c8d;">Error: ${error.message}</p>
                </div>
            `;
        }
    }

    switchToMetalReport(metalName) {
        // Switch to reports tab and load the specific report with history
        this.switchTab('reports', metalName);
    }

    async showMineDetails(metalName) {
        // Check cache first
        if (this.mineDataCache[metalName]) {
            this.displayMineModal(metalName, this.mineDataCache[metalName]);
            return;
        }

        // Show loading modal
        this.showLoadingModal(metalName);

        try {
            const response = await fetch(`./msha_scraper/msha_critical_metals_analysis/analysis_results/individual_metals/${metalName}_detailed.json`);
            if (!response.ok) {
                throw new Error(`Mine data not found for ${metalName}`);
            }
            
            // Get the raw text and fix invalid JSON values
            const jsonText = await response.text();
            const fixedJsonText = this.fixInvalidJson(jsonText);
            const mineData = JSON.parse(fixedJsonText);
            
            this.mineDataCache[metalName] = mineData;
            this.displayMineModal(metalName, mineData);
            
        } catch (error) {
            console.error('Error loading mine data:', error);
            this.displayMineErrorModal(metalName, error.message);
        }
    }

    showLoadingModal(metalName) {
        const modal = document.getElementById('mine-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        modalTitle.textContent = `${metalName.charAt(0).toUpperCase() + metalName.slice(1)} Mine Details`;
        modalBody.innerHTML = `
            <div class="text-center" style="padding: 4rem;">
                <div class="loading-spinner"></div>
                <p>Loading mine data for ${metalName}...</p>
            </div>
        `;
        
        modal.style.display = 'block';
    }

    displayMineModal(metalName, mineData) {
        const modal = document.getElementById('mine-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        modalTitle.innerHTML = `<i class="fas fa-mountain"></i> ${metalName.charAt(0).toUpperCase() + metalName.slice(1)} Mine Details`;
        
        // Extract the mines array from the data structure
        let mines = [];
        if (mineData && mineData.mines && Array.isArray(mineData.mines)) {
            mines = mineData.mines;
        } else if (mineData && mineData.all_identified_mines && Array.isArray(mineData.all_identified_mines)) {
            mines = mineData.all_identified_mines;
        } else if (Array.isArray(mineData)) {
            mines = mineData;
        }
        
        if (mines.length === 0) {
            modalBody.innerHTML = `
                <div class="text-center" style="padding: 4rem;">
                    <i class="fas fa-info-circle" style="font-size: 3rem; color: #7f8c8d; margin-bottom: 1rem;"></i>
                    <h3>No detailed mine data available</h3>
                    <p>There are no specific mines recorded for ${metalName} in the database.</p>
                </div>
            `;
        } else {
            // Show summary statistics if available
            let summaryHtml = '';
            if (mineData.summary) {
                const stats = mineData.summary;
                summaryHtml = `
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; color: #000;">
                        <h4 style="margin-bottom: 0.5rem; color: #2c3e50;">Summary Statistics</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; color: #333;">
                            <div><strong>Total Mines:</strong> ${stats.total_mines_identified || 0}</div>
                            <div><strong>Active Mines:</strong> ${stats.active_mines || 0}</div>
                            <div><strong>Total Est. Production:</strong> ${this.formatNumber(stats.total_estimated_production_mt_per_year || 0)} MT/yr</div>
                            <div><strong>Total Employment:</strong> ${(stats.total_employment || 0).toLocaleString()}</div>
                        </div>
                    </div>
                `;
            }
            
            modalBody.innerHTML = `
                ${summaryHtml}
                <div style="margin-bottom: 1rem;">
                    <strong>Individual Mines (${mines.length}):</strong>
                </div>
                <div style="max-height: 400px; overflow-y: auto;">
                    ${mines.map(mine => this.createMineCard(mine)).join('')}
                </div>
            `;
        }
        
        modal.style.display = 'block';
    }

    displayMineErrorModal(metalName, errorMessage) {
        const modal = document.getElementById('mine-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        modalTitle.textContent = `${metalName.charAt(0).toUpperCase() + metalName.slice(1)} Mine Details`;
        modalBody.innerHTML = `
            <div class="text-center" style="padding: 4rem; color: #e74c3c;">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <h3>Error loading mine data</h3>
                <p>Could not load mine information for ${metalName}.</p>
                <p style="font-size: 0.9rem; color: #7f8c8d;">Error: ${errorMessage}</p>
            </div>
        `;
        
        modal.style.display = 'block';
    }

    createMineCard(mine) {
        // Handle both the original CSV-based structure and the detailed JSON structure
        const mineName = mine.mine_name || 'Unknown Mine';
        const state = mine.state || 'N/A';
        const status = mine.status || 'N/A';
        const mineType = mine.mine_type || 'N/A';
        const operator = mine.operator || 'N/A';
        const employees = mine.employees || mine.employees_reported || 0;
        const production = mine.estimated_annual_production_mt || 0;
        const primarySic = mine.primary_sic || mine.sic || 'N/A';
        const isActive = mine.is_active_producer !== undefined ? (mine.is_active_producer ? 'Active' : 'Inactive') : status;
        
        return `
            <div class="mine-card">
                <div class="mine-name">${mineName}</div>
                <div class="mine-details">
                    <div class="mine-detail-item">
                        <span class="mine-detail-label">State:</span>
                        <span class="mine-detail-value">${state}</span>
                    </div>
                    <div class="mine-detail-item">
                        <span class="mine-detail-label">Status:</span>
                        <span class="mine-detail-value">${isActive}</span>
                    </div>
                    <div class="mine-detail-item">
                        <span class="mine-detail-label">Type:</span>
                        <span class="mine-detail-value">${mineType}</span>
                    </div>
                    <div class="mine-detail-item">
                        <span class="mine-detail-label">Operator:</span>
                        <span class="mine-detail-value">${operator}</span>
                    </div>
                    <div class="mine-detail-item">
                        <span class="mine-detail-label">Primary SIC:</span>
                        <span class="mine-detail-value">${primarySic}</span>
                    </div>
                    <div class="mine-detail-item">
                        <span class="mine-detail-label">Employees:</span>
                        <span class="mine-detail-value">${employees ? employees.toLocaleString() : 'N/A'}</span>
                    </div>
                    <div class="mine-detail-item">
                        <span class="mine-detail-label">Est. Production (MT/yr):</span>
                        <span class="mine-detail-value">${production ? this.formatNumber(production) : 'N/A'}</span>
                    </div>
                    ${mine.longitude && mine.latitude && mine.longitude !== null && mine.latitude !== null ? `
                    <div class="mine-detail-item">
                        <span class="mine-detail-label">Location:</span>
                        <span class="mine-detail-value">${mine.latitude.toFixed(4)}, ${mine.longitude.toFixed(4)}</span>
                    </div>
                    ` : ''}
                    ${mine.county ? `
                    <div class="mine-detail-item">
                        <span class="mine-detail-label">County:</span>
                        <span class="mine-detail-value">${mine.county}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    fixInvalidJson(jsonText) {
        // Replace invalid JSON values with valid ones
        return jsonText
            .replace(/:\s*NaN\s*([,}])/g, ': null$1')  // Replace NaN with null
            .replace(/:\s*Infinity\s*([,}])/g, ': null$1')  // Replace Infinity with null
            .replace(/:\s*-Infinity\s*([,}])/g, ': null$1')  // Replace -Infinity with null
            .replace(/:\s*undefined\s*([,}])/g, ': null$1');  // Replace undefined with null
    }

    closeModal() {
        document.getElementById('mine-modal').style.display = 'none';
    }

    async loadCriticalMineralsTable() {
        // Check if data is already loaded
        if (this.criticalMineralsData.length > 0 && this.dataTable) {
            return;
        }

        try {
            const response = await fetch('./static-criticalminerals-2030estimates-GDP.csv');
            if (!response.ok) {
                throw new Error('Failed to load critical minerals data');
            }
            
            const csvText = await response.text();
            this.criticalMineralsData = this.parseCriticalMineralsCSV(csvText);
            
            this.initializeDataTable();
            
        } catch (error) {
            console.error('Error loading critical minerals data:', error);
            document.querySelector('#analysis-tab .analysis-container').innerHTML = `
                <h2>Critical Minerals Data Table</h2>
                <div class="text-center" style="padding: 4rem; color: #e74c3c;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <h3>Error loading data table</h3>
                    <p>Could not load critical minerals data.</p>
                    <p style="font-size: 0.9rem; color: #7f8c8d;">Error: ${error.message}</p>
                </div>
            `;
        }
    }

    parseCriticalMineralsCSV(csvText) {
        const lines = csvText.trim().split('\n');
        const headers = this.parseCSVLine(lines[0]);
        
        return lines.slice(1).map(line => {
            if (!line.trim()) return null;
            
            const values = this.parseCSVLine(line);
            const row = {};
            
            headers.forEach((header, index) => {
                row[header.trim()] = values[index] ? values[index].trim() : '';
            });
            
            return row;
        }).filter(row => row !== null);
    }

    initializeDataTable() {
        // Prepare data for DataTable
        const tableData = this.criticalMineralsData.map(row => {
            const metalName = row.Metal || '';
            const currentProduction = this.formatNumber(parseFloat(row['Current Production (tons)'].replace(/,/g, '')) || 0);
            const demand2030 = this.formatNumber(parseFloat(row['Demand 2030 (tons)'].replace(/,/g, '')) || 0);
            const supply2030 = this.formatNumber(parseFloat(row['Supply 2030 (tons)'].replace(/,/g, '')) || 0);
            const domesticSupplyPct = row['Percentage on Domestic Supply for Demand 2030'] || '0%';
            const bottleneck = row.Bottleneck || '';
            const gdpImpact = (parseFloat(row['Net decrease in U.S. GDP']) || 0).toLocaleString();

            return [
                `<a href="#reports/${metalName.toLowerCase()}" onclick="app.switchToMetalReport('${metalName.toLowerCase()}'); return false;" style="color: #3498db; text-decoration: underline;">${metalName}</a>`,
                currentProduction,
                demand2030,
                supply2030,
                domesticSupplyPct,
                bottleneck,
                gdpImpact
            ];
        });

        // Initialize DataTable
        if (this.dataTable) {
            this.dataTable.destroy();
        }

        this.dataTable = $('#minerals-table').DataTable({
            data: tableData,
            paging: false, // Remove pagination
            order: [[6, 'desc']], // Sort by GDP Impact descending by default
            responsive: true,
            columnDefs: [
                {
                    targets: [1, 2, 3, 6], // Numeric columns
                    className: 'text-right'
                },
                {
                    targets: [4], // Percentage column
                    className: 'text-center'
                }
            ],
            language: {
                search: "Search metals:",
                info: "Showing all _TOTAL_ critical minerals"
            }
        });
    }

}

// Commenting System for Detailed Reports
class CommentingSystem {
    constructor() {
        this.comments = [];
        this.currentSelection = null;
        this.commentIcon = null;
        this.isActive = false;
        this.isSubmitting = false;
        this.init();
    }

    init() {
        this.createCommentIcon();
        this.createModal();
        this.setupEventListeners();
    }

    createCommentIcon() {
        this.commentIcon = document.createElement('div');
        this.commentIcon.className = 'comment-icon';
        this.commentIcon.innerHTML = '<i class="fas fa-comment"></i>';
        this.commentIcon.style.cssText = `
            position: absolute;
            background: #3498db;
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.2s ease;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(this.commentIcon);
    }

    createModal() {
        const modal = document.createElement('div');
        modal.className = 'comment-modal';
        modal.innerHTML = `
            <div class="comment-modal-content">
                <div class="comment-modal-header">
                    <h3>Add Comment</h3>
                    <span class="comment-modal-close">&times;</span>
                </div>
                <div class="comment-context">
                    <strong>Selected text:</strong>
                    <div class="comment-selected-text"></div>
                </div>
                <textarea class="comment-textarea" placeholder="Share your feedback, corrections, or insights..." maxlength="500"></textarea>
                <div class="comment-char-count">0/500</div>
                <div class="comment-modal-actions">
                    <button class="comment-cancel-btn">Cancel</button>
                    <button class="comment-submit-btn">Add Comment</button>
                </div>
            </div>
        `;
        modal.style.cssText = `
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        `;
        document.body.appendChild(modal);
        this.modal = modal;
    }

    setupEventListeners() {
        // Text selection handling
        document.addEventListener('mouseup', (e) => {
            if (this.isActive) {
                setTimeout(() => this.handleTextSelection(e), 10);
            }
        });

        document.addEventListener('mousedown', (e) => {
            // Don't hide comment icon/selection if clicking on modal or comment icon
            if (!this.commentIcon.contains(e.target) && !this.modal.contains(e.target)) {
                // Only hide if not clicking to open the modal
                if (!this.modal || this.modal.style.display !== 'block') {
                    this.hideCommentIcon();
                }
            }
        });

        // Comment icon click
        this.commentIcon.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showModal();
        });

        // Modal event listeners
        const modal = this.modal;
        const closeBtn = modal.querySelector('.comment-modal-close');
        const cancelBtn = modal.querySelector('.comment-cancel-btn');
        const submitBtn = modal.querySelector('.comment-submit-btn');
        const textarea = modal.querySelector('.comment-textarea');
        const charCount = modal.querySelector('.comment-char-count');

        closeBtn.addEventListener('click', () => this.hideModal());
        cancelBtn.addEventListener('click', () => this.hideModal());
        submitBtn.addEventListener('click', (e) => {
            console.log('Submit button clicked');
            e.preventDefault();
            this.submitComment();
        });

        textarea.addEventListener('input', (e) => {
            const length = e.target.value.length;
            charCount.textContent = `${length}/500`;
            charCount.style.color = length > 450 ? '#e74c3c' : '#7f8c8d';
        });

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideModal();
            }
        });
    }

    activate() {
        console.log('Comment system activated');
        this.isActive = true;
    }

    deactivate() {
        console.log('Comment system deactivated');
        this.isActive = false;
        this.hideCommentIcon();
    }

    handleTextSelection(e) {
        console.log('handleTextSelection called');
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        
        console.log('Selected text:', selectedText);
        
        if (selectedText.length > 0 && selectedText.length >= 10) {
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            
            // Only show if selection is within report content
            const reportContent = document.getElementById('report-content');
            if (reportContent && reportContent.contains(range.commonAncestorContainer)) {
                this.currentSelection = {
                    text: selectedText,
                    context: this.getSelectionContext(range),
                    range: range.cloneRange()
                };
                
                this.showCommentIcon(rect);
            }
        } else {
            this.hideCommentIcon();
        }
    }

    getSelectionContext(range) {
        const container = range.commonAncestorContainer;
        let contextElement = container.nodeType === Node.TEXT_NODE ? container.parentNode : container;
        
        // Find the containing paragraph or section
        while (contextElement && !['P', 'H2', 'H3', 'LI', 'DIV'].includes(contextElement.tagName)) {
            contextElement = contextElement.parentNode;
        }
        
        if (contextElement) {
            const fullText = contextElement.textContent.trim();
            const selectedText = range.toString().trim();
            const startIndex = fullText.indexOf(selectedText);
            
            // Get surrounding context (50 chars before and after)
            const contextStart = Math.max(0, startIndex - 50);
            const contextEnd = Math.min(fullText.length, startIndex + selectedText.length + 50);
            
            return {
                fullContext: fullText.substring(contextStart, contextEnd),
                selectedText: selectedText,
                sectionTitle: this.getSectionTitle(contextElement)
            };
        }
        
        return {
            fullContext: range.toString().trim(),
            selectedText: range.toString().trim(),
            sectionTitle: 'Unknown Section'
        };
    }

    getSectionTitle(element) {
        // Find the nearest section header
        let current = element;
        while (current && current !== document.body) {
            if (['H2', 'H3'].includes(current.tagName)) {
                return current.textContent.trim();
            }
            current = current.previousElementSibling || current.parentNode;
            if (current && current.previousElementSibling) {
                const siblings = Array.from(current.parentNode.children);
                const currentIndex = siblings.indexOf(current);
                for (let i = currentIndex - 1; i >= 0; i--) {
                    if (['H2', 'H3'].includes(siblings[i].tagName)) {
                        return siblings[i].textContent.trim();
                    }
                }
            }
        }
        return 'General';
    }

    showCommentIcon(rect) {
        const icon = this.commentIcon;
        const scrollY = window.scrollY;
        
        icon.style.left = `${rect.right + 10}px`;
        icon.style.top = `${rect.top + scrollY + (rect.height / 2) - 16}px`;
        icon.style.opacity = '1';
    }

    hideCommentIcon() {
        this.commentIcon.style.opacity = '0';
        // Only clear selection if modal is not open
        if (!this.modal || this.modal.style.display !== 'block') {
            this.currentSelection = null;
        }
    }

    showModal() {
        if (!this.currentSelection) return;
        
        const modal = this.modal;
        const selectedTextDiv = modal.querySelector('.comment-selected-text');
        const textarea = modal.querySelector('.comment-textarea');
        
        selectedTextDiv.innerHTML = `"${this.currentSelection.text}"`;
        textarea.value = '';
        modal.querySelector('.comment-char-count').textContent = '0/500';
        
        modal.style.display = 'block';
        setTimeout(() => textarea.focus(), 100);
    }

    hideModal() {
        this.modal.style.display = 'none';
        this.currentSelection = null;
        this.hideCommentIcon();
    }

    async submitComment() {
        console.log('submitComment called');
        
        if (this.isSubmitting) return; // Prevent double submission
        
        const textarea = this.modal.querySelector('.comment-textarea');
        const submitBtn = this.modal.querySelector('.comment-submit-btn');
        const commentText = textarea.value.trim();
        
        console.log('Comment text:', commentText);
        console.log('Current selection:', this.currentSelection);
        
        if (!commentText || !this.currentSelection) {
            console.log('Submission blocked - missing text or selection');
            this.showNotification('Please enter a comment', 'error');
            return;
        }
        
        // Show loading state
        this.isSubmitting = true;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
        
        const comment = {
            selectedText: this.currentSelection.text,
            context: this.currentSelection.context,
            comment: commentText,
            metalName: this.getCurrentMetal()
        };
        
        try {
            const response = await fetch('/api/comments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(comment)
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Failed to submit comment');
            }
            
            this.hideModal();
            
            // Refresh comments display
            await this.loadCommentsFromAPI();
            this.displayComments();
            
            // Show success message
            this.showNotification('Comment submitted! It will appear after moderation.');
            
        } catch (error) {
            console.error('Error submitting comment:', error);
            this.showNotification(error.message || 'Failed to submit comment. Please try again.', 'error');
        } finally {
            // Reset loading state
            this.isSubmitting = false;
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Add Comment';
        }
    }

    getCurrentMetal() {
        // Extract metal name from current URL or page state
        const hash = window.location.hash;
        if (hash.includes('reports/')) {
            return hash.split('reports/')[1];
        }
        return 'unknown';
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.textContent = message;
        
        const backgroundColor = type === 'error' ? '#e74c3c' : '#27ae60';
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${backgroundColor};
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            z-index: 3000;
            transition: opacity 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            max-width: 400px;
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, type === 'error' ? 5000 : 3000); // Show errors longer
    }

    async loadCommentsFromAPI() {
        const currentMetal = this.getCurrentMetal();
        if (currentMetal === 'unknown') return;
        
        try {
            const response = await fetch(`/api/comments?metal=${encodeURIComponent(currentMetal)}`);
            if (response.ok) {
                this.comments = await response.json();
            } else {
                console.warn('Failed to load comments:', response.statusText);
                this.comments = [];
            }
        } catch (error) {
            console.error('Error loading comments:', error);
            this.comments = [];
        }
    }

    displayComments() {
        const currentMetal = this.getCurrentMetal();
        const metalComments = this.comments || [];
        
        if (metalComments.length === 0) return;
        
        const reportContent = document.getElementById('report-content');
        if (!reportContent) return;
        
        // Remove existing comments section
        const existingSection = document.querySelector('.community-feedback-section');
        if (existingSection) {
            existingSection.remove();
        }
        
        // Create comments section
        const commentsSection = document.createElement('div');
        commentsSection.className = 'community-feedback-section';
        commentsSection.innerHTML = `
            <hr style="margin: 3rem 0 2rem 0; border: none; border-top: 1px solid #ddd;">
            <h2 style="color: #2c3e50; margin-bottom: 1.5rem;">
                <i class="fas fa-comments" style="margin-right: 0.5rem;"></i>
                Community Feedback (${metalComments.length})
            </h2>
            <div class="comments-list">
                ${metalComments.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                    .map(comment => this.renderComment(comment)).join('')}
            </div>
        `;
        
        reportContent.appendChild(commentsSection);
    }

    renderComment(comment) {
        const date = new Date(comment.timestamp).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="comment-item" style="
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                background: #fafbfc;
            ">
                <div class="comment-context" style="
                    background: #f8f9fa;
                    border-left: 4px solid #3498db;
                    padding: 12px 16px;
                    margin-bottom: 12px;
                    border-radius: 0 4px 4px 0;
                ">
                    <div style="font-weight: 600; color: #2c3e50; margin-bottom: 4px;">
                        ${comment.context.sectionTitle}
                    </div>
                    <div style="font-style: italic; color: #5a6c7d; font-size: 0.9rem;">
                        "${comment.selectedText}"
                    </div>
                </div>
                <div class="comment-text" style="
                    color: #2c3e50;
                    line-height: 1.6;
                    margin-bottom: 12px;
                ">
                    ${comment.comment}
                </div>
                <div class="comment-meta" style="
                    color: #7f8c8d;
                    font-size: 0.85rem;
                ">
                    ${date}
                </div>
            </div>
        `;
    }

}

// Initialize the application
const explorer = new CriticalMineralExplorer();
const app = explorer; // Alias for easier access in onclick handlers
const commentingSystem = new CommentingSystem();

// Make commenting system globally available
window.commentingSystem = commentingSystem;
