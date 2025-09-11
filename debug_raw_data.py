#!/usr/bin/env python3

import requests
import yaml
import json

def fetch_all_paginated(url, headers):
    """Fetch all items from paginated API endpoint."""
    all_data = []
    cursor = ""
    
    while True:
        params = {'limit': 50}
        if cursor:
            params['cursor'] = cursor
        
        response = requests.get(url, headers=headers, params=params)
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

def dump_raw_data():
    # Load configuration
    with open('board-details.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Accept': 'application/json'
    }
    
    board_id = config['board_id']
    
    print("Fetching all board items...")
    items_url = f'https://api.miro.com/v2/boards/{board_id}/items'
    items_data = fetch_all_paginated(items_url, headers)
    
    print("Fetching all connectors...")
    connectors_url = f'https://api.miro.com/v2/boards/{board_id}/connectors'
    connectors_data = fetch_all_paginated(connectors_url, headers)
    
    # Save raw data
    raw_data = {
        'items': items_data,
        'connectors': connectors_data,
        'board_id': board_id
    }
    
    with open('raw_miro_data.json', 'w') as f:
        json.dump(raw_data, f, indent=2)
    
    print(f"Raw data saved to raw_miro_data.json")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total items: {len(items_data)}")
    print(f"Total connectors: {len(connectors_data)}")
    
    print("\nItem types:")
    item_types = {}
    for item in items_data:
        item_type = item.get('type', 'unknown')
        item_types[item_type] = item_types.get(item_type, 0) + 1
    
    for item_type, count in item_types.items():
        print(f"  {item_type}: {count}")
    
    print("\nConnector summary:")
    for i, connector in enumerate(connectors_data[:5]):  # Show first 5
        start_id = connector.get('startItem', {}).get('id', 'unknown')
        end_id = connector.get('endItem', {}).get('id', 'unknown')
        label = connector.get('data', {}).get('content', 'no label')
        print(f"  {i+1}: {start_id} -> {end_id} ('{label}')")
    
    if len(connectors_data) > 5:
        print(f"  ... and {len(connectors_data) - 5} more connectors")
        
    # Check for missing items referenced in connectors
    item_ids = {item['id'] for item in items_data}
    missing_items = set()
    for connector in connectors_data:
        start_id = connector.get('startItem', {}).get('id')
        end_id = connector.get('endItem', {}).get('id')
        if start_id and start_id not in item_ids:
            missing_items.add(start_id)
        if end_id and end_id not in item_ids:
            missing_items.add(end_id)
    
    if missing_items:
        print(f"\nWARNING: {len(missing_items)} items referenced in connectors but not found:")
        for item_id in list(missing_items)[:5]:
            print(f"  {item_id}")
        if len(missing_items) > 5:
            print(f"  ... and {len(missing_items) - 5} more")

if __name__ == '__main__':
    dump_raw_data()