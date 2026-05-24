import re
paths = [
    r'c:\Users\mulug\OneDrive\Desktop\pro\flet_learnix\views\teacher\shell.py',
    r'c:\Users\mulug\OneDrive\Desktop\pro\flet_learnix\views\parent\shell.py',
    r'c:\Users\mulug\OneDrive\Desktop\pro\flet_learnix\views\setup\_base.py',
    r'c:\Users\mulug\OneDrive\Desktop\pro\flet_learnix\main.py'
]

for p in paths:
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
    new_c = re.sub(r'ft\.View\(\s*("\/[^"]+"|page\.route|route)\s*,\s*\[', r'ft.View(route=\1, controls=[', content)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(new_c)
