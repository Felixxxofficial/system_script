import pandas as pd

# Read the CSV file
file_path = r"C:\Users\felix\Downloads\Reels-Grid.csv"
df = pd.read_csv(file_path)

# Calculate rows per part (split into 2 parts, adjust as needed)
total_rows = len(df)
rows_per_part = total_rows // 2 + 1  # Roughly half, plus 1 to handle odd numbers

# Split and save parts
for i in range(0, total_rows, rows_per_part):
    part_df = df[i:i + rows_per_part]
    part_df.to_csv(f"C:\\Users\\felix\\Downloads\\Reels-Grid-part-{i//rows_per_part + 1}.csv", index=False)