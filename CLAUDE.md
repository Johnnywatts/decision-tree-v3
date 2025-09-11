# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project that extracts decision tree data from Miro boards and converts it to Mermaid diagram format. The project focuses on parsing Miro boards containing:

- Start nodes (beginning of decision tree)
- Diamond-shaped question nodes containing decision points
- Connectors labeled with responses/answers
- Final conclusion nodes

The goal is to generate clean Mermaid flowchart diagrams that accurately represent the decision tree structure.

## Project Status

Fully functional with a working pipeline from Miro API to Mermaid diagram generation.

## Setup and Usage

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the complete pipeline:
```bash
# Step 1: Extract data from Miro (creates raw_miro_data.json)
python miro_extractor.py

# Step 2: Generate clean Mermaid diagram
python fixed_mermaid_generator.py
```

This will:
1. Read board ID and API key from `board-details.yaml`
2. Fetch decision tree data from Miro board and save as `raw_miro_data.json`
3. Process the raw data and generate `fixed_decision_tree.mmd` and `fixed_decision_tree.md`

## File Structure

**Core Files:**
- `board-details.yaml` - Contains Miro board ID and API key
- `miro_extractor.py` - Fetches data from Miro API
- `fixed_mermaid_generator.py` - Generates clean Mermaid diagrams
- `requirements.txt` - Python dependencies

**Generated Files:**
- `raw_miro_data.json` - Raw data from Miro API
- `fixed_decision_tree.mmd` - Clean Mermaid flowchart
- `fixed_decision_tree.md` - Markdown with embedded Mermaid diagram

## Architecture

The pipeline works in two stages:

**Stage 1 (miro_extractor.py):**
- Connects to Miro API using credentials from `board-details.yaml`
- Fetches all board items and connectors
- Saves raw JSON data to `raw_miro_data.json`

**Stage 2 (fixed_mermaid_generator.py):**
- Parses raw JSON data
- Identifies node types: Start (stadium), Questions (diamond), Conclusions (stadium)
- Maps connector labels to decision paths
- Generates clean Mermaid flowchart syntax
- Outputs both `.mmd` and `.md` formats