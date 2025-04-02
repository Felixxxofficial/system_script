import sys
from datetime import datetime
import os

# Directory to save the new file (adjust to your preference)
output_dir = "C:/Users/felix/Obsidian/Felix"  # Change to your vault path

# Get today's date
today = datetime.now().strftime("%Y-%m-%d")

# Create a new file with today's date in the name
file_name = f"ScriptTest_{today}.md"
file_path = os.path.join(output_dir, file_name)

# Write a simple message to the file
with open(file_path, 'w') as f:
    f.write(f"Script executed on {today}!")

print(f"SCRIPT OUTPUT: Created {file_path}")