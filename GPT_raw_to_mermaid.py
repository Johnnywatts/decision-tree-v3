#!/usr/bin/env python3
"""
Script: GPT_raw_to_mermaid.py
Converts Miro board JSON data to a Mermaid diagram file.
"""
import json
import re
import argparse
from html import unescape

DEFAULT_INPUT_FILE = "raw_miro_data.json"
DEFAULT_OUTPUT_FILE = "GPT_raw_to_mermaid.mmd"
DEFAULT_MD_FILE = "GPT_raw_to_mermaid.md"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _html_to_text(html: str) -> str:
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

NODE_TYPES_INCLUDE = {"shape", "sticky_note", "text", "doc_format"}

def extract_nodes_and_edges(data):
    """Extract nodes and edges from Miro export with keys: items, connectors.

    Returns:
        nodes: dict[id] = label
        edges: list of (src_id, dst_id, label)
    """
    nodes = {}
    edges = []
    for item in data.get("items", []):
        item_id = item.get("id")
        if not item_id:
            continue
        t = item.get("type")
        if t not in NODE_TYPES_INCLUDE:
            # skip unsupported diagram container etc.
            continue
        label = ""
        data_block = item.get("data", {}) or {}
        if isinstance(data_block, dict):
            # common keys: content, html
            raw_content = data_block.get("content") or data_block.get("html") or ""
            label = _html_to_text(raw_content)
        if not label:
            label = t
        # Shrink overly long labels for mermaid readability
        if len(label) > 80:
            label = label[:77] + "..."
        nodes[item_id] = label

    for conn in data.get("connectors", []):
        start = conn.get("startItem", {})
        end = conn.get("endItem", {})
        src = start.get("id")
        dst = end.get("id")
        if not src or not dst:
            continue
        captions = conn.get("captions") or []
        edge_label = ""
        if captions:
            # take concatenated caption content (strip HTML)
            caption_texts = []
            for c in captions:
                ct = _html_to_text(c.get("content", ""))
                if ct:
                    caption_texts.append(ct)
            edge_label = " / ".join(caption_texts)
        edges.append((src, dst, edge_label))
    return nodes, edges

def sanitize_id(raw_id: str) -> str:
    # Mermaid node id must start with letter; map numeric ids.
    if re.match(r"^[A-Za-z_]", raw_id):
        base = raw_id
    else:
        base = "N" + raw_id
    # remove problematic chars
    base = re.sub(r"[^0-9A-Za-z_]+", "_", base)
    return base

def write_mermaid(nodes, edges, out_path):
    id_map = {orig: sanitize_id(orig) for orig in nodes.keys()}
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("flowchart TD\n")
        for orig_id, label in nodes.items():
            # escape angle brackets that may break some renderers
            safe_label = label.replace('<', '&lt;').replace('>', '&gt;')
            f.write(f"    {id_map[orig_id]}[{safe_label}]\n")
        for src, dst, elabel in edges:
            if src not in id_map or dst not in id_map:
                continue
            if elabel:
                # Mermaid syntax for labeled edge: A -->|label| B
                f.write(f"    {id_map[src]} -->|{elabel}| {id_map[dst]}\n")
            else:
                f.write(f"    {id_map[src]} --> {id_map[dst]}\n")
    return id_map

def write_markdown(md_path, mermaid_path, nodes, edges, id_map):
    with open(mermaid_path, 'r', encoding='utf-8') as mf:
        mermaid_code = mf.read().strip()
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Miro Board Diagram\n\n")
        f.write(f"Generated from `{mermaid_path}`.\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_code)
        f.write("\n```\n\n")
        f.write("## Node Legend\n\n")
        for oid, label in nodes.items():
            f.write(f"- {id_map[oid]}: {label}\n")

def parse_args():
    p = argparse.ArgumentParser(description="Convert Miro raw JSON to Mermaid flowchart")
    p.add_argument("-i", "--input", default=DEFAULT_INPUT_FILE, help="Input Miro JSON file")
    p.add_argument("-o", "--output", default=DEFAULT_OUTPUT_FILE, help="Output Mermaid .mmd file")
    p.add_argument("--md", default=DEFAULT_MD_FILE, help="Optional output Markdown file with embedded diagram")
    return p.parse_args()

def main():
    args = parse_args()
    data = load_json(args.input)
    nodes, edges = extract_nodes_and_edges(data)
    id_map = write_mermaid(nodes, edges, args.output)
    if args.md:
        write_markdown(args.md, args.output, nodes, edges, id_map)
        print(f"Extracted {len(nodes)} nodes, {len(edges)} edges -> {args.output} & {args.md}")
    else:
        print(f"Extracted {len(nodes)} nodes, {len(edges)} edges -> {args.output}")

if __name__ == "__main__":
    main()
