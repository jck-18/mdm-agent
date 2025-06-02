"""
Flask REST API for MDM Agent - Product Data Management
Serves normalized product data from JSON files through REST endpoints
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from flask import Flask, jsonify, request, render_template, send_from_directory, url_for, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import NotFound, BadRequest

# === Configuration ===
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Get project root and data directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
NORMALIZED_DATA_DIR = os.path.join(PROJECT_ROOT, "normalized_output")
COMBINED_DATA_DIR = os.path.join(PROJECT_ROOT, "combined_output")
AGGREGATED_DATA_DIR = os.path.join(PROJECT_ROOT, "aggregated_output")
RAW_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
INTERNAL_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
BROCHURES_DIR = os.path.join(PROJECT_ROOT, "brochures")

# Supported product types and data stages
PRODUCT_TYPES = ["phones", "tv", "watch"]
DATA_STAGES = {
    "raw": RAW_OUTPUT_DIR,
    "combined": COMBINED_DATA_DIR,
    "aggregated": AGGREGATED_DATA_DIR,
    "normalized": NORMALIZED_DATA_DIR,
    "internal": INTERNAL_DATA_DIR
}

# === Data Loading Utilities ===
def load_product_data(product_type: str, stage: str = "normalized") -> Dict[str, Any]:
    """Load product data for a given product type and processing stage"""
    if product_type not in PRODUCT_TYPES:
        raise ValueError(f"Invalid product type. Must be one of: {PRODUCT_TYPES}")
    
    if stage not in DATA_STAGES:
        raise ValueError(f"Invalid data stage. Must be one of: {list(DATA_STAGES.keys())}")
    
    if stage == "internal":
        # Internal data is in CSV format
        file_path = os.path.join(DATA_STAGES[stage], f"samsung_{product_type.replace('tv', 'frame_tv')}_detailed.csv")
        if product_type == "phones":
            file_path = os.path.join(DATA_STAGES[stage], "samsung_galaxy_s24_detailed.csv")
        elif product_type == "watch":
            file_path = os.path.join(DATA_STAGES[stage], "samsung_watch6_classic_detailed.csv")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No internal data found for product type: {product_type}")
        
        # Convert CSV to JSON-like structure
        import pandas as pd
        df = pd.read_csv(file_path)
        return {"internal_data": df.to_dict(orient="records")}
    
    elif stage == "raw":
        # Raw data contains individual scrape files
        import glob
        pattern = os.path.join(DATA_STAGES[stage], f"{product_type}_*.json")
        files = glob.glob(pattern)
        
        if not files:
            raise FileNotFoundError(f"No raw data found for product type: {product_type}")
        
        # Group files by source and date
        raw_data = {}
        for file_path in files:
            filename = os.path.basename(file_path)
            parts = filename.replace('.json', '').split('_')
            if len(parts) >= 4:
                source = parts[1]  # amazon, flipkart
                date = parts[2]    # YYYYMMDD
                time = parts[3]    # HHMMSS
                
                datetime_key = f"{date}_{time}"
                if datetime_key not in raw_data:
                    raw_data[datetime_key] = {}
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data[datetime_key][source] = json.load(f)
        
        return raw_data
    
    else:
        # For combined, aggregated, and normalized data
        if stage == "normalized":
            file_path = os.path.join(DATA_STAGES[stage], f"{product_type}_llm_normalized.json")
        else:
            file_path = os.path.join(DATA_STAGES[stage], f"{product_type}_{stage}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No {stage} data found for product type: {product_type}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

def get_available_brochures(product_type: str = None) -> List[str]:
    """Get available PDF brochures"""
    if not os.path.exists(BROCHURES_DIR):
        return []
    
    brochures = []
    for filename in os.listdir(BROCHURES_DIR):
        if filename.endswith('.pdf'):
            if product_type is None or filename.startswith(product_type):
                brochures.append(filename)
    
    return sorted(brochures)

def get_product_images(product_type: str, date: str = None, source: str = None) -> List[str]:
    """Get image filenames for a product type"""
    if not os.path.exists(IMAGES_DIR):
        return []
    
    images = []
    for filename in os.listdir(IMAGES_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
            # Expected format: {product_type}_{source}_{date}_{hash}.{ext}
            if filename.startswith(f"{product_type}_"):
                if source and f"_{source}_" not in filename:
                    continue
                if date and date not in filename:
                    continue
                images.append(filename)
    
    return sorted(images)

# === API Endpoints ===

@app.route("/", methods=["GET"])
def index():
    """Main route - redirect to web interface or show API info"""
    # Check if request accepts HTML (from browser)
    if 'text/html' in request.headers.get('Accept', ''):
        return web_index()
    
    # Otherwise return API information (for API clients)
    return jsonify({
        "service": "MDM Agent REST API",
        "version": "1.0.0",
        "description": "Product data management API for Samsung products",
        "web_interface": f"{request.host_url}web",
        "endpoints": {
            "GET /": "This help message or web interface",
            "GET /health": "Health check",
            "GET /products": "List all available product types and data stages",
            "GET /products/{type}": "Get products by type (default: normalized stage)",
            "GET /products/{type}?stage={stage}": "Get products by type and processing stage",
            "GET /products/{type}/{date}": "Get specific product by type and date",
            "GET /products/{type}/latest": "Get latest product of a specific type",
            "GET /raw/{type}": "Get raw scraped data by type",
            "GET /raw/{type}/{source}": "Get raw data by type and source (amazon/flipkart)",
            "GET /internal/{type}": "Get internal CSV data by type",
            "GET /images/{type}": "Get available images for a product type",
            "GET /images/{type}?source={source}": "Filter images by source",
            "GET /brochures": "Get available PDF brochures",
            "GET /brochures/{type}": "Get brochures for specific product type",
            "GET /search": "Search across all products"
        },
        "supported_types": PRODUCT_TYPES,
        "data_stages": list(DATA_STAGES.keys()),
        "timestamp": datetime.now().isoformat()
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "directories": {
            "normalized_data": NORMALIZED_DATA_DIR,
            "combined_data": COMBINED_DATA_DIR,
            "aggregated_data": AGGREGATED_DATA_DIR,
            "raw_output": RAW_OUTPUT_DIR,
            "internal_data": INTERNAL_DATA_DIR,
            "images": IMAGES_DIR,
            "brochures": BROCHURES_DIR
        },
        "data_availability": {
            stage: os.path.exists(directory) 
            for stage, directory in DATA_STAGES.items()
        }
    })

@app.route("/products", methods=["GET"])
def list_products():
    """List all available product types with data availability across all stages"""
    products_info = {}
    
    for product_type in PRODUCT_TYPES:
        type_info = {
            "available_stages": {},
            "total_stages_available": 0,
            "latest_date": None,
            "image_count": len(get_product_images(product_type)),
            "brochure_count": len(get_available_brochures(product_type))
        }
        
        # Check each data stage
        for stage in DATA_STAGES.keys():
            try:
                data = load_product_data(product_type, stage)
                if stage == "internal":
                    count = len(data.get("internal_data", []))
                    dates = ["internal"]
                elif stage == "raw":
                    count = len(data)
                    dates = list(data.keys())
                else:
                    count = len(data)
                    dates = list(data.keys()) if isinstance(data, dict) else []
                
                type_info["available_stages"][stage] = {
                    "available": True,
                    "count": count,
                    "dates": dates
                }
                type_info["total_stages_available"] += 1
                
                # Get latest date from normalized stage if available
                if stage == "normalized" and dates:
                    type_info["latest_date"] = max(dates)
                    
            except (FileNotFoundError, ValueError):
                type_info["available_stages"][stage] = {
                    "available": False,
                    "count": 0,
                    "dates": []
                }
        
        products_info[product_type] = type_info
    
    return jsonify({
        "products": products_info,
        "total_types": len(PRODUCT_TYPES),
        "available_stages": list(DATA_STAGES.keys()),
        "timestamp": datetime.now().isoformat()
    })

@app.route("/products/<product_type>", methods=["GET"])
def get_products_by_type(product_type: str):
    """Get all products of a specific type"""
    try:
        # Query parameters
        stage = request.args.get('stage', 'normalized')
        include_images = request.args.get('include_images', 'false').lower() == 'true'
        date_filter = request.args.get('date')
        
        data = load_product_data(product_type, stage)
        
        # Filter by date if specified (not applicable for internal data)
        if date_filter and stage != "internal":
            if isinstance(data, dict) and date_filter not in data:
                raise NotFound(f"No product found for date: {date_filter}")
            if isinstance(data, dict):
                data = {date_filter: data[date_filter]}
        
        # Add image information if requested
        if include_images and stage != "internal":
            if isinstance(data, dict):
                for date in data.keys():
                    images = get_product_images(product_type, date)
                    if isinstance(data[date], dict):
                        data[date]["_images"] = images
        
        return jsonify({
            "product_type": product_type,
            "stage": stage,
            "count": len(data) if isinstance(data, dict) else 1,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except ValueError as e:
        raise BadRequest(str(e))
    except FileNotFoundError as e:
        raise NotFound(str(e))

@app.route("/products/<product_type>/<date>", methods=["GET"])
def get_product_by_date(product_type: str, date: str):
    """Get specific product by type and date"""
    try:
        data = load_product_data(product_type)
        
        if date not in data:
            raise NotFound(f"No {product_type} product found for date: {date}")
        
        product = data[date]
        
        # Optional query parameters
        include_images = request.args.get('include_images', 'false').lower() == 'true'
        
        if include_images:
            images = get_product_images(product_type, date)
            product["_images"] = images
        
        return jsonify({
            "product_type": product_type,
            "date": date,
            "data": product,
            "timestamp": datetime.now().isoformat()
        })
        
    except ValueError as e:
        raise BadRequest(str(e))
    except FileNotFoundError as e:
        raise NotFound(str(e))

@app.route("/products/<product_type>/latest", methods=["GET"])
def get_latest_product(product_type: str):
    """Get latest product of a specific type"""
    try:
        data = load_product_data(product_type)
        
        if not data:
            raise NotFound(f"No products found for type: {product_type}")
        
        # Get the latest date
        latest_date = max(data.keys())
        product = data[latest_date]
        
        # Optional query parameters
        include_images = request.args.get('include_images', 'false').lower() == 'true'
        
        if include_images:
            images = get_product_images(product_type, latest_date)
            product["_images"] = images
        
        return jsonify({
            "product_type": product_type,
            "date": latest_date,
            "is_latest": True,
            "data": product,
            "timestamp": datetime.now().isoformat()
        })
        
    except ValueError as e:
        raise BadRequest(str(e))
    except FileNotFoundError as e:
        raise NotFound(str(e))

@app.route("/raw/<product_type>", methods=["GET"])
def get_raw_data(product_type: str):
    """Get raw scraped data for a product type"""
    try:
        data = load_product_data(product_type, "raw")
        
        # Query parameters
        source_filter = request.args.get('source')  # amazon, flipkart
        date_filter = request.args.get('date')
        
        # Filter by source or date if specified
        filtered_data = {}
        for datetime_key, sources in data.items():
            date_part = datetime_key.split('_')[0]
            
            # Date filter
            if date_filter and date_part != date_filter:
                continue
            
            # Source filter
            if source_filter:
                if source_filter in sources:
                    filtered_data[datetime_key] = {source_filter: sources[source_filter]}
            else:
                filtered_data[datetime_key] = sources
        
        return jsonify({
            "product_type": product_type,
            "stage": "raw",
            "source_filter": source_filter,
            "date_filter": date_filter,
            "count": len(filtered_data),
            "data": filtered_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except ValueError as e:
        raise BadRequest(str(e))
    except FileNotFoundError as e:
        raise NotFound(str(e))

@app.route("/raw/<product_type>/<source>", methods=["GET"])
def get_raw_data_by_source(product_type: str, source: str):
    """Get raw data by product type and specific source"""
    try:
        data = load_product_data(product_type, "raw")
        
        # Filter by source
        source_data = {}
        for datetime_key, sources in data.items():
            if source in sources:
                source_data[datetime_key] = sources[source]
        
        if not source_data:
            raise NotFound(f"No raw data found for {product_type} from source: {source}")
        
        return jsonify({
            "product_type": product_type,
            "source": source,
            "stage": "raw",
            "count": len(source_data),
            "data": source_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except ValueError as e:
        raise BadRequest(str(e))
    except FileNotFoundError as e:
        raise NotFound(str(e))

@app.route("/internal/<product_type>", methods=["GET"])
def get_internal_data(product_type: str):
    """Get internal CSV data for a product type"""
    try:
        data = load_product_data(product_type, "internal")
        
        return jsonify({
            "product_type": product_type,
            "stage": "internal",
            "count": len(data.get("internal_data", [])),
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except ValueError as e:
        raise BadRequest(str(e))
    except FileNotFoundError as e:
        raise NotFound(str(e))

@app.route("/brochures", methods=["GET"])
def get_all_brochures():
    """Get all available PDF brochures"""
    brochures = get_available_brochures()
    
    # Group by product type
    brochures_by_type = {}
    for brochure in brochures:
        for product_type in PRODUCT_TYPES:
            if brochure.startswith(product_type):
                if product_type not in brochures_by_type:
                    brochures_by_type[product_type] = []
                brochures_by_type[product_type].append(brochure)
                break
    
    return jsonify({
        "total_brochures": len(brochures),
        "brochures_by_type": brochures_by_type,
        "all_brochures": brochures,
        "brochures_directory": BROCHURES_DIR,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/brochures/<product_type>", methods=["GET"])
def get_brochures_by_type(product_type: str):
    """Get PDF brochures for a specific product type"""
    if product_type not in PRODUCT_TYPES:
        raise BadRequest(f"Invalid product type. Must be one of: {PRODUCT_TYPES}")
    
    brochures = get_available_brochures(product_type)
    
    return jsonify({
        "product_type": product_type,
        "count": len(brochures),
        "brochures": brochures,
        "brochures_directory": BROCHURES_DIR,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/images/<product_type>", methods=["GET"])
def get_images_by_type(product_type: str):
    """Get available images for a product type"""
    if product_type not in PRODUCT_TYPES:
        raise BadRequest(f"Invalid product type. Must be one of: {PRODUCT_TYPES}")
    
    # Query parameters
    source_filter = request.args.get('source')  # amazon, flipkart
    date_filter = request.args.get('date')
    
    images = get_product_images(product_type, date_filter, source_filter)
    
    # Group images by source and date
    images_info = {}
    for image in images:
        parts = image.split('_')
        if len(parts) >= 4:
            img_source = parts[1]
            img_date = parts[2]
            
            key = f"{img_source}_{img_date}"
            if key not in images_info:
                images_info[key] = []
            images_info[key].append(image)
    
    return jsonify({
        "product_type": product_type,
        "source_filter": source_filter,
        "date_filter": date_filter,
        "total_count": len(images),
        "images_by_source_date": images_info,
        "all_images": images,
        "images_directory": IMAGES_DIR,        "timestamp": datetime.now().isoformat()
    })

@app.route("/search", methods=["GET"])
def search_products():
    """Search across all product data"""
    query = request.args.get('q', '').strip()
    product_type_filter = request.args.get('type', '')
    stage_filter = request.args.get('stage', 'normalized')
    
    if not query:
        raise BadRequest("Query parameter 'q' is required")
    
    if len(query) < 2:
        raise BadRequest("Query must be at least 2 characters long")
    
    results = []
    search_types = [product_type_filter] if product_type_filter in PRODUCT_TYPES else PRODUCT_TYPES
    
    for product_type in search_types:
        try:
            data = load_product_data(product_type, stage_filter)
            
            if stage_filter == "internal":
                products = data.get("internal_data", [])
            elif isinstance(data, dict):
                products = []
                for date_key, date_data in data.items():
                    if isinstance(date_data, list):
                        products.extend(date_data)
                    else:
                        products.append(date_data)
            else:
                products = [data]
            
            # Search within products
            for product in products:
                if isinstance(product, dict):
                    # Convert product to searchable text
                    searchable_text = json.dumps(product, default=str).lower()
                    if query.lower() in searchable_text:
                        results.append({
                            "product_type": product_type,
                            "stage": stage_filter,
                            "product": product,
                            "relevance": searchable_text.count(query.lower())
                        })
        
        except (FileNotFoundError, ValueError):
            continue
    
    # Sort by relevance
    results.sort(key=lambda x: x["relevance"], reverse=True)
    
    return jsonify({
        "query": query,
        "product_type_filter": product_type_filter,
        "stage_filter": stage_filter,
        "total_results": len(results),
        "results": results[:50],  # Limit to 50 results
        "timestamp": datetime.now().isoformat()
    })

@app.route("/brochures/download/<filename>", methods=["GET"])
def download_brochure(filename: str):
    """Download a specific PDF brochure"""
    try:
        return send_from_directory(BROCHURES_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        raise NotFound(f"Brochure file not found: {filename}")

# === Web Interface Routes ===

@app.route("/web", methods=["GET"])
@app.route("/web/", methods=["GET"])
def web_index():
    """Web interface dashboard"""
    # Get basic statistics
    stats = {
        "total_products": 0,
        "total_brochures": len(get_available_brochures()),
        "total_images": 0,
        "data_sources": len(PRODUCT_TYPES)
    }
    
    for product_type in PRODUCT_TYPES:
        try:
            data = load_product_data(product_type, "normalized")
            if isinstance(data, dict):
                stats["total_products"] += len(data)
            else:
                stats["total_products"] += 1
        except (FileNotFoundError, ValueError):
            pass
        
        stats["total_images"] += len(get_product_images(product_type))
    
    return render_template('index.html', stats=stats)

@app.route("/web/products", methods=["GET"])
def web_products():
    """Web interface for products"""
    return render_template('products.html')

@app.route("/web/brochures", methods=["GET"])
def web_brochures():
    """Web interface for brochures"""
    return render_template('brochures.html')

@app.route("/web/api", methods=["GET"])
def web_api_docs():
    """Web interface for API documentation"""
    base_url = request.host_url.rstrip('/')
    return render_template('api_docs.html', base_url=base_url)

@app.route("/favicon.ico")
def favicon():
    """Serve favicon"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                              'favicon.ico', mimetype='image/vnd.microsoft.icon')

