# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project that aims to extract decision tree data from Miro boards and convert it to a YAML format suitable for building interactive web decision trees. The project focuses on parsing Miro boards containing:

- Start nodes (beginning of decision tree)
- Diamond-shaped question nodes containing decision points
- Connectors labeled with responses/answers
- Final conclusion nodes

The goal is to generate a Python-friendly file format (YAML) that captures the decision tree structure for later use in web applications.

## Project Status

This appears to be an early-stage project with only a README file present. No code, dependencies, or build system has been implemented yet.

## Setup and Usage

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the extraction:
```bash
python miro_extractor.py
```

This will:
1. Read board ID and API key from `board-details.yaml`
2. Fetch decision tree data from Miro board
3. Generate `decision_tree.yaml` with structured data
4. Generate `decision_tree.mmd` with Mermaid flowchart

## File Structure

- `board-details.yaml` - Contains Miro board ID and API key
- `miro_extractor.py` - Main extraction script
- `decision_tree.yaml` - Generated YAML decision tree structure
- `decision_tree.mmd` - Generated Mermaid flowchart

## Architecture

The extractor identifies:
- Start nodes (shapes that have no incoming connections)
- Question nodes (diamond shapes)
- Conclusion nodes (sticky notes)
- Connectors with labels (decision paths)

Output formats:
- YAML: Structured decision tree with nodes, types, and options
- Mermaid: Flowchart diagram with proper node shapes and labeled edges