#!/usr/bin/env python3
"""
deepresearch_detailed_reports.py

Deep Research API wrapper for enhancing detailed mineral/metal reports with citations.
Preserves the exact structure while adding peer-reviewed links and latest news.

USAGE
-----
# Single file
python deepresearch_detailed_reports.py --file ./detailed_reports/gadolinium_report.md

# Process all *.md files in detailed_reports directory
python deepresearch_detailed_reports.py --dir ./detailed_reports

# Speed/quality control
python deepresearch_detailed_reports.py --file report.md --quality high

ENV
---
Set OPENAI_API_KEY in your environment or a .env file.
Requires: openai>=1.40.0, python-dotenv
"""

import os
import sys
import time
import argparse
from pathlib import Path
from textwrap import dedent
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

try:
    import openai
except ImportError as e:
    raise SystemExit("❌ The 'openai' package is required. Install with: pip install --upgrade openai")

# Configuration
MODEL_FAST = "o4-mini-deep-research-2025-06-26"
MODEL_HIGH = "o3-deep-research-2025-06-26"
MAX_OUTPUT = 200000
RETRY_LIMIT = 6
TIMEOUT_SECONDS = 45 * 60  # 45 minutes


def call_with_backoff(client: openai.OpenAI, **kwargs):
    """Retry the request with exponential back-off on rate-limit errors."""
    for attempt in range(RETRY_LIMIT):
        try:
            if attempt == 0:
                time.sleep(1.05)
            return client.responses.create(**kwargs)
        except openai.RateLimitError:
            wait = 2 ** attempt
            print(f"Rate-limited (attempt {attempt+1}/{RETRY_LIMIT}), sleeping {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Exceeded retry limit due to persistent rate-limits")


def build_prompt(report_text: str, material_name: str) -> str:
    """Build the user prompt for Deep Research."""
    return dedent(f"""
        Material/Metal: {material_name}

        --- BEGIN DETAILED REPORT ---
        {report_text}
        --- END DETAILED REPORT ---

        REQUIREMENTS:
        - PRESERVE THE EXACT STRUCTURE: Keep all existing section headers and subsections exactly as they are
        - Verify every factual assertion (production volumes, capacity figures, technical specifications) and correct errors
        - Add inline citations in markdown as ([LastAuthor et al., Year](DOI-or-URL)) for each data point and technical claim
        - Replace any missing or placeholder references with real, peer-reviewed citations
        - Include latest industry news and developments (2023-2025) where relevant
        - For production/demand figures, cite authoritative sources (USGS, industry reports, company filings)
        - For technical processes, cite peer-reviewed papers, patents, or technical handbooks
        - Keep the same approximate length for each section
        - Use reliable sources: peer-reviewed journals, government agencies (USGS, DOE, EU Commission), industry reports
        - If a fact is uncertain or contested, briefly state the uncertainty and provide multiple citations
        - Add recent news about projects, facilities, or technology developments mentioned
        - Ensure all links are real, working URLs (DOIs, PubMed, agency websites, company reports)

        SPECIFIC FOCUS AREAS:
        - Production/supply/demand volumes: Verify against latest USGS, company reports, trade data
        - Technology descriptions: Add patent numbers and research papers
        - Company/project information: Include latest updates from press releases and investor presentations
        - Environmental/regulatory aspects: Cite relevant legislation and agency reports

        CRITICAL OUTPUT REQUIREMENTS:
        - Start your output with the first section header from the original report
        - DO NOT include any task checklist, bullet points, or explanatory text before the report content
        - DO NOT add any preamble, introduction, or task description
        - The first line of your output should be "## Key Bottleneck technology..." or whatever the first section header is
        - Return ONLY the enhanced report content, starting with the first section and ending with the last section

        Output: Return ONLY the enhanced markdown report starting with the first section header. No checklists, no preamble, no commentary.

    """).strip()


def extract_content(response) -> str:
    """Extract the markdown content from the response."""
    if not response.output:
        raise RuntimeError("No output in response")

    # Look for content in the output items - skip reasoning, find actual response
    for item in response.output:
        # Skip reasoning items
        if hasattr(item, 'type') and item.type == 'reasoning':
            continue

        # Check if this item has text content
        if hasattr(item, 'text') and item.text:
            return str(item.text)

        # Check if this item has content field
        if hasattr(item, 'content') and item.content:
            if isinstance(item.content, list) and len(item.content) > 0:
                first_content = item.content[0]
                if hasattr(first_content, 'text'):
                    return first_content.text

    raise RuntimeError("Could not find output content in the response")


