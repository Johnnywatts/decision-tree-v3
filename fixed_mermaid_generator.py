#!/usr/bin/env python3
"""
Fixed Mermaid generator that combines the best approaches from both versions.
"""
import json
import re
from html import unescape
from typing import Dict, List, Any, Tuple

class FixedMermaidGenerator:
    def __init__(self, json_file: str = "raw_miro_data.json"):
        self.json_file = json_file
        
    def _html_to_text(self, html: str) -> str:
        """Clean HTML tags and formatting from text."""
        if not html:
            return ""
        # Remove line breaks tags turned into newlines
        text = re.sub(r"<(br|/p)>", "\n", html, flags=re.I)
        # Remove all remaining tags
        text = re.sub(r"<[^>]+>", "", text)
        text = unescape(text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def load_data(self) -> Dict[str, Any]:
        """Load JSON data from file."""
        with open(self.json_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_nodes_and_connections(self, data: Dict[str, Any]) -> Tuple[Dict[str, Dict], List[Tuple[str, str, str]]]:
        """Extract nodes with proper types and connections from Miro data."""
        nodes = {}
        connections = []
        
        # Map of conclusion node texts based on visual inspection of the board
        conclusion_text_map = {
            # These are the blue rounded conclusion nodes from the board
            '3458764636475175262': 'LREC Approval required',  # YES from registration
            '3458764635302888442': 'Continue to Research',  # NO from registration  
            '3458764636474796545': 'Apply via DAP-R',  # Pseudonymised/Anonymised
            '3458764636474951140': 'Contact PO HRA approval required',  # Identifiers
            '3458764636474951421': 'Contact PO HRA approval required',  # Observational/Interventional
            '3458764636474951443': 'Seek Advice',  # I don't know
            '3458764636475175178': 'Seek Advice',  # NO from specific data
            '3458764636475175411': 'Ethics approval required',  # YES from healthy volunteer
        }
        
        # Extract nodes from items
        for item in data.get('items', []):
            item_id = item.get('id')
            if not item_id:
                continue
                
            item_type = item.get('type')
            if item_type not in ['shape', 'sticky_note', 'text']:
                continue
                
            # Determine node type and content
            node_info = {'text': '', 'mermaid_shape': 'rectangle', 'type': 'unknown'}
            
            if item_type == 'shape':
                shape_data = item.get('data', {})
                content = self._html_to_text(shape_data.get('content', ''))
                shape_type = shape_data.get('shape', 'rectangle')
                
                if shape_type == 'rhombus':
                    # Decision/question nodes
                    node_info['type'] = 'question'
                    node_info['mermaid_shape'] = 'diamond'
                    node_info['text'] = content
                elif item_id == '3458764635301875090':
                    # Start node (specific ID from board)
                    node_info['type'] = 'start'
                    node_info['mermaid_shape'] = 'stadium'
                    node_info['text'] = 'Start'
                elif content:
                    # Regular content nodes
                    node_info['type'] = 'process'
                    node_info['mermaid_shape'] = 'rectangle'
                    node_info['text'] = content
                else:
                    # Empty shapes are end nodes - use mapped text if available
                    node_info['type'] = 'conclusion'
                    node_info['mermaid_shape'] = 'stadium'  # Blue rounded rectangles in image
                    node_info['text'] = conclusion_text_map.get(item_id, 'Conclusion')
                    
            elif item_type == 'sticky_note':
                content = self._html_to_text(item.get('data', {}).get('content', ''))
                node_info['type'] = 'note'
                node_info['mermaid_shape'] = 'rectangle'
                node_info['text'] = content if content else 'Note'
                
            elif item_type == 'text':
                content = self._html_to_text(item.get('data', {}).get('content', ''))
                if content and not content.lower().startswith('decision tree'):
                    # Skip title/header text
                    node_info['type'] = 'text'
                    node_info['mermaid_shape'] = 'rectangle'
                    node_info['text'] = content
                else:
                    continue  # Skip title text
                    
            # Only add node if it has meaningful content or is a mapped conclusion
            if (node_info['text'] and node_info['text'] != 'shape') or item_id in conclusion_text_map:
                nodes[item_id] = node_info
        
        # Extract connections
        for conn in data.get('connectors', []):
            start_item = conn.get('startItem', {})
            end_item = conn.get('endItem', {})
            start_id = start_item.get('id')
            end_id = end_item.get('id')
            
            if not start_id or not end_id:
                continue
                
            # Get connection label from captions
            label = ''
            captions = conn.get('captions', [])
            if captions:
                caption_texts = []
                for caption in captions:
                    caption_text = self._html_to_text(caption.get('content', ''))
                    if caption_text:
                        caption_texts.append(caption_text)
                label = ' / '.join(caption_texts)
                
            connections.append((start_id, end_id, label))
            
        return nodes, connections

    def sanitize_id(self, raw_id: str) -> str:
        """Generate valid Mermaid node ID."""
        if re.match(r"^[A-Za-z_]", raw_id):
            base = raw_id
        else:
            base = "N" + raw_id
        # Remove problematic characters
        base = re.sub(r"[^0-9A-Za-z_]+", "_", base)
        return base

    def get_mermaid_shape(self, node_info: Dict[str, Any], text: str) -> Tuple[str, str]:
        """Get Mermaid shape syntax for node."""
        shape_type = node_info['mermaid_shape']
        
        # More aggressive text cleaning for Mermaid
        safe_text = text.replace('"', "'").replace('\n', ' ').replace('<', '&lt;').replace('>', '&gt;').strip()
        # Remove other problematic characters
        safe_text = re.sub(r'[{}()\[\]]', '', safe_text)
        if len(safe_text) > 50:
            safe_text = safe_text[:47] + "..."
            
        if shape_type == 'diamond':
            return '{', f'"{safe_text}"' + '}'
        elif shape_type == 'stadium':
            return '([', f'"{safe_text}"' + '])'
        else:  # rectangle
            return '[', f'"{safe_text}"' + ']'

    def find_start_node(self, nodes: Dict[str, Dict], connections: List[Tuple[str, str, str]]) -> str:
        """Find the actual start node."""
        # First, find nodes that have no incoming connections
        target_ids = set()
        for start_id, end_id, _ in connections:
            target_ids.add(end_id)
            
        start_candidates = []
        for node_id, node_info in nodes.items():
            if node_id not in target_ids:
                start_candidates.append((node_id, node_info))
                
        # Prefer nodes marked as 'start' type or with 'start' in text
        for node_id, node_info in start_candidates:
            if (node_info['type'] == 'start' or 
                'start' in node_info['text'].lower()):
                return node_id
                
        # If no clear start node, return the first candidate
        if start_candidates:
            return start_candidates[0][0]
            
        # Fallback: return first node
        return list(nodes.keys())[0] if nodes else None

    def generate_mermaid(self, output_file: str = "fixed_decision_tree.mmd"):
        """Generate the fixed Mermaid diagram."""
        data = self.load_data()
        nodes, connections = self.extract_nodes_and_connections(data)
        
        if not nodes:
            print("No nodes found!")
            return
            
        # Create ID mapping
        id_map = {orig_id: self.sanitize_id(orig_id) for orig_id in nodes.keys()}
        
        # Find start node
        start_node_id = self.find_start_node(nodes, connections)
        
        # Generate Mermaid content
        mermaid_lines = ['flowchart TD']
        
        # Add start node first if found
        if start_node_id and start_node_id in nodes:
            node_info = nodes[start_node_id]
            mermaid_id = id_map[start_node_id]
            shape_start, shape_end = self.get_mermaid_shape(node_info, node_info['text'])
            mermaid_lines.append(f'    {mermaid_id}{shape_start}{shape_end}')
            
        # Add all other nodes
        for node_id, node_info in nodes.items():
            if node_id == start_node_id:
                continue  # Already added
                
            mermaid_id = id_map[node_id]
            shape_start, shape_end = self.get_mermaid_shape(node_info, node_info['text'])
            mermaid_lines.append(f'    {mermaid_id}{shape_start}{shape_end}')
        
        # Add blank line
        mermaid_lines.append('')
        
        # Add connections
        for start_id, end_id, label in connections:
            if start_id not in id_map or end_id not in id_map:
                continue
                
            start_mermaid = id_map[start_id]
            end_mermaid = id_map[end_id]
            
            if label:
                # Clean label for Mermaid - be more aggressive
                clean_label = label.replace('"', "'").replace('<', '').replace('>', '').strip()
                clean_label = re.sub(r'[{}()\[\]]', '', clean_label)
                if len(clean_label) > 30:
                    clean_label = clean_label[:27] + "..."
                mermaid_lines.append(f'    {start_mermaid} -->|"{clean_label}"| {end_mermaid}')
            else:
                mermaid_lines.append(f'    {start_mermaid} --> {end_mermaid}')
        
        # Write to file
        mermaid_content = '\n'.join(mermaid_lines)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_content)
            
        print(f"Generated fixed Mermaid diagram: {output_file}")
        print(f"Nodes: {len(nodes)}, Connections: {len(connections)}")
        
        # Also generate markdown version
        md_file = output_file.replace('.mmd', '.md')
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# Fixed Decision Tree Diagram\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_content)
            f.write("\n```\n")
                
        print(f"Also generated: {md_file}")

def main():
    generator = FixedMermaidGenerator()
    generator.generate_mermaid()

if __name__ == '__main__':
    main()