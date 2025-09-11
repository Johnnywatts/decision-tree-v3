# Chat Log 01: Fixing Miro to Mermaid Generation

**Date**: 2025-09-11  
**Task**: Fix Mermaid diagram generation from Miro board data

## Problem Description

User had two versions of code to generate Mermaid diagrams from Miro board data, but neither were working correctly:
1. `miro_extractor.py` (original version)
2. `GPT_raw_to_mermaid.py` (ChatGPT version)

Issues identified:
- Mermaid viewer not working locally, only MD file preview available
- Generated diagrams didn't match the actual decision tree structure
- Node shapes and labels were incorrect

## Solution Process

### 1. Analysis Phase
- Examined both existing Mermaid generation approaches
- Reviewed the exported Miro board image (`DGC Decision Tree_Questions Pathways_v1.1 (1).jpg`)
- Verified `raw_miro_data.json` correctness against the board export
- Identified key issues:
  - Wrong node shapes (everything as rectangles instead of diamonds for questions)
  - Missing or incorrect node labels
  - Poor text extraction from HTML content
  - No proper start node identification

### 2. Board Structure Analysis
From the exported image, the decision tree should have:
- **Start node**: Green stadium shape with "Start" text
- **Question nodes**: Yellow diamond shapes with decision questions
- **Conclusion nodes**: Blue rounded rectangles with specific labels like:
  - "LREC Approval required"
  - "Ethics approval required" 
  - "Seek Advice"
  - "Continue to Research"
  - "Apply via DAP-R"
  - "Contact PO HRA approval required"

### 3. Solution Implementation
Created `fixed_mermaid_generator.py` that combines the best of both approaches:

#### Key Improvements:
1. **Proper HTML text cleaning** (from GPT version)
2. **Correct node shape detection**:
   - Stadium `([...])` for start and conclusion nodes
   - Diamond `{...}` for question nodes (rhombus shapes)
   - Rectangle `[...]` for notes
3. **Accurate conclusion node mapping** based on visual inspection
4. **Better start node identification**

#### Code Structure:
```python
class FixedMermaidGenerator:
    def __init__(self, json_file: str = "raw_miro_data.json")
    def _html_to_text(self, html: str) -> str  # Clean HTML
    def extract_nodes_and_connections(self, data) -> Tuple[Dict, List]
    def sanitize_id(self, raw_id: str) -> str  # Valid Mermaid IDs
    def get_mermaid_shape(self, node_info, text) -> Tuple[str, str]
    def find_start_node(self, nodes, connections) -> str
    def generate_mermaid(self, output_file: str = "fixed_decision_tree.mmd")
```

## Results

### Generated Files:
- `fixed_decision_tree.mmd` - Mermaid diagram file
- `fixed_decision_tree.md` - Markdown file with embedded diagram for preview

### Sample Output:
```mermaid
flowchart TD
    N3458764635301875090(["Start"])
    N3458764635301463439{"Is it Health Care data?"}
    N3458764635301463798{"Is it healthy Volunteer data ?"}
    N3458764635302567244{"Is registration required?"}
    N3458764635302888442(["Continue to Research"])
    N3458764636475175262(["LREC Approval required"])
    N3458764636475175411(["Ethics approval required"])
    
    N3458764635301875090 --> N3458764635301463439
    N3458764635301463439 -->|"YES"| N3458764635301699516
    N3458764635301463439 -->|"NO"| N3458764635301463798
    N3458764635302567244 -->|"YES"| N3458764636475175262
    N3458764635302567244 -->|"NO"| N3458764635302888442
    # ... more connections
```

### Statistics:
- **Nodes extracted**: 21
- **Connections**: 16
- **Node types**: Start (1), Questions (8), Conclusions (8), Notes (4)

## Verification

The generated Mermaid diagram now correctly represents:
✅ Proper node shapes matching the original board  
✅ Accurate decision flow with labeled connections  
✅ Correct start point and conclusion endpoints  
✅ Meaningful labels for all conclusion nodes  

## Files Created/Modified

### New Files:
- `fixed_mermaid_generator.py` - Main solution
- `fixed_decision_tree.mmd` - Generated Mermaid diagram
- `fixed_decision_tree.md` - Markdown preview version

### Existing Files Referenced:
- `raw_miro_data.json` - Source data (verified correct)
- `DGC Decision Tree_Questions Pathways_v1.1 (1).jpg` - Reference board image
- `miro_extractor.py` - Original version (issues identified)
- `GPT_raw_to_mermaid.py` - ChatGPT version (used for inspiration)

## Usage

To generate the fixed Mermaid diagram:
```bash
python3 fixed_mermaid_generator.py
```

This will create both `.mmd` and `.md` files that can be previewed in markdown viewers since the local Mermaid viewer is not working.

## Technical Notes

### Node ID Mapping Strategy:
- Miro uses numeric IDs that aren't valid Mermaid identifiers
- Solution: Prefix with 'N' and sanitize special characters
- Example: `3458764635301463439` → `N3458764635301463439`

### Shape Detection Logic:
- `item.type == 'shape'` and `data.shape == 'rhombus'` → Diamond question node
- `item.id == '3458764635301875090'` → Start node (specific ID)
- Empty shapes with mapped IDs → Conclusion nodes with proper labels
- `item.type == 'sticky_note'` → Rectangular note nodes

### Connection Labeling:
- Extract from `connector.captions[].content`
- Clean HTML and handle multiple captions
- Format as `A -->|"label"| B` in Mermaid syntax

This solution successfully fixed both the visual representation and the logical flow of the decision tree diagram.