# === Error Handlers ===

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": str(error.description),
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "error": "Bad Request",
        "message": str(error.description),
        "timestamp": datetime.now().isoformat()
    }), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }), 500

# === Main ===
if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs(NORMALIZED_DATA_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    # Check if data files exist
    print("=== MDM Agent REST API ===")
    print(f"Data directory: {NORMALIZED_DATA_DIR}")
    print(f"Images directory: {IMAGES_DIR}")
    print("\nAvailable data files:")
    
    for product_type in PRODUCT_TYPES:
        file_path = os.path.join(NORMALIZED_DATA_DIR, f"{product_type}_llm_normalized.json")
        exists = "✓" if os.path.exists(file_path) else "✗"
        print(f"  {exists} {product_type}_llm_normalized.json")
    
    print(f"\nStarting API server on http://localhost:5000")
    print("Available interfaces:")
    print("  Web Interface: http://localhost:5000")
    print("  API Root: http://localhost:5000 (JSON)")
    print("  API Docs: http://localhost:5000/web/api")
    print("\nMain endpoints:")
    print("  GET /products - List all product types")
    print("  GET /products/{type} - Get products by type")
    print("  GET /products/{type}/{date} - Get specific product")
    print("  GET /products/{type}/latest - Get latest product")
    print("  GET /search?q={query} - Search products")
    
    app.run(debug=True, host="0.0.0.0", port=5000)
    
    app.run(debug=True, host="0.0.0.0", port=5000)
