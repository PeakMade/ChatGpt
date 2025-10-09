import re

# Read the file
with open(r'c:\Users\tgaskins\OneDrive - PeakMade Real Estate\Desktop\ChatGPTMock\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count current occurrences
current_count = len(re.findall(r'session\.get\(\s*[\'"]user_id[\'"].*?default_user', content))
print(f"Found {current_count} occurrences to replace")

# Replace all occurrences with a more comprehensive pattern
updated_content = re.sub(
    r'session\.get\(\s*[\'"]user_id[\'"],?\s*[\'"]default_user[\'"]?\s*\)',
    'get_or_create_user_id()',
    content
)

# Write back
with open(r'c:\Users\tgaskins\OneDrive - PeakMade Real Estate\Desktop\ChatGPTMock\app.py', 'w', encoding='utf-8') as f:
    f.write(updated_content)

print("Replacement complete!")
