import json
import os
import re
import glob
from fpdf import FPDF
from datetime import datetime

# === CONFIG ===
# Get the project root directory (parent of scripts folder)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

product_type = "tv"   # can be 'phones', 'watch', or 'tv'
input_file = os.path.join(project_root, "normalized_output", f"{product_type}_llm_normalized.json")
output_dir = os.path.join(project_root, "brochures")
images_dir = os.path.join(project_root, "images")
os.makedirs(output_dir, exist_ok=True)

# === IMAGE UTILITIES ===
def find_product_images(product_type, limit=5):
    """Find images for a specific product type"""
    if not os.path.exists(images_dir):
        return []
    
    # Look for images with the new naming pattern: {product_type}_{source}_{date}_{hash}.{ext}
    pattern = os.path.join(images_dir, f"{product_type}_*.*")
    all_images = glob.glob(pattern)
    
    # Filter for common image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    valid_images = [img for img in all_images 
                   if any(img.lower().endswith(ext) for ext in image_extensions)]
    
    # Sort by file modification time (newest first) and limit
    valid_images.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    return valid_images

def add_image_to_pdf(pdf, image_path, max_width=80, max_height=60):
    """Add an image to the PDF with size constraints"""
    try:
        # Get current position
        x = pdf.get_x()
        y = pdf.get_y()
        
        # Add image with size constraints
        pdf.image(image_path, x=x, y=y, w=max_width, h=max_height)
        
        # Move cursor below the image
        pdf.set_y(y + max_height + 5)
        return True
        
    except Exception as e:
        print(f"Warning: Could not add image {image_path}: {e}")
        return False

def add_image_grid_to_pdf(pdf, image_paths, max_width=80, max_height=60, images_per_row=2):
    """Add multiple images in a grid layout to the PDF"""
    margin = 10
    spacing_x = 10
    spacing_y = 15
    
    x_start = margin
    y = pdf.get_y()
    col = 0

    for i, image_path in enumerate(image_paths):
        if col == 0:
            x = x_start
        else:
            x = x_start + col * (max_width + spacing_x)
        
        try:
            # Check if next row fits; if not, add a new page
            if y + max_height + spacing_y > 270:
                pdf.add_page()
                y = pdf.get_y()
            
            pdf.image(image_path, x=x, y=y, w=max_width, h=max_height)
        except Exception as e:
            print(f"Warning: Skipped image {image_path}: {e}")
            continue
        
        col += 1
        if col >= images_per_row:
            col = 0
            y += max_height + spacing_y

# === DATA FORMATTING UTILITIES ===
def clean_text_for_pdf(text):
    """Clean text to avoid encoding issues in PDF"""
    if not isinstance(text, str):
        text = str(text)
    
    # Replace problematic characters with safe alternatives
    text = text.replace('™', '(TM)')
    text = text.replace('®', '(R)')
    text = text.replace('°', ' degrees')
    text = text.replace('–', '-')
    text = text.replace('—', '-')
    text = text.replace('"', '"')
    text = text.replace('"', '"')
    text = text.replace(''', "'")
    text = text.replace(''', "'")
    text = text.replace('…', '...')
    
    # Handle bullet points and special characters more carefully
    text = text.replace('•', '-')
    text = text.replace('‣', '-')
    text = text.replace('▪', '-')
    text = text.replace('▫', '-')
    
    # Only replace truly problematic characters, keep most Unicode
    # Remove control characters and some problematic Unicode ranges
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x84\x86-\x9F]', '', text)
    
    # Replace remaining problematic characters only if they cause issues
    # Keep common Unicode characters like accented letters
    try:
        # Test if the text can be encoded to latin-1 (FPDF limitation)
        text.encode('latin-1')
    except UnicodeEncodeError:
        # Only if encoding fails, replace problematic characters
        text = text.encode('latin-1', errors='replace').decode('latin-1')
    
    return text.strip()

