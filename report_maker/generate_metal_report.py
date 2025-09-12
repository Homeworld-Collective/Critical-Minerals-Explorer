"""
generate_metal_report.py (v1.0)
----------------------------------
Generate a Deep‑Research report for any critical mineral supply‑chain
and emit an enhanced summary‑row.

USAGE
=====
$ export OPENAI_API_KEY="sk‑..."
$ python generate_metal_report.py <metal_name>
"""

from __future__ import annotations

import os
import re
import sys
import time
import json
import pandas as pd
from pathlib import Path

import openai

###############################################################################
# 1.  CONFIGURATION
###############################################################################

MODEL_NAME   = "o4-mini-deep-research-2025-06-26"
MAX_OUTPUT   = 200000          # tokens to reserve for the model's answer (very high for deep research)
RETRY_LIMIT  = 6               # exponential back‑off: 1 s ➜ 32 s (≈ 1 min total)

HEADERS = [
    "Metal",
    "Percentage on US and Allies Domestic Supply for Demand 2030",
    "US and Allies Domestic Current Production (tons)",
    "US and Allies Domestic Demand 2030 (tons)",
    "US and Allies Domestic Supply 2030 (tons)",
    "References for volumes",
    "Key Discovery Technologies",
    "Key Extraction Technologies",
    "Key Separation Technologies",
    "Key Purification & Refinement Technologies",
    "Key Remediation Technologies",
    "References for mining technologies",
    "Key Bottleneck technology for US and Allies Domestic Production ",
    "Key Bottleneck summary (2-4 sentences)",
]

###############################################################################
# 2.  HELPER FUNCTIONS
###############################################################################

def get_metal_data(metal_name: str) -> dict:
    """Load metal data from the MSHA analysis CSV files."""
    # Get the parent directory (repository root)
    repo_root = Path(__file__).parent.parent
    csv_path = repo_root / f"msha_scraper/msha_critical_metals_analysis/analysis_results/individual_metals/{metal_name}_analysis.csv"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"No data found for metal: {metal_name}")
    
    # Read the CSV data
    try:
        df = pd.read_csv(csv_path)
        
        # Basic info about the metal's mining status
        if len(df) == 0 or (len(df) == 1 and df.iloc[0]['mine_name'] == f'No active {metal_name} mines in US'):
            production_status = "No active US production"
            mine_count = 0
            total_production = 0
        else:
            production_status = "Active US production"
            mine_count = len(df)
            total_production = df['estimated_annual_production_mt'].sum() if 'estimated_annual_production_mt' in df.columns else 0
        
        return {
            "metal": metal_name.title(),
            "production_status": production_status,
            "mine_count": mine_count,
            "total_estimated_production_mt": total_production,
            "data_source": str(csv_path)
        }
    except Exception as e:
        print(f"Error reading data for {metal_name}: {e}")
        return {
            "metal": metal_name.title(),
            "production_status": "Data unavailable", 
            "mine_count": 0,
            "total_estimated_production_mt": 0,
            "data_source": str(csv_path)
        }


def build_prompt(metal_name: str, metal_data: dict) -> str:
    """Compose the user prompt for the Deep‑Research call."""
    metal_title = metal_name.title()
    
    # Create structured sections based on HEADERS (starting from index 2)
    sections = []
    for i in range(2, len(HEADERS)):
        header = HEADERS[i]
        sections.append(f"## {header}\n[Detailed technical analysis with specific data, numbers, companies, locations, and citations]")
    
    sections_template = "\n\n".join(sections)
    
    # Add context about current US production status
    production_context = f"""
CURRENT US PRODUCTION CONTEXT:
- Metal: {metal_title}
- US Production Status: {metal_data['production_status']}
- Number of US mines: {metal_data['mine_count']}
- Estimated total US production: {metal_data['total_estimated_production_mt']:.1f} MT/year
"""
    
    return f"""I need a comprehensive deep research report on {metal_title} supply chain analysis for US and allied nations.

{production_context}

Please structure your response with these exact sections:

{sections_template}

REQUIREMENTS:
- Include specific production volumes, company names, locations, technologies
- Provide detailed technical explanations like the lanthanum example
- Use bullet points (•) for multiple technologies/methods within sections  
- Focus on US and allies (US, Canada, Australia, EU, Norway, Iceland, Japan)
- Include proper citations with sources and dates
- Match the technical depth and quality of professional supply chain analysis
- If US production is minimal/zero, focus on allied production and import dependencies

EXAMPLE QUALITY (follow this style):
"• Radiometric Surveys: Many rare earth deposits contain thorium or uranium. Airborne radiometric surveys measuring natural gamma radiation can highlight REE prospects by detecting associated radioactive minerals. In fact, numerous rare earth deposits (e.g. Mt. Weld in Australia) were discovered during U/Th exploration.• Geological Mapping & Geochemistry: Mapping identifies carbonatite intrusions, pegmatites, or ion-adsorption clay basins that could host REEs. Geochemical sampling of stream sediments or soils can find anomalies in elements like cerium, lanthanum, or yttrium, which indicate REE mineralization."

Provide the complete technical research report now."""


