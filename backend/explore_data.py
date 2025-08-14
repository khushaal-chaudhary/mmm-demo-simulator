import pandas as pd

# Load the dataset
df = pd.read_csv('advertising.csv')

# --- Initial Data Inspection ---
print("--- First 5 Rows ---")
print(df.head())

print("\n--- Data Info ---")
df.info()

print("\n--- Statistical Summary ---")
print(df.describe())