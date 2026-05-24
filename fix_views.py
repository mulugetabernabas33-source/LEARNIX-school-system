import os
import re

def fix_view_args(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # We want to replace ft.View( "route" , controls
    # First, inline replacements: ft.View("/...", controls)
    # Regex: ft.View( (f?["'].*?["']|page\.route) , (\[.*?\]|controls) )
    # Because some might be multiline, it's safer to use a more robust regex.

    # Pattern for inline: ft.View("/path", controls) -> ft.View(route="/path", controls=controls)
    pattern1 = re.compile(r'ft\.View\(\s*(f?["\'][^"\']+["\']|page\.route)\s*,\s*(controls|\[[^\]]+\]|\s*\[)\s*', re.DOTALL)
    
    def replacer(match):
        route_arg = match.group(1)
        controls_arg = match.group(2)
        # Note: if controls_arg is just '[', we might be capturing the start of a multiline list.
        # So we just prefix route= and controls=
        return f'ft.View(route={route_arg}, controls={controls_arg}'

    new_content = pattern1.sub(replacer, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")

for root, dirs, files in os.walk(r'c:\Users\mulug\OneDrive\Desktop\pro\flet_learnix'):
    for file in files:
        if file.endswith('.py'):
            fix_view_args(os.path.join(root, file))

# Also check root main.py just in case
# fix_view_args(r'c:\Users\mulug\OneDrive\Desktop\pro\main.py')
