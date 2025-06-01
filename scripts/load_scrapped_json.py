import json
from pathlib import Path

def load_scraped_jsons(output_dir="output/"):
    combined = {}
    for json_file in Path(output_dir).glob("*.json"):
        product_key = json_file.stem  # e.g. phones_amazon_20240601
        with open(json_file, "r", encoding="utf-8") as f:
            combined[product_key] = json.load(f)
    return combined

if __name__ == "__main__":
    jsons = load_scraped_jsons()
    for k, v in jsons.items():
        print(f"{k}: {len(v)} specs")

# write combined JSON to a file
output_file = "output/combined_scraped.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(jsons, f, indent=2, ensure_ascii=False)
    print(f"Combined JSON written to {output_file}")