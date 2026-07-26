import re
import html
import os

def parse_tree(filepath):
    """Parses the output of 'tree /f /a' into a nested dictionary structure."""
    root = {"name": "Root", "type": "folder", "children": []}
    stack = [root]

    # --- ENCODING FIX ---
    # Windows CMD/PowerShell can output in UTF-8, UTF-16, or CP1252.
    # We try them in order until one works.
    lines = []
    for enc in ['utf-8', 'utf-16', 'cp1252']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                lines = f.readlines()
            break # If successful, exit the loop
        except UnicodeDecodeError:
            continue
            
    # Final fallback: force UTF-8 but replace any unreadable characters with '?'
    if not lines:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    # ---------------------

    for line in lines:
        line = line.rstrip('\n\r')
        if not line.strip():
            continue

        # Skip standard Windows tree headers
        if "Folder PATH listing" in line or "Volume serial number" in line:
            continue
            
        # Skip the summary line at the bottom
        if "Dir(s)" in line and "bytes free" in line:
            continue

        # Detect root directory (e.g., "C:." or "\\server\share")
        if re.match(r'^[A-Za-z]:|^\\\\', line):
            root["name"] = line.strip()
            continue

        # 1. Match the indentation
        indent_match = re.match(r'^((?:[│|]   |    )*)', line)
        if not indent_match:
            continue
            
        indent = indent_match.group(1)
        indent_len = len(indent)
        rest = line[indent_len:]
        
        # 2. Match the branch connector (+---, \---, ├───, └───)
        branch_match = re.match(r'^(?:[+\\├└][-─]+)\s*(.*)', rest)
        if branch_match:
            name = branch_match.group(1).strip()
            is_folder = True
            depth = (indent_len // 4) + 1
        else:
            name = rest.strip()
            is_folder = False
            depth = indent_len // 4
            
        if not name:
            continue

        # Safety clamp to prevent IndexError
        depth = min(depth, len(stack))
        if depth == 0:
            depth = 1 

        node = {
            "name": name,
            "type": "folder" if is_folder else "file",
            "children": [] if is_folder else None
        }

        parent = stack[depth - 1]
        parent["children"].append(node)

        if is_folder:
            if depth < len(stack):
                stack[depth] = node
            else:
                stack.append(node)
            stack = stack[:depth + 1]

    return root

def generate_html_tree(node, is_root=False):
    """Recursively generates HTML <li> and <ul> elements."""
    escaped_name = html.escape(node["name"])
    
    if is_root:
        html_str = f'<li class="folder root"><span class="toggle" onclick="toggleNode(this)">▼</span> <span class="icon">📁</span> <span class="name">{escaped_name}</span>'
    elif node["type"] == "folder":
        html_str = f'<li class="folder"><span class="toggle" onclick="toggleNode(this)">▼</span> <span class="icon">📁</span> <span class="name">{escaped_name}</span>'
    else:
        return f'<li class="file"><span class="icon">📄</span> <span class="name">{escaped_name}</span></li>\n'

    if node["children"]:
        html_str += '\n<ul class="nested">\n'
        for child in node["children"]:
            html_str += generate_html_tree(child)
        html_str += '</ul>\n'
    
    html_str += '</li>\n'
    return html_str

def create_html_file(tree_data, output_filepath):
    """Wraps the generated tree HTML in a complete document with CSS and JS."""
    tree_html = generate_html_tree(tree_data, is_root=True)
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Directory Structure</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; padding: 20px; max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .controls {{ margin-bottom: 20px; }}
        button {{ background-color: #3498db; color: white; border: none; padding: 8px 16px; margin-right: 10px; border-radius: 4px; cursor: pointer; font-size: 14px; }}
        button:hover {{ background-color: #2980b9; }}
        ul.tree {{ list-style-type: none; padding-left: 0; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        ul.tree ul {{ list-style-type: none; padding-left: 25px; border-left: 1px dashed #bdc3c7; margin-left: 10px; }}
        li {{ margin: 5px 0; line-height: 1.6; }}
        .toggle {{ cursor: pointer; display: inline-block; width: 15px; text-align: center; color: #7f8c8d; font-size: 12px; user-select: none; }}
        .icon {{ margin-right: 5px; }}
        .name {{ font-family: 'Consolas', 'Courier New', monospace; }}
        .folder > .name {{ font-weight: 600; color: #2c3e50; }}
        .file > .name {{ color: #555; }}
        .root > .name {{ font-size: 1.2em; color: #2980b9; }}
    </style>
</head>
<body>
    <h1>📂 Directory Structure</h1>
    <div class="controls">
        <button onclick="expandAll()">Expand All</button>
        <button onclick="collapseAll()">Collapse All</button>
    </div>
    <ul class="tree">
        {tree_html}
    </ul>
    <script>
        function toggleNode(el) {{
            var li = el.parentElement;
            var ul = li.querySelector('ul.nested');
            if (ul) {{
                if (ul.style.display === 'none') {{ ul.style.display = 'block'; el.textContent = '▼'; }} 
                else {{ ul.style.display = 'none'; el.textContent = '▶'; }}
            }}
        }}
        function expandAll() {{
            document.querySelectorAll('ul.nested').forEach(ul => ul.style.display = 'block');
            document.querySelectorAll('.toggle').forEach(t => t.textContent = '▼');
        }}
        function collapseAll() {{
            document.querySelectorAll('ul.nested').forEach(ul => ul.style.display = 'none');
            document.querySelectorAll('.toggle').forEach(t => t.textContent = '▶');
        }}
    </script>
</body>
</html>
"""
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(html_template)

if __name__ == "__main__":
    input_file = "structure.txt"
    output_file = "structure_html.html"

    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' not found in the current directory.")
        print("Please run: tree /f /a > structure.txt")
    else:
        print(f"Parsing {input_file}...")
        parsed_tree = parse_tree(input_file)
        
        print(f"Generating {output_file}...")
        create_html_file(parsed_tree, output_file)
        
        print("Success! Open structure_html.html in your browser.")