def format_value(value, key=""):
    """Format different types of values for display"""
    if value is None:
        return "Not specified"
      # Handle boolean values
    if isinstance(value, bool):
        return "Yes" if value else "No"
    
    # Handle lists
    if isinstance(value, list):
        if len(value) == 0:
            return "Not specified"
        elif len(value) == 1:
            return clean_text_for_pdf(str(value[0]))
        else:
            # For short lists, join with commas
            if all(len(str(item)) < 30 for item in value) and len(value) <= 5:
                return clean_text_for_pdf(", ".join(str(item) for item in value))
            else:
                # For long lists, use simple dashes instead of bullet points
                formatted_items = []
                for item in value[:8]:  # Limit to 8 items to avoid clutter
                    clean_item = clean_text_for_pdf(str(item))
                    formatted_items.append(f"- {clean_item}")
                if len(value) > 8:
                    formatted_items.append(f"- ... and {len(value) - 8} more")
                return "\n".join(formatted_items)
    
    # Handle dictionaries (nested objects)
    if isinstance(value, dict):
        formatted_items = []
        for k, v in value.items():
            if k.startswith('_'):  # Skip metadata
                continue
            formatted_key = format_key(k)
            formatted_value = format_value(v)
            if formatted_value != "Not specified":
                formatted_items.append(f"{formatted_key}: {formatted_value}")
        return "\n".join(formatted_items) if formatted_items else "Not specified"
    
    # Handle strings and numbers
    value_str = clean_text_for_pdf(str(value))
    
    # Handle long manufacturer names
    if "brand" in key.lower() and len(value_str) > 50:
        # Extract just the brand name from long manufacturer strings
        if "Samsung" in value_str:
            return "Samsung"
    
    return value_str

def format_key(key):
    """Format key names for display"""
    # Handle special cases
    key_mappings = {
        'os': 'Operating System',
        'ram': 'RAM',
        'usb': 'USB',
        'hdmi': 'HDMI',
        'wifi': 'Wi-Fi',
        'nfc': 'NFC',
        'gps': 'GPS',
        'ip_rating': 'IP Rating',
        'display_size': 'Screen Size',
        'battery_capacity': 'Battery',
        'model_number': 'Model Number',
        'model_name': 'Model Name',
        'water_dust_resistance': 'Water/Dust Resistance',
        'wireless_communication_technologies': 'Wireless Technology',
        'connectivity_technologies': 'Connectivity',
        'other_display_features': 'Display Features',
        'other_camera_features': 'Camera Features',
        'special_features': 'Special Features'
    }
    
    if key in key_mappings:
        return key_mappings[key]
    
    # Default formatting
    formatted = key.replace('_', ' ').title()
    return clean_text_for_pdf(formatted)

def should_skip_field(key, value):
    """Determine if a field should be skipped in the brochure"""
    skip_patterns = [
        '_metadata', '_normalization', 'number_of_items', 
        'item_height', 'item_width', 'are_batteries_included',
        'lithium_battery_weight', 'lithium_battery_energy_content',
        'package_dimensions', 'item_model_number', 'batteries'
    ]
    
    # Skip metadata and internal fields
    if any(pattern in key for pattern in skip_patterns):
        return True
    
    # Skip empty or meaningless values
    if value is None or value == "" or value == "Not specified":
        return True
        
    # Skip very long technical strings that aren't user-friendly
    if isinstance(value, str) and len(value) > 200:
        return True
    
    return False

