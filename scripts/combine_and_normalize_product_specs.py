import json
import re
import os
from glob import glob

# === CONFIG ===
# Get the project root directory (parent of scripts folder)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

input_dir = os.path.join(project_root, "output")  # directory where scraped JSON files are stored
output_dir = os.path.join(project_root, "combined_output")  # directory where combined files will be saved
product_type = "watches"  # can be phones, watches, tv
output_file = os.path.join(output_dir, f"{product_type}_combined.json")

# === Normalization rules ===
normalization_map = {
    "model_number": ["item_model_number", "model_number", "model_no", "modelname"],
    "model_name": ["model_name"],
    "color": ["color", "colour", "dial_color", "strap_color"],
    "os": ["operating_system", "os"],
    "ram": ["ram", "ram_capacity", "ram_memory_installed_size"],
    "storage": ["internal_storage", "storage_memory", "memory_storage_capacity"],
    "battery_capacity": ["battery_capacity", "battery_power_rating"],
    "display_size": ["display_size", "standing_screen_display_size", "screen_size"],
    "resolution": ["resolution", "screen_resolution", "display_resolution"],
    "weight": ["item_weight", "weight"],
    "dimensions": ["product_dimensions", "dimensions"],
    "brand": ["brand", "manufacturer", "product_brand"],
    "warranty": ["warranty", "warranty_period", "warranty_description"],
    "features": ["features", "feature_list", "specifications", "specs"],
    "price": ["price", "cost", "retail_price"],
    "release_date": ["release_date", "launch_date", "availability_date"],
    "connectivity": ["connectivity", "network_technology", "connectivity_options"],
    "camera": ["camera", "camera_features", "camera_specifications"],
    "processor": ["processor", "cpu", "chipset", "processor_brand"],
    "sensors": ["sensors", "sensor_features", "sensor_specifications"],
    "water_resistance": ["water_resistance", "water_proofing", "ip_rating"],
    "warranty_info": ["warranty_info", "warranty_details", "warranty_terms"],
    "accessories": ["accessories", "included_accessories", "box_contents"],
    "charging": ["charging", "charging_type", "charging_speed", "fast_charging"],
    "audio": ["audio", "sound_features", "speaker_specifications"],
    "video": ["video", "video_features", "video_specifications"],
    "gps": ["gps", "navigation", "location_services"],
    "bluetooth": ["bluetooth", "bluetooth_version", "bluetooth_features"],
    "nfc": ["nfc", "near_field_communication", "nfc_features"],
    "sim": ["sim", "sim_card_type", "sim_slots", "sim_configuration"],
    "materials": ["materials", "build_materials", "case_material"],
    "display_type": ["display_type", "screen_type", "display_technology"],
    "charging_port": ["charging_port", "port_type", "connector_type"],
    "audio_jack": ["audio_jack", "headphone_jack", "audio_port"]
}

# === Helper functions ===

def normalize_key(label):
    return label.lower().strip().replace(" ", "_")

def match_normalized_key(label):
    norm_label = normalize_key(label)
    for std, variants in normalization_map.items():
        if norm_label in variants or norm_label == std:
            return std
    return norm_label

def extract_date(file_path):
    """Extract date from filename like phones_amazon_20250601_050408.json"""
    basename = os.path.basename(file_path)
    # Extract date part (YYYYMMDD) from the filename
    match = re.search(rf"{product_type}_\w+_(\d{{8}})_\d{{6}}\.json", basename)
    return match.group(1) if match else None

# === Main combine logic ===

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

combined = {}

# Get files from output directory with timestamp patterns
amazon_files = glob(os.path.join(input_dir, f"{product_type}_amazon_*.json"))
flipkart_files = glob(os.path.join(input_dir, f"{product_type}_flipkart_*.json"))

print(f"Found {len(amazon_files)} Amazon files and {len(flipkart_files)} Flipkart files")

# Pair and merge files based on date
for amazon_path in amazon_files:
    date = extract_date(amazon_path)
    if not date:
        print(f"Could not extract date from {amazon_path}")
        continue
    
    # Find corresponding Flipkart file with same date
    flipkart_candidates = [f for f in flipkart_files if extract_date(f) == date]
    if not flipkart_candidates:
        print(f"No matching Flipkart file found for date {date}")
        continue
    
    flipkart_path = flipkart_candidates[0]  # Take the first match

    print(f"Processing pair: {os.path.basename(amazon_path)} + {os.path.basename(flipkart_path)}")

    with open(amazon_path, "r", encoding="utf-8") as f1, open(flipkart_path, "r", encoding="utf-8") as f2:
        amazon_data = json.load(f1)
        flipkart_data = json.load(f2)

    # Merge based on normalized keys
    merged = {}
    for item in amazon_data + flipkart_data:
        key = match_normalized_key(item["label"])
        value = item["value"]
        if key not in merged:
            merged[key] = value
        elif isinstance(merged[key], list):
            if value not in merged[key]:
                merged[key].append(value)
        elif merged[key] != value:
            merged[key] = [merged[key], value]

    combined[date] = merged

# Write output
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2, ensure_ascii=False)

print(f"[✓] Combined and normalized {len(combined)} products into {output_file}")
