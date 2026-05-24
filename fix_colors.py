import os
import re

count = 0
for root, _, files in os.walk(r'c:\Users\mulug\OneDrive\Desktop\pro\flet_learnix'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace ft.colors.XXX with ft.Colors.XXX
            new_content, n = re.subn(r'ft\.colors\.', r'ft.Colors.', content)
            
            if n > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed {n} colors in {filepath}")
                count += n
print(f"Total colors fixed: {count}")