# === ENHANCED PDF CLASS ===
class SamsungBrochurePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.page_count = 0
        
    def header(self):
        # Samsung brand colors
        self.set_fill_color(20, 40, 85)  # Samsung blue
        self.rect(0, 0, 210, 25, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 16)
        self.cell(0, 25, "SAMSUNG", align="C", ln=True)
        
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%B %d, %Y')} | Page {self.page_no()}", align="C")

    def add_title(self, brand, model, color=""):
        self.set_font("Arial", "B", 20)
        self.set_text_color(20, 40, 85)
        title = f"{model}"  # Only show model name, not brand
        if color and color != "Not specified":
            title += f" - {color}"
        self.cell(0, 15, clean_text_for_pdf(title), ln=True, align="C")
        self.ln(10)

    def add_section_header(self, title):
        self.set_fill_color(240, 240, 240)
        self.set_text_color(20, 40, 85)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, clean_text_for_pdf(title), ln=True, fill=True, border='B')
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def add_field(self, label, value, indent=0):
        formatted_value = format_value(value, label)
        
        if formatted_value == "Not specified":
            return
        
        # Handle multi-line values
        if '\n' in formatted_value:
            # Label
            self.set_font("Arial", "B", 11)
            if indent > 0:
                self.cell(indent)
            self.cell(0, 6, clean_text_for_pdf(f"{label}:"), ln=True)
            
            # Multi-line value
            self.set_font("Arial", "", 10)
            lines = formatted_value.split('\n')
            for line in lines:
                if indent > 0:
                    self.cell(indent + 10)
                else:
                    self.cell(10)
                self.cell(0, 5, clean_text_for_pdf(line), ln=True)
            self.ln(2)
        else:            # Single line field
            self.set_font("Arial", "B", 11)
            if indent > 0:
                self.cell(indent)
            self.cell(50, 6, clean_text_for_pdf(f"{label}:"))
            
            self.set_font("Arial", "", 11)
            # Handle long values
            if len(formatted_value) > 60:
                self.ln(6)
                if indent > 0:
                    self.cell(indent + 10)
                else:
                    self.cell(10)
                self.multi_cell(0, 5, clean_text_for_pdf(formatted_value))
            else:
                self.cell(0, 6, clean_text_for_pdf(formatted_value), ln=True)
            self.ln(1)

    def add_feature_grid(self, features):
        if not features:
            return
            
        self.add_section_header("Key Features")
        
        # Create a grid layout for features
        self.set_font("Arial", "", 10)
        col_width = 85
        x_start = self.get_x()
        
        for i, feature in enumerate(features[:12]):  # Limit to 12 features
            if i > 0 and i % 2 == 0:
                self.ln(6)
            
            x_pos = x_start + (i % 2) * col_width
            self.set_xy(x_pos, self.get_y())
            self.cell(5, 5, "*", ln=False)  # Use * instead of + or bullet
            self.cell(col_width - 5, 5, clean_text_for_pdf(str(feature)[:35]), ln=False)
        
        self.ln(10)

    def add_two_column_layout(self, left_data, right_data, left_title="", right_title=""):
        """Add content in two columns"""
        if left_title:
            self.add_section_header(left_title)
        
        # Store current position
        start_y = self.get_y()
        left_x = 10
        right_x = 110
        col_width = 90
        
        # Track max Y position for both columns
        left_y_max = start_y
        right_y_max = start_y
        
        # Left column
        self.set_xy(left_x, start_y)
        for label, value in left_data.items():
            if self.get_y() > 250:  # Near bottom of page
                self.add_page()
                start_y = self.get_y()
                self.set_xy(left_x, start_y)
            
            self.set_font("Arial", "B", 10)
            self.cell(col_width, 5, clean_text_for_pdf(f"{label}:"), ln=True)
            self.set_font("Arial", "", 9)
            self.set_x(left_x)
            formatted_value = format_value(value, label)
            if formatted_value != "Not specified":
                self.multi_cell(col_width, 4, clean_text_for_pdf(formatted_value))
            self.ln(2)
        
        # Record left column final position
        left_y_max = self.get_y()
        
        # Right column
        right_y = start_y
        self.set_xy(right_x, right_y)
        
        if right_title and right_data:
            self.set_font("Arial", "B", 12)
            self.cell(col_width, 8, clean_text_for_pdf(right_title), ln=True, align="C")
            self.set_x(right_x)
            self.ln(3)
        
        for label, value in right_data.items():
            if self.get_y() > 250:  # Near bottom of page
                break
            
            self.set_font("Arial", "B", 10)
            self.set_x(right_x)
            self.cell(col_width, 5, clean_text_for_pdf(f"{label}:"), ln=True)
            self.set_font("Arial", "", 9)
            self.set_x(right_x)
            formatted_value = format_value(value, label)
            if formatted_value != "Not specified":
                self.multi_cell(col_width, 4, clean_text_for_pdf(formatted_value))
            self.ln(2)
        
        # Record right column final position
        right_y_max = self.get_y()
        
        # Set cursor to the bottom of the longest column
        final_y = max(left_y_max, right_y_max)
        self.set_xy(10, final_y)

