import pandas as pd
import numpy as np

def clean_and_merge_data():
    print("--- [Data Cleaning] Starting Pipeline ---")
    
    # 1. Load the raw datasets
    print("Loading fear_greed_index.csv and historical_data.csv...")
    fg_df = pd.read_csv("data/fear_greed_index.csv")
    hist_df = pd.read_csv("data/historical_data.csv")
    
    # 2. Parse timestamps in the Fear & Greed dataset
    # The date is already in standard YYYY-MM-DD format
    fg_df['date_only'] = pd.to_datetime(fg_df['date']).dt.date
    
    # 3. Parse timestamps in the Historical Trader dataset
    # IMPORTANT: The numeric 'Timestamp' column suffered from float scientific notation rounding.
    # We parse the high-resolution 'Timestamp IST' string column (format: DD-MM-YYYY HH:MM)
    print("Parsing high-precision timestamps (Timestamp IST)...")
    hist_df['parsed_ist'] = pd.to_datetime(hist_df['Timestamp IST'], format='%d-%m-%Y %H:%M')
    hist_df['date_only'] = hist_df['parsed_ist'].dt.date
    
    # 4. Merge the datasets on daily date
    print("Merging datasets on daily dates...")
    merged_df = pd.merge(hist_df, fg_df, on='date_only', how='inner')
    
    # Sort chronologically to maintain timeseries order
    merged_df = merged_df.sort_values('parsed_ist').reset_index(drop=True)
    
    # 5. Save the cleaned dataset for analysis and visualization
    output_path = "data/cleaned_data.csv"
    merged_df.to_csv(output_path, index=False)
    print(f"Data cleaning complete! Saved {len(merged_df):,} rows to '{output_path}'.")

if __name__ == "__main__":
    clean_and_merge_data()
