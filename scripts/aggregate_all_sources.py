#!/usr/bin/env python3
"""
Aggregate data from multiple sources: scraped e-commerce data + internal CSV data
This feeds into the LLM normalization layer with enriched data.
"""

import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

# === CONFIG ===
# Get the project root directory (parent of scripts folder)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

product_type = "watch"  # can be phones, watches, tv
combined_input_dir = os.path.join(project_root, "combined_output")
csv_data_dir = os.path.join(project_root, "data")
aggregated_output_dir = os.path.join(project_root, "aggregated_output")
output_file = os.path.join(aggregated_output_dir, f"{product_type}_aggregated.json")

# === CSV DATA LOADER ===
def load_internal_csv_data(product_type: str):
    """Load internal CSV data for the specified product type"""
    csv_mapping = {
        "phones": "samsung_galaxy_s24_detailed.csv",
        "watch": "samsung_watch6_classic_detailed.csv", 
        "tv": "samsung_frame_tv_detailed.csv"
    }
    
    csv_file = csv_mapping.get(product_type)
    if not csv_file:
        print(f"[!] No CSV mapping found for product type: {product_type}")
        return {}
    
    csv_path = os.path.join(csv_data_dir, csv_file)
    if not os.path.exists(csv_path):
        print(f"[!] CSV file not found: {csv_path}")
        return {}
    
    print(f"[✓] Loading internal CSV data from: {csv_file}")
    
    df = pd.read_csv(csv_path)
    internal_data = {}
    
    for _, row in df.iterrows():
        attribute = str(row["Attribute"]).lower().replace(" ", "_")
        variant = str(row["Variant"])
        value = str(row["Value"])
        
        # Skip empty or NaN values
        if pd.isna(value) or value == "nan":
            continue
            
        # Group by attribute, handling multiple variants
        if attribute not in internal_data:
            internal_data[attribute] = {}
        
        if variant == "All" or variant == "nan":
            internal_data[attribute] = value
        else:
            if not isinstance(internal_data[attribute], dict):
                internal_data[attribute] = {}
            internal_data[attribute][variant] = value
    
    # Flatten single-variant attributes
    flattened = {}
    for attr, value in internal_data.items():
        if isinstance(value, dict) and len(value) == 1:
            flattened[attr] = list(value.values())[0]
        else:
            flattened[attr] = value
    
    return flattened

# === AGGREGATION LOGIC ===
def aggregate_sources(scraped_data: dict, internal_data: dict):
    """Merge scraped e-commerce data with internal CSV data"""
    
    # Start with scraped data as base
    aggregated = scraped_data.copy()
    
    # Add internal data, with preference for internal data when conflicts arise
    for key, value in internal_data.items():
        # Normalize key for comparison
        norm_key = key.lower().replace(" ", "_").replace("-", "_")
        
        # Check if we already have this data from scraping
        existing_keys = [k for k in aggregated.keys() if k.lower().replace(" ", "_").replace("-", "_") == norm_key]
        
        if existing_keys:
            # We have this attribute from scraping, let's merge intelligently
            existing_key = existing_keys[0]
            existing_value = aggregated[existing_key]
            
            # If internal data is more detailed, prefer it
            if isinstance(value, dict) or (isinstance(value, str) and len(value) > len(str(existing_value))):
                aggregated[f"{norm_key}_internal"] = value
            else:
                aggregated[f"{norm_key}_verified"] = value
        else:
            # New attribute from internal data
            aggregated[f"{norm_key}_internal"] = value
    
    return aggregated

# === MAIN WORKFLOW ===
def main():
    # Create output directory
    os.makedirs(aggregated_output_dir, exist_ok=True)
    
    # Load combined scraped data
    combined_file = os.path.join(combined_input_dir, f"{product_type}_combined.json")
    if not os.path.exists(combined_file):
        print(f"[!] Combined scraped data not found: {combined_file}")
        return
    
    with open(combined_file, "r", encoding="utf-8") as f:
        scraped_data = json.load(f)
    
    print(f"[✓] Loaded scraped data with {len(scraped_data)} date entries")
    
    # Load internal CSV data
    internal_data = load_internal_csv_data(product_type)
    print(f"[✓] Loaded internal data with {len(internal_data)} attributes")
    
    # Aggregate all sources
    final_aggregated = {}
    
    for date, product_data in scraped_data.items():
        print(f"→ Aggregating data for date: {date}")
        
        # Merge scraped data with internal data
        aggregated_product = aggregate_sources(product_data, internal_data)
        
        # Add metadata
        aggregated_product["_metadata"] = {
            "scraped_fields": len(product_data),
            "internal_fields": len(internal_data),
            "total_fields": len(aggregated_product) - 1,  # -1 for metadata itself
            "aggregation_date": datetime.now().isoformat(),
            "sources": ["amazon", "flipkart", "internal_csv"]
        }
        
        final_aggregated[date] = aggregated_product
    
    # Save aggregated data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_aggregated, f, indent=2, ensure_ascii=False)
    
    print(f"\n[✓] Aggregated data saved to: {output_file}")
    
    # Print summary
    for date, data in final_aggregated.items():
        metadata = data.get("_metadata", {})
        print(f"Date {date}: {metadata.get('scraped_fields', 0)} scraped + {metadata.get('internal_fields', 0)} internal = {metadata.get('total_fields', 0)} total fields")

if __name__ == "__main__":
    main()
