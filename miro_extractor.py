#!/usr/bin/env python3

import requests
import yaml
from typing import Dict, List, Any

class MiroDecisionTreeExtractor:
    def __init__(self, api_key: str, board_id: str):
        self.api_key = api_key
        self.board_id = board_id
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean HTML tags and formatting from text."""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def fetch_all_paginated(self, url: str) -> List[Dict[str, Any]]:
        """Fetch all items from paginated API endpoint."""
        all_data = []
        cursor = ""
        
        while True:
            params = {'limit': 50}
            if cursor:
                params['cursor'] = cursor
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            all_data.extend(data.get('data', []))
            
            # Check if there's more data
            links = data.get('links', {})
            if 'next' not in links:
                break
                
            # Extract cursor from next URL
            next_url = links['next']
            if 'cursor=' in next_url:
                cursor = next_url.split('cursor=')[1]
            else:
                break
        
        return all_data

    def fetch_board_items(self) -> List[Dict[str, Any]]:
        """Fetch all items from the Miro board."""
        url = f'https://api.miro.com/v2/boards/{self.board_id}/items'
        return self.fetch_all_paginated(url)
    
    def fetch_connectors(self) -> List[Dict[str, Any]]:
        """Fetch all connectors from the Miro board."""
        url = f'https://api.miro.com/v2/boards/{self.board_id}/connectors'
        return self.fetch_all_paginated(url)
    
    def parse_decision_tree(self) -> Dict[str, Any]:
        """Parse Miro board items into a decision tree structure."""
        items = self.fetch_board_items()
        connectors = self.fetch_connectors()
        
        # Categorize items by type and shape
        start_nodes = []
        question_nodes = []
        conclusion_nodes = []
        
        for item in items:
            if item['type'] == 'sticky_note':
                # Sticky notes are conclusions
                conclusion_nodes.append({
                    'id': item['id'],
                    'text': self._clean_text(item.get('data', {}).get('content', 'No content')),
                    'position': item.get('position', {})
                })
            elif item['type'] == 'shape':
                # Check if shape has content (questions) or not (conclusions)
                has_content = 'data' in item and 'content' in item['data']
                
                if has_content:
                    shape_type = item.get('data', {}).get('shape', 'unknown')
                    text_content = self._clean_text(item.get('data', {}).get('content', ''))
                    
                    # Rhombus shapes are questions
                    if shape_type == 'rhombus':
                        question_nodes.append({
                            'id': item['id'],
                            'text': text_content,
                            'position': item.get('position', {})
                        })
                    else:
                        # Other shapes with content are start nodes
                        start_nodes.append({
                            'id': item['id'],
                            'text': text_content,
                            'position': item.get('position', {})
                        })
                else:
                    # Shapes without content are conclusion nodes
                    conclusion_nodes.append({
                        'id': item['id'],
                        'text': 'Conclusion',  # Default text for conclusion nodes
                        'position': item.get('position', {})
                    })
            elif item['type'] == 'text':
                # Text items are titles/headers, skip them
                continue
        
        # Build connection map
        connections = {}
        for connector in connectors:
            start_id = connector['startItem']['id']
            end_id = connector['endItem']['id']
            
            # Get label from captions array
            label = ''
            captions = connector.get('captions', [])
            if captions:
                # Take the first caption content and clean it
                label = self._clean_text(captions[0].get('content', ''))
            
            if start_id not in connections:
                connections[start_id] = []
            connections[start_id].append({
                'to': end_id,
                'label': label
            })
        
        # Find the start node (node with no incoming connections)
        all_target_ids = set()
        for conn_list in connections.values():
            for conn in conn_list:
                all_target_ids.add(conn['to'])
        
        # Look for start node among all nodes with content
        all_content_nodes = start_nodes + question_nodes
        start_node = None
        for node in all_content_nodes:
            if node['id'] not in all_target_ids:
                start_node = node
                break
        
        # If no start node found, use the first node based on position
        if not start_node and all_content_nodes:
            # Sort by Y position (topmost node)
            sorted_nodes = sorted(all_content_nodes, key=lambda n: n['position'].get('y', 0))
            start_node = sorted_nodes[0]
        
        # Build decision tree structure
        decision_tree = {
            'start': start_node['id'] if start_node else None,
            'nodes': {},
            'metadata': {
                'board_id': self.board_id,
                'extracted_at': None
            }
        }
        
        # Add all nodes
        all_nodes = start_nodes + question_nodes + conclusion_nodes
        for node in all_nodes:
            node_type = 'question' if any(n['id'] == node['id'] for n in question_nodes) else \
                       'conclusion' if any(n['id'] == node['id'] for n in conclusion_nodes) else \
                       'start'
            
            decision_tree['nodes'][node['id']] = {
                'type': node_type,
                'text': node['text'],
                'options': []
            }
            
            # Add connections as options
            if node['id'] in connections:
                for conn in connections[node['id']]:
                    decision_tree['nodes'][node['id']]['options'].append({
                        'label': conn['label'],
                        'next': conn['to']
                    })
        
        return decision_tree
    
    def save_as_yaml(self, decision_tree: Dict[str, Any], filename: str = 'decision_tree.yaml'):
        """Save the decision tree as YAML."""
        with open(filename, 'w') as f:
            yaml.dump(decision_tree, f, default_flow_style=False, allow_unicode=True)
    
    def generate_mermaid(self, decision_tree: Dict[str, Any]) -> str:
        """Generate Mermaid flowchart from decision tree."""
        mermaid_lines = ['flowchart TD']
        
        # Create a mapping from numeric IDs to valid Mermaid IDs
        id_mapping = {}
        for i, node_id in enumerate(decision_tree['nodes'].keys()):
            id_mapping[node_id] = f'node{i+1}'
        
        # Add node definitions
        for node_id, node_data in decision_tree['nodes'].items():
            mermaid_id = id_mapping[node_id]
            
            # Define node shape based on type
            if node_data['type'] == 'start':
                shape_start, shape_end = '([', '])'
            elif node_data['type'] == 'question':
                shape_start, shape_end = '{', '}'
            else:  # conclusion
                shape_start, shape_end = '[', ']'
            
            # Clean text for Mermaid (escape quotes and newlines)
            clean_text = node_data['text'].replace('"', "'").replace('\n', ' ').strip()
            if len(clean_text) > 50:  # Truncate long text
                clean_text = clean_text[:47] + "..."
            
            mermaid_lines.append(f'    {mermaid_id}{shape_start}"{clean_text}"{shape_end}')
        
        # Add blank line for readability
        mermaid_lines.append('')
        
        # Add connections
        for node_id, node_data in decision_tree['nodes'].items():
            mermaid_from = id_mapping[node_id]
            for option in node_data['options']:
                mermaid_to = id_mapping.get(option['next'])
                if mermaid_to:  # Only add connection if target node exists
                    label = option['label'].replace('"', "'").strip()
                    if label:
                        mermaid_lines.append(f'    {mermaid_from} -->|"{label}"| {mermaid_to}')
                    else:
                        mermaid_lines.append(f'    {mermaid_from} --> {mermaid_to}')
        
        return '\n'.join(mermaid_lines)
    
    def save_mermaid(self, mermaid_content: str, filename: str = 'decision_tree.mmd'):
        """Save Mermaid diagram to file."""
        with open(filename, 'w') as f:
            f.write(mermaid_content)

def main():
    # Load configuration
    with open('board-details.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    extractor = MiroDecisionTreeExtractor(
        api_key=config['api_key'],
        board_id=config['board_id']
    )
    
    try:
        print("Fetching board data...")
        decision_tree = extractor.parse_decision_tree()
        
        print("Saving as YAML...")
        extractor.save_as_yaml(decision_tree)
        
        print("Generating Mermaid diagram...")
        mermaid_content = extractor.generate_mermaid(decision_tree)
        extractor.save_mermaid(mermaid_content)
        
        print("Done! Files created:")
        print("- decision_tree.yaml")
        print("- decision_tree.mmd")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Miro API: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()