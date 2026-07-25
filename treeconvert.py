import re
import html

def parse_tree_to_html(input_file, output_file):
    # Base HTML template with styling for the tree structure
    html_start = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Folder Structure Navigation</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; background-color: #f9f9f9; color: #333; }
        .tree-container { background: #fff; border: 1px solid #e1e4e8; border-radius: 6px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        details { margin-left: 24px; display: block; }
        summary { cursor: pointer; padding: 4px 8px; font-weight: 600; outline: none; border-radius: 4px; color: #0366d6; list-style-type: none; position: relative; }
        summary::-webkit-details-marker { display: none; }
        summary::before { content: "📁 "; display: inline-block; width: 1.5em; }
        details[open] > summary::before { content: "📂 "; }
        summary:hover { background-color: #f0f3f6; }
        ul { list-style: none; padding-left: 24px; margin: 4px 0; }
        li { padding: 4px 8px; color: #24292e; border-radius: 4px; display: flex; align-items: center; }
        li::before { content: "📄 "; display: inline-block; width: 1.5em; }
        li:hover { background-color: #f6f8fa; }
    </style>
</head>
<body>
<div class="tree-container">
"""

    html_end = """
</div>
</body>
</html>"""

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    html_body = []
    current_indent_level = 0
    stack = []  # Tracks open HTML tags to ensure correct closing pairs
    in_ul = False

    for line in lines:
        if not line.strip():
            continue
        
        # Calculate level based on character depth pattern (e.g., "|   ", "    ")
        # Matches the structure of standard "tree /a /f" output
        match = re.match(r"^([| \t\-+\\]*)", line)
        prefix = match.group(1) if match else ""
        
        # Compute tree indentation level
        level = (len(prefix) // 4) + 1 if prefix else 0
        
        # Clean the text to isolate the file/folder name
        name = line.replace(prefix, "").strip()
        if not name:
            continue
        
        # Escape HTML characters to prevent breaking the layout
        name = html.escape(name)

        # Close older tags if we moved back up the folder tree
        while len(stack) > level:
            last_tag = stack.pop()
            if last_tag == 'ul':
                in_ul = False
            html_body.append(f"{'  ' * len(stack)}</{last_tag}>\n")

        # Guess if item is a file by checking for an extension
        is_file = '.' in name and not name.startswith('.')

        if is_file:
            if not in_ul:
                html_body.append(f"{'  ' * len(stack)}<ul>\n")
                stack.append('ul')
                in_ul = True
            html_body.append(f"{'  ' * len(stack)}  <li>{name}</li>\n")
        else:
            if in_ul:
                html_body.append(f"{'  ' * len(stack)}</ul>\n")
                stack.pop()
                in_ul = False
                
            # Render folder as interactive details panel
            html_body.append(f"{'  ' * len(stack)}<details>\n")
            html_body.append(f"{'  ' * len(stack)}  <summary>{name}</summary>\n")
            stack.append('details')

    # Empty out remaining active tags inside the stack
    while stack:
        last_tag = stack.pop()
        html_body.append(f"{'  ' * len(stack)}</{last_tag}>\n")

    # Construct the final page document
    full_html = html_start + "".join(html_body) + html_end
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"Success! Generated '{output_file}' with fully collapsible elements.")

# Run script matching your system file names
parse_tree_to_html("structure.txt", "structure.html")