# === SMART FIELD GROUPING ===
def get_field_groups(product_type):
    """Define logical grouping of fields based on product type"""
    
    base_groups = {
        "Basic Information": ["brand", "model_name", "model_number", "color", "series", "form_factor"],
        "Physical Specifications": ["dimensions", "weight", "materials", "water_dust_resistance"],
        "Warranty & Support": ["warranty", "domestic_warranty", "warranty_info", "covered_in_warranty"]
    }
    
    if product_type == "phones":
        groups = {
            **base_groups,
            "Display": ["display", "display_size", "resolution", "display_type", "refresh_rate", "brightness", "other_display_features"],
            "Performance": ["processor", "processor_type", "ram", "storage", "os", "internal_storage"],
            "Camera": ["rear_camera", "front_camera", "primary_camera", "secondary_camera", "camera", "video_recording", "optical_zoom", "other_camera_features"],
            "Battery & Charging": ["battery_capacity", "battery_life", "charging", "quick_charging", "battery_type"],
            "Connectivity": ["network_type", "5g", "4g", "wifi", "bluetooth", "nfc", "sim_type", "connectivity", "connectivity_technologies", "wireless_communication_technologies"],
            "Audio & Media": ["audio_jack", "speaker_phone", "audio", "music_player", "video_formats"]
        }
    elif product_type == "watch":
        groups = {
            **base_groups,
            "Display": ["display", "display_size", "display_type", "touchscreen", "resolution"],
            "Health & Fitness": ["heart_rate_monitor", "sensors", "step_count", "calorie_count", "fitness"],
            "Smart Features": ["os", "compatible_os", "notifications", "call_function", "voice_control", "special_features"],
            "Connectivity": ["bluetooth", "wifi", "gps", "nfc", "connectivity"],
            "Battery": ["battery_life", "battery_type", "charger_type"],
            "Design": ["dial_shape", "strap_material", "water_resistant", "size"]
        }
    elif product_type == "tv":
        groups = {
            **base_groups,
            "Display": ["display", "display_size", "resolution", "display_type", "refresh_rate", "brightness"],
            "Smart Features": ["os", "smart_features", "supported_apps", "voice_control", "special_features"],
            "Audio": ["audio", "sound_technology", "speakers", "audio_wattage"],
            "Connectivity": ["hdmi_ports", "usb_ports", "wifi", "bluetooth", "ethernet", "connectivity"],
            "Power": ["power_consumption", "voltage", "wattage"],
            "Installation": ["mounting_type", "installation", "remote_control"]
        }
    else:
        groups = base_groups
    
    return groups

def extract_key_specs(product, product_type):
    """Extract key specifications for highlight box"""
    key_specs = {}
    
    if product_type == "phones":
        spec_keys = ["display", "rear_camera", "front_camera", "battery_capacity", "storage", "ram", "os"]
    elif product_type in ["watches", "watch"]:
        spec_keys = ["display_size", "battery_life", "water_resistant", "os", "connectivity"]
    elif product_type == "tv":
        spec_keys = ["display_size", "resolution", "smart_features", "audio"]
    else:
        spec_keys = ["model_name", "dimensions", "weight"]
    
    for key in spec_keys:
        # Look for exact match or partial match
        matching_keys = [k for k in product.keys() if k == key or key in k or k in key]
        for match_key in matching_keys:
            if not should_skip_field(match_key, product[match_key]):
                formatted_key = format_key(match_key)
                key_specs[formatted_key] = product[match_key]
                break  # Take first match
    
    return key_specs