def call_with_backoff(client: openai.OpenAI, **kwargs):
    """Retry the request with exponential back‑off on rate‑limit errors."""
    for attempt in range(RETRY_LIMIT):
        try:
            # Gentle 1‑second pacing helps keep total RPM low.
            if attempt == 0:
                time.sleep(1.05)
            return client.responses.create(**kwargs)
        except openai.RateLimitError:
            wait = 2 ** attempt
            print(f"Rate‑limited (attempt {attempt+1}/{RETRY_LIMIT}), "
                  f"sleeping {wait}s …")
            time.sleep(wait)
    raise RuntimeError("Exceeded retry limit due to persistent rate‑limits")


def create_summary_json(markdown_report: str, metal_name: str) -> dict:
    """Create a summary JSON with concise summaries for each section."""
    summary_data = {
        "metal": metal_name.title(),
        "sections": {}
    }
    
    # Split the markdown into sections based on headers
    sections = re.split(r'^#\s+(.+)$', markdown_report, flags=re.MULTILINE)
    
    # Process sections (odd indices are headers, even indices are content)
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            header = sections[i].strip()
            content = sections[i + 1].strip()
            
            # Clean up content - remove excessive newlines, bullets, etc.
            content = re.sub(r'\n+', ' ', content)
            content = re.sub(r'•\s*', '• ', content)
            content = re.sub(r'\s+', ' ', content)
            
            # Create a more meaningful summary - first sentence or two, up to 300 characters
            sentences = content.split('. ')
            summary = sentences[0]
            if len(sentences) > 1 and len(summary) < 200:
                summary += '. ' + sentences[1]
            
            # Trim to reasonable length
            if len(summary) > 300:
                summary = summary[:297] + "..."
            elif not summary.endswith('.') and not summary.endswith('...'):
                summary += "."
            
            summary_data["sections"][header] = summary
    
    # If no structured sections found, create a general summary
    if not summary_data["sections"]:
        summary_data["sections"]["general"] = markdown_report[:500].strip()
        if len(markdown_report) > 500:
            summary_data["sections"]["general"] += "..."
    
    return summary_data


###############################################################################
# 3.  MAIN SCRIPT
###############################################################################