def improve_report(file_path: Path, quality: str = "fast") -> None:
    """Improve a single detailed report file using Deep Research."""
    # Load environment
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("❌ OPENAI_API_KEY not found. Set it in env or a .env file.")

    client = openai.OpenAI(api_key=api_key)

    # Read the report file
    print(f"📄 Processing: {file_path}")
    report_text = file_path.read_text(encoding="utf-8")

    # Extract material name from filename (e.g., gadolinium_report.md -> gadolinium)
    material_name = file_path.stem.replace("_report", "").replace("_", " ").title()
    print(f"📦 Material: {material_name}")

    # Create backup
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    if not backup_path.exists():
        backup_path.write_text(report_text, encoding="utf-8")
        print(f"💾 Backup saved: {backup_path}")

    # Choose model
    model = MODEL_HIGH if quality == "high" else MODEL_FAST
    print(f"🧠 Calling Deep Research: model={model}")

    # Build the request
    prompt = build_prompt(report_text, material_name)

    # Submit Deep Research request
    response = call_with_backoff(
        client,
        model=model,
        input=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": dedent("""
                            You are an expert materials scientist and industry analyst specializing in critical minerals
                            and strategic metals. Your task is to enhance a detailed technical report by:

                            1. Rigorously verifying each factual assertion (production volumes, technical specs, company data)
                            2. Providing accurate citations from peer-reviewed sources, industry reports, and government data
                            3. Adding the latest industry developments and news (2023-2025)
                            4. Correcting any errors or outdated information
                            5. Maintaining the exact document structure and section organization

                            You have deep expertise in:
                            - Mining and extraction technologies
                            - Hydrometallurgical and pyrometallurgical processing
                            - Supply chain analysis and market forecasting
                            - Environmental remediation and regulatory compliance
                            - Critical minerals policy and strategic implications

                            Focus on accuracy, currency, and comprehensive citation of all claims.
                        """).strip(),
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
        background=True,
    )

    print(f"🔄 Deep research started. Response ID: {response.id}")
    print("⏳ Polling for completion...")

    # Poll for completion
    start_time = time.time()
    last_output_count = 0

    while response.status != "completed":
        elapsed_time = time.time() - start_time
        if elapsed_time > TIMEOUT_SECONDS:
            raise RuntimeError(f"Deep research timed out after {TIMEOUT_SECONDS} seconds")

        if response.status == "failed":
            print(f"❌ Deep research failed. Status: {response.status}")
            if hasattr(response, 'error') and response.error:
                print(f"Error: {response.error}")
            raise RuntimeError(f"Deep research failed with status: {response.status}")

        # Show progress
        current_output_count = len(response.output) if response.output else 0
        if current_output_count > last_output_count:
            print(f"📈 Progress: {current_output_count} output chunks")
            last_output_count = current_output_count

        print(f"⏱️  Status: {response.status}, elapsed: {elapsed_time:.0f}s, waiting...")
        time.sleep(10)
        response = client.responses.retrieve(response.id)

    print("✅ Deep research completed!")

    # Extract the improved content
    improved_text = extract_content(response)

    # Save the improved version, overwriting the original
    file_path.write_text(improved_text, encoding="utf-8")

    print(f"✅ Enhanced report saved: {file_path}")
    print(f"📊 Original: {len(report_text)} chars → Enhanced: {len(improved_text)} chars")


def main():
    parser = argparse.ArgumentParser(description="Enhance detailed reports with Deep Research API citations")

    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", type=str, help="Path to a single markdown report file")
    src.add_argument("--dir", type=str, help="Directory containing report *.md files")
    src.add_argument("--all", action="store_true", help="Process all reports in detailed_reports/ (skip files modified in past week)")

    parser.add_argument("--quality", choices=["fast", "high"], default="fast",
                       help="Deep Research quality (fast=o4-mini, high=o3)")

    args = parser.parse_args()

    # Collect target files
    targets = []
    if args.file:
        targets = [Path(args.file)]
    elif args.all:
        # Process all files in detailed_reports directory, skipping recently modified ones
        directory = Path("./detailed_reports")
        if not directory.exists():
            raise SystemExit("❌ detailed_reports directory not found")

        one_week_ago = datetime.now() - timedelta(days=7)
        all_reports = sorted([p for p in directory.glob("*_report.md") if p.is_file()])

        # Filter out files modified in the past week
        targets = []
        skipped = []
        for report in all_reports:
            mod_time = datetime.fromtimestamp(report.stat().st_mtime)
            if mod_time < one_week_ago:
                targets.append(report)
            else:
                skipped.append(report)

        if skipped:
            print(f"⏭️  Skipping {len(skipped)} recently modified reports (< 1 week old):")
            for s in skipped:
                print(f"   - {s.name}")
            print()
    else:
        directory = Path(args.dir)
        # Get all markdown files in the directory
        targets = sorted([p for p in directory.glob("*.md") if p.is_file()])

    if not targets:
        raise SystemExit("❌ No markdown files found to process")

    # Process each file
    print(f"🎯 Found {len(targets)} report(s) to process")

    for i, file_path in enumerate(targets, 1):
        try:
            print("=" * 80)
            print(f"📋 Processing {i}/{len(targets)}: {file_path.name}")
            improve_report(file_path, args.quality)
        except Exception as e:
            print(f"❌ Failed to process {file_path}: {e}")
            continue


if __name__ == "__main__":
    main()