def process_product_data(product, product_type):
    """Process and organize product data for display"""
    # Remove metadata fields
    clean_product = {k: v for k, v in product.items() if not k.startswith('_')}
    
    # Extract key information for title
    brand = format_value(clean_product.get("brand", "Samsung"))
    model = format_value(clean_product.get("model_name", clean_product.get("model", "Product")))
    
    # Extract color - handle both simple and complex color data
    color_data = clean_product.get("color", "")
    if isinstance(color_data, dict):
        # Extract from internal data if available
        if "internal" in color_data:
            internal_colors = color_data["internal"]
            if isinstance(internal_colors, dict):
                # Take first color variant
                color = list(internal_colors.values())[0] if internal_colors else ""
            else:
                color = str(internal_colors)
        else:
            color = ""
    else:
        color = format_value(color_data)
      # Group fields
    field_groups = get_field_groups(product_type)
    organized_data = {}
    used_fields = set()
    
    # Extract features for special handling
    features_raw = clean_product.get("special_features", clean_product.get("features", []))
    features = []
    
    # Handle different feature data structures
    if isinstance(features_raw, list):
        features = features_raw
    elif isinstance(features_raw, dict):
        # Extract features from nested dictionary structure
        for key, value in features_raw.items():
            if isinstance(value, list):
                features.extend(value)
            elif isinstance(value, str):
                features.append(value)
    
    if features_raw:
        used_fields.add("special_features")
        used_fields.add("features")
    
    # Extract key specifications
    key_specs = extract_key_specs(clean_product, product_type)
    for spec_key in key_specs:
        # Mark original field as used
        original_keys = [k for k in clean_product.keys() if format_key(k) == spec_key]
        used_fields.update(original_keys)
    
    # Organize fields into groups
    for group_name, field_keys in field_groups.items():
        group_data = {}
        for key in field_keys:
            # Check for exact match or partial match
            matching_keys = [k for k in clean_product.keys() if k == key or key in k or k in key]
            for match_key in matching_keys[:3]:  # Limit to avoid duplicates
                if match_key not in used_fields and not should_skip_field(match_key, clean_product[match_key]):
                    group_data[format_key(match_key)] = clean_product[match_key]
                    used_fields.add(match_key)
        
        if group_data:
            organized_data[group_name] = group_data
    
    # Add remaining fields to "Additional Information"
    remaining_fields = {k: v for k, v in clean_product.items() 
                      if k not in used_fields and not should_skip_field(k, v)}
    
    if remaining_fields:
        additional_data = {}
        for k, v in remaining_fields.items():
            additional_data[format_key(k)] = v
        if additional_data:
            organized_data["Additional Information"] = additional_data
    
    return brand, model, color, features, key_specs, organized_data

# === MAIN EXECUTION ===
def generate_brochure(product_type="phones"):
    """Generate professional PDF brochure from normalized JSON data"""
    
    if not os.path.exists(input_file):
        print(f"[!] Input file not found: {input_file}")
        print(f"[!] Please run normalize_with_llm.py first")
        return
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Error reading input file: {e}")
        return
    
    print(f"[*] Generating {product_type} brochures...")
    
    for date, product in data.items():
        try:
            # Process product data
            brand, model, color, features, key_specs, organized_data = process_product_data(product, product_type)
            
            # Create PDF
            pdf = SamsungBrochurePDF()
            pdf.add_page()
              # Add title
            pdf.add_title(brand, model, color)
            
            # Add key specifications in two-column layout
            if key_specs:
                half_point = len(key_specs) // 2
                key_specs_items = list(key_specs.items())
                left_specs = dict(key_specs_items[:half_point])
                right_specs = dict(key_specs_items[half_point:])
                pdf.add_two_column_layout(left_specs, right_specs, "Key Specifications")
                pdf.ln(10)
            
            # Add features grid if available
            if features:
                pdf.add_feature_grid(features)
            
            # Add organized sections
            for section_name, section_data in organized_data.items():
                if section_data:  # Only add sections with data
                    pdf.add_section_header(section_name)
                    
                    for field_name, field_value in section_data.items():
                        pdf.add_field(field_name, field_value)
                    
                    pdf.ln(5)
            
            # Find and add product images
            image_paths = find_product_images(product_type)
            if image_paths:
                pdf.add_section_header("Product Images")
                add_image_grid_to_pdf(pdf, image_paths, images_per_row=2)

            
            # Save PDF
            safe_model = "".join(c for c in model if c.isalnum() or c in (' ', '-', '_')).strip()[:20]
            filename = f"{product_type}_{date}_{safe_model.replace(' ', '_')}_brochure.pdf"
            output_path = os.path.join(output_dir, filename)
            
            pdf.output(output_path)
            print(f"[✓] Generated: {output_path}")
            
            # Print summary
            total_fields = sum(len(section) for section in organized_data.values())
            print(f"    📄 {len(organized_data)} sections, {total_fields} fields")
            if features:
                print(f"    ✨ {len(features)} key features highlighted")
            if key_specs:
                print(f"    🔑 {len(key_specs)} key specifications featured")
                
        except Exception as e:
            print(f"[!] Error generating PDF for {date}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    generate_brochure(product_type)
