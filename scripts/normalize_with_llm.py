#!/usr/bin/env python3
"""
Enhanced LLM normalization script that processes aggregated data from multiple sources
(e-commerce scraping + internal CSV) to create comprehensive normalized product records.
"""

import os
import json
import openai
from time import sleep
from dotenv import load_dotenv

# === CONFIG ===
# Get the project root directory (parent of scripts folder)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
output_dir = os.path.join(project_root, "normalized_output")

# Load .env file from project root
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

product_type = "watch"  # can be phones, watch, tv
input_file = os.path.join(project_root, "aggregated_output", f"{product_type}_aggregated.json")
output_file = os.path.join(output_dir, f"{product_type}_llm_normalized.json")

# Get the key from .env file
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("[!] Warning: OPENAI_API_KEY environment variable is not set")
    print(f"[!] Checked .env file at: {env_path}")
    print("[!] The script will run but LLM normalization will be skipped")
    api_key = None
else:
    print(f"[✓] OpenAI API key loaded successfully (ends with: ...{api_key[-6:]})")

# === PROMPTS ===
SYSTEM_PROMPT = """
You are a Master Data Management (MDM) assistant specializing in Samsung product normalization. You receive aggregated product data from multiple sources: e-commerce websites (Amazon, Flipkart) AND internal company databases (CSV).

## CRITICAL REQUIREMENT: PRESERVE ALL MEANINGFUL DATA
- DO NOT discard fields unless they are truly redundant or meaningless
- PRESERVE ALL technical specifications, measurements, and detailed attributes
- MAINTAIN granular information like processor speeds, camera details, network bands
- KEEP ALL warranty, connectivity, and feature information

## NORMALIZATION RULES:

### 1. Key Standardization
- Normalize ALL keys to lowercase_with_underscores format
- Handle special suffixes: "_internal" (from CSV), "_verified" (cross-validated)
- Use standardized key mappings when applicable:
  * model_number, model_name, brand, color, os, ram, storage, battery_capacity
  * display_size, resolution, weight, dimensions, warranty, features, price
  * connectivity, camera, processor, sensors, water_resistance, charging
  * audio, video, gps, bluetooth, nfc, sim, materials, display_type

### 2. Multi-Source Value Handling
- When you see "_internal" suffixed keys, these are from authoritative CSV sources - PREFER these
- When you see "_verified" keys, these are cross-validated - treat as highly reliable
- For conflicting values, create arrays: ["e-commerce_value", "internal_value"]
- Preserve version numbers, model variants, and technical specifications exactly

### 3. Value Consolidation Strategy
- For measurements: Preserve full details "15.75 cm (6.2 inch)" over simplified "6.2 inch"
- For technical specs: Keep detailed values over marketing terms
- For lists: Merge and deduplicate while preserving specificity
- For ranges: Keep as ranges (e.g., "1.8 - 3.2 GHz") don't pick single values

### 4. Boolean and Feature Handling
- Convert "Yes"/"No" patterns to boolean where appropriate
- Move boolean "Yes" attributes to a consolidated "features" array
- Preserve detailed feature descriptions, don't simplify to just true/false
- Keep capability details: "Fast Charging 25W" not just "fast_charging: true"

### 5. Data Enrichment Rules
- Combine related attributes intelligently (e.g., merge camera details)
- Create logical groupings: display{}, camera{}, battery{}, connectivity{}
- Preserve both summary and detailed versions when available
- Maintain backward compatibility with original field names

### 6. Technical Preservation
- NEVER lose processor details, speeds, architecture info
- KEEP ALL camera specifications, megapixels, aperture details
- PRESERVE network bands, frequency details, connectivity versions
- MAINTAIN exact measurements, weights, dimensions with units
- KEEP warranty terms, coverage details, duration specifics

### 7. Product Category Specific Rules
**Phones**: Preserve ALL camera, battery, processor, display, network, storage details
**Watches**: Preserve ALL sensors, health features, battery life, water resistance, compatibility details  
**TVs**: Preserve ALL display tech, resolution, smart features, audio, connectivity, mounting details

no duplicates like under verified and internal unless value is diff.
Return comprehensive normalized JSON that preserves the richness of the source data.
"""

USER_TEMPLATE = """Normalize this {product_type} product data aggregated from multiple sources (e-commerce + internal CSV):

```json
{data}
```

Apply MDM normalization rules while preserving ALL meaningful technical specifications and details."""

# === LLM CALL ===
def call_gpt4o_cleaner(product_json: dict, product_type: str):
    if not api_key:
        print("[!] Skipping LLM normalization - no API key")
        return product_json  # Return original data if no API key
    
    user_prompt = USER_TEMPLATE.format(data=json.dumps(product_json, indent=2), product_type=product_type)

    try:
        # Updated OpenAI API call for newer versions
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.3,
            max_tokens=4096  # Increased for comprehensive output
        )
        reply = response.choices[0].message.content

        # Try extracting JSON from code block if present
        if "```json" in reply:
            reply = reply.split("```json")[1].split("```")[0].strip()

        return json.loads(reply)
    except Exception as e:
        print(f"[!] Error normalizing product: {e}")
        return None

# === MAIN WORKFLOW ===
def main():
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(input_file):
        print(f"[!] Input file not found: {input_file}")
        print(f"[!] Please run aggregate_all_sources.py first")
        exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        aggregated_data = json.load(f)

    final_result = {}

    for date, product in aggregated_data.items():
        print(f"→ Normalizing {product_type} product from date: {date}")
        
        # Extract metadata if present
        metadata = product.pop("_metadata", {})
        
        # Show source data richness
        source_fields = metadata.get("total_fields", len(product))
        print(f"  Source data: {source_fields} fields")
        
        # Normalize with LLM
        cleaned = call_gpt4o_cleaner(product, product_type)
        if cleaned:
            # Add normalization metadata
            cleaned["_normalization_metadata"] = {
                "original_fields": source_fields,
                "normalized_fields": len(cleaned) - 1,  # -1 for metadata itself
                "field_retention_ratio": (len(cleaned) - 1) / source_fields if source_fields > 0 else 0,
                "source_metadata": metadata
            }
            final_result[date] = cleaned
            print(f"  Normalized: {len(cleaned) - 1} fields (retention: {cleaned['_normalization_metadata']['field_retention_ratio']:.2%})")
        else:
            print(f"  [!] Failed to normalize data for {date}")
        
        sleep(1.1)  # Respect rate limits

    # Save normalized data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_result, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Normalized data saved to: {output_file}")
    
    # Print summary
    for date, data in final_result.items():
        metadata = data.get("_normalization_metadata", {})
        print(f"Date {date}: {metadata.get('original_fields', 0)} → {metadata.get('normalized_fields', 0)} fields ({metadata.get('field_retention_ratio', 0):.2%} retention)")

if __name__ == "__main__":
    main()