def main(metal_name: str) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not found. Export it or place it in your environment."
        )

    client = openai.OpenAI(api_key=api_key)
    
    # Get metal data
    print(f"Loading data for {metal_name}...")
    metal_data = get_metal_data(metal_name)
    print(f"Status: {metal_data['production_status']}, Mines: {metal_data['mine_count']}")

    # Test API access first
    print("Testing API access...")
    try:
        models = client.models.list()
        available_models = [model.id for model in models.data if 'o3' in model.id or 'deep' in model.id]
        print(f"Available O3/Deep Research models: {available_models}")
        if not available_models:
            print("WARNING: No O3 or Deep Research models found. You may need higher API tier access.")
            print("Available models contain:", [model.id for model in models.data][:10])
    except Exception as e:
        print(f"Error checking models: {e}")

    print(f"Submitting Deep‑Research request for {metal_name}...")
    prompt = build_prompt(metal_name, metal_data)
    print(f"Prompt length: {len(prompt)} characters")
    
    # Use background mode for deep research as recommended by OpenAI
    response = call_with_backoff(
        client,
        model=MODEL_NAME,
        input=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are a professional metals engineer and supply‑chain analyst. "
                            "Produce rigorous, well‑structured, citation‑rich reports with specific data, numbers, "
                            "companies, locations, and technical details. Follow the exact structure requested. "
                            "Provide detailed technical analysis like professional supply chain reports."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            },
        ],
        tools=[{"type": "web_search_preview"}],
        max_output_tokens=MAX_OUTPUT,
        background=True,  # Enable background mode for deep research
    )
    
    print(f"Deep research started. Response ID: {response.id}")
    print("Polling for completion...")
    
    # Poll for completion with very high timeout and show intermediate results
    start_time = time.time()
    timeout_seconds = 7200  # 2 hours timeout (deep research can take a long time)
    last_output_count = 0
    
    while response.status != "completed":
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout_seconds:
            raise RuntimeError(f"Deep research timed out after {timeout_seconds} seconds")
            
        if response.status == "failed":
            print(f"Deep research failed. Error details:")
            if hasattr(response, 'error') and response.error:
                print(f"Error: {response.error}")
            if hasattr(response, 'incomplete_details') and response.incomplete_details:
                print(f"Incomplete details: {response.incomplete_details}")
            raise RuntimeError(f"Deep research failed with status: {response.status}")
        
        # Show intermediate progress and outputs
        current_output_count = len(response.output) if response.output else 0
        if current_output_count > last_output_count:
            print(f"\n--- NEW ACTIVITY (Total outputs: {current_output_count}) ---")
            # Show the latest output items
            for i in range(last_output_count, current_output_count):
                item = response.output[i]
                if hasattr(item, 'type'):
                    if item.type == "reasoning":
                        print(f"🧠 Reasoning step {i+1}")
                        if hasattr(item, 'summary') and item.summary:
                            for j, summary_item in enumerate(item.summary[:2]):  # Show first 2 summary items
                                if hasattr(summary_item, 'text'):
                                    preview = summary_item.text[:150] + "..." if len(summary_item.text) > 150 else summary_item.text
                                    print(f"   • {preview}")
                    elif item.type == "web_search_call":
                        print(f"🔍 Web search {i+1}")
                        if hasattr(item, 'action') and 'query' in item.action:
                            print(f"   Query: {item.action['query']}")
                        print(f"   Status: {getattr(item, 'status', 'unknown')}")
                    else:
                        print(f"📄 {item.type} step {i+1}")
            print("--- End of new activity ---\n")
            last_output_count = current_output_count
        
        print(f"Status: {response.status}, elapsed: {elapsed_time:.0f}s, outputs: {current_output_count}, waiting 10 seconds...")
        time.sleep(10)  # Slightly longer interval since we're showing more info
        response = client.responses.retrieve(response.id)
        
    print("🎉 Deep research completed!")

    # Extract the markdown report from the response
    markdown_report = None
    
    # Debug: Print all output items to understand structure
    print(f"Total output items: {len(response.output)}")
    for i, item in enumerate(response.output):
        print(f"Item {i}: type={getattr(item, 'type', 'unknown')}, class={type(item).__name__}")
        if hasattr(item, 'summary') and item.summary:
            print(f"  - has summary with {len(item.summary)} items")
        if hasattr(item, 'text') and item.text:
            print(f"  - has text: {str(item.text)[:100]}...")
        if hasattr(item, 'content') and item.content:
            print(f"  - has content: {type(item.content)}")
    
    # Look for content in the output items - try different approaches
    for item in response.output:
        # Skip reasoning items, look for actual response content
        if hasattr(item, 'type') and item.type == 'reasoning':
            continue
            
        # Check if this item has text content
        if hasattr(item, 'text') and item.text:
            markdown_report = str(item.text)
            print(f"Found text content: {markdown_report[:200]}...")
            break
            
        # Check if this item has content field
        if hasattr(item, 'content') and item.content:
            if isinstance(item.content, list) and len(item.content) > 0:
                first_content = item.content[0]
                if hasattr(first_content, 'text'):
                    markdown_report = first_content.text
                    print(f"Found content text: {markdown_report[:200]}...")
                    break
    
    # Fallback: if no proper content found, try reasoning summaries but warn user
    if not markdown_report:
        print("WARNING: No proper research content found, falling back to reasoning summaries")
        for item in response.output:
            if hasattr(item, 'summary') and item.summary:
                summary_texts = []
                for summary_item in item.summary:
                    if hasattr(summary_item, 'text'):
                        summary_texts.append(summary_item.text)
                if summary_texts:
                    markdown_report = '\n\n'.join(summary_texts)
                    break
    
    if not markdown_report:
        raise RuntimeError("Could not find output message with content in the response")
    
    # Set up output paths
    repo_root = Path(__file__).parent.parent
    detailed_reports_dir = repo_root / "detailed_reports"
    detailed_reports_dir.mkdir(exist_ok=True)
    
    report_file = detailed_reports_dir / f"{metal_name}_report.md"
    summary_file = detailed_reports_dir / f"summary_{metal_name.lower()}.json"
    
    # Save the structured markdown report
    report_file.write_text(markdown_report, encoding="utf-8")
    print(f"✓ Full report saved to {report_file.resolve()}")
    
    # Create and save the summary JSON
    summary_data = create_summary_json(markdown_report, metal_name)
    summary_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    print(f"✓ Summary JSON saved to {summary_file.resolve()}")
    
    # Print a preview of the summary
    print(f"\n---\nSummary for {metal_name.title()}:\n")
    for header, summary in summary_data["sections"].items():
        print(f"{header}: {summary}")
    print("\n---")

###############################################################################
# 4.  ENTRY POINT
###############################################################################

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_metal_report.py <metal_name>")
        print("Example: python generate_metal_report.py lithium")
        sys.exit(1)
    
    metal_name = sys.argv[1].lower()
    main(metal_name)
