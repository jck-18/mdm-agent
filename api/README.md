# MDM Agent REST API Documentation

## Overview

The MDM Agent REST API provides programmatic access to normalized Samsung product data. The API serves data from JSON files in the `normalized_output` folder and associated product images.

## Base URL
```
http://localhost:5000
```

## Authentication
Currently, no authentication is required. The API is designed for development and internal use.

## Response Format
All API responses follow this structure:
```json
{
  "data": "...",
  "timestamp": "2025-06-02T15:30:45.123456",
  "additional_metadata": "..."
}
```

## Endpoints

### 1. API Information
**GET /** 
- Returns API information and available endpoints
- **Response**: API metadata and endpoint list

**Example:**
```bash
curl http://localhost:5000/
```

### 2. Health Check
**GET /health**
- Health check endpoint for monitoring
- **Response**: Service status and configuration

**Example:**
```bash
curl http://localhost:5000/health
```

### 3. List Product Types
**GET /products**
- Lists all available product types with basic information
- **Response**: Product types with availability and counts

**Example:**
```bash
curl http://localhost:5000/products
```

**Response:**
```json
{
  "products": {
    "phones": {
      "available": true,
      "count": 1,
      "dates": ["20250601"],
      "latest_date": "20250601"
    },
    "tv": {
      "available": true,
      "count": 1,
      "dates": ["20250601"],
      "latest_date": "20250601"
    },
    "watch": {
      "available": true,
      "count": 1,
      "dates": ["20250601"],
      "latest_date": "20250601"
    }
  },
  "total_types": 3,
  "timestamp": "2025-06-02T15:30:45.123456"
}
```

### 4. Get Products by Type
**GET /products/{type}**
- Retrieves all products of a specific type
- **Parameters:**
  - `type`: Product type (phones, tv, watch)
- **Query Parameters:**
  - `include_images=true`: Include image filenames in response
  - `date=YYYYMMDD`: Filter by specific date

**Examples:**
```bash
# Get all phones
curl http://localhost:5000/products/phones

# Get phones with images
curl http://localhost:5000/products/phones?include_images=true

# Get phones for specific date
curl http://localhost:5000/products/phones?date=20250601
```

### 5. Get Product by Date
**GET /products/{type}/{date}**
- Retrieves specific product by type and date
- **Parameters:**
  - `type`: Product type (phones, tv, watch)
  - `date`: Date in YYYYMMDD format
- **Query Parameters:**
  - `include_images=true`: Include image filenames in response

**Example:**
```bash
curl http://localhost:5000/products/phones/20250601?include_images=true
```

**Response:**
```json
{
  "product_type": "phones",
  "date": "20250601",
  "data": {
    "os": "Android 14 with One UI 6.1",
    "dimensions": {
      "verified": "147.0 x 70.6 x 7.6 mm",
      "internal": "0.8 x 7.1 x 14.7 cm"
    },
    "weight": {
      "verified": "167 g",
      "internal": "167 g"
    },
    "_images": [
      "phones_amazon_20250602_150933_1442bc5e196c9cd683274bb99bbf6f50.jpg",
      "phones_amazon_20250602_150933_377dc4acf79134bc7c5c97d94a41cd4b.jpg"
    ]
  },
  "timestamp": "2025-06-02T15:30:45.123456"
}
```

### 6. Get Latest Product
**GET /products/{type}/latest**
- Retrieves the most recent product of a specific type
- **Parameters:**
  - `type`: Product type (phones, tv, watch)
- **Query Parameters:**
  - `include_images=true`: Include image filenames in response

**Example:**
```bash
curl http://localhost:5000/products/phones/latest?include_images=true
```

### 7. Get Images by Type
**GET /images/{type}**
- Lists all available images for a product type
- **Parameters:**
  - `type`: Product type (phones, tv, watch)

**Example:**
```bash
curl http://localhost:5000/images/phones
```

**Response:**
```json
{
  "product_type": "phones",
  "count": 13,
  "images": [
    "phones_amazon_20250602_150933_1442bc5e196c9cd683274bb99bbf6f50.jpg",
    "phones_amazon_20250602_150933_377dc4acf79134bc7c5c97d94a41cd4b.jpg"
  ],
  "timestamp": "2025-06-02T15:30:45.123456"
}
```

### 8. Get Images by Date
**GET /images/{type}/{date}**
- Lists images for specific product and date
- **Parameters:**
  - `type`: Product type (phones, tv, watch)
  - `date`: Date in YYYYMMDD format

**Example:**
```bash
curl http://localhost:5000/images/phones/20250602
```

### 9. Search Products
**GET /search**
- Search across all products
- **Query Parameters:**
  - `q`: Search query (required)
  - `type`: Filter by product type (optional)

**Examples:**
```bash
# Search all products
curl "http://localhost:5000/search?q=android"

# Search only phones
curl "http://localhost:5000/search?q=android&type=phones"
```

**Response:**
```json
{
  "query": "android",
  "product_type_filter": null,
  "count": 1,
  "results": [
    {
      "product_type": "phones",
      "date": "20250601",
      "data": {
        "os": "Android 14 with One UI 6.1",
        "..."
      }
    }
  ],
  "timestamp": "2025-06-02T15:30:45.123456"
}
```

## Error Responses

The API returns standard HTTP status codes and JSON error responses:

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid product type. Must be one of: ['phones', 'tv', 'watch']",
  "timestamp": "2025-06-02T15:30:45.123456"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "No phones product found for date: 20250602",
  "timestamp": "2025-06-02T15:30:45.123456"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "timestamp": "2025-06-02T15:30:45.123456"
}
```

## Data Structure

### Product Data Schema
The API serves normalized product data with the following structure:

```json
{
  "os": "Operating System",
  "dimensions": {
    "verified": "External dimensions",
    "internal": "Internal specifications"
  },
  "weight": {
    "verified": "Verified weight",
    "internal": "Internal specs weight"
  },
  "model_number": ["Model variants"],
  "wireless_communication_technologies": "Communication tech",
  "connectivity_technologies": ["Connectivity options"],
  "gps": true,
  "special_features": ["Feature list"],
  "display": {
    "size": "Display size",
    "resolution": "Resolution",
    "type": "Display technology"
  },
  "camera": {
    "primary": "Primary camera specs",
    "secondary": "Secondary camera specs"
  },
  "battery": {
    "capacity": "Battery capacity",
    "charging": "Charging specifications"
  },
  "_normalization_metadata": {
    "original_fields": 91,
    "normalized_fields": 48,
    "field_retention_ratio": 0.527,
    "source_metadata": {
      "scraped_fields": 82,
      "internal_fields": 10,
      "total_fields": 91,
      "aggregation_date": "2025-06-02T00:35:23.581087",
      "sources": ["amazon", "flipkart", "internal_csv"]
    }
  }
}
```

## Image Naming Convention

Images follow this naming pattern:
```
{product_type}_{source}_{date}_{hash}.{extension}
```

Example: `phones_amazon_20250602_150933_1442bc5e196c9cd683274bb99bbf6f50.jpg`

Where:
- `product_type`: phones, tv, watch
- `source`: amazon, flipkart, etc.
- `date`: YYYYMMDD_HHMMSS
- `hash`: MD5 hash of image URL
- `extension`: jpg, png, webp, etc.

## Getting Started

1. **Install Dependencies:**
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. **Start the API:**
   ```bash
   # Windows
   start_api.bat
   
   # Unix/Linux/Mac
   ./start_api.sh
   
   # Or directly
   python app.py
   ```

3. **Test the API:**
   ```bash
   curl http://localhost:5000/
   curl http://localhost:5000/products
   curl http://localhost:5000/products/phones/latest?include_images=true
   ```

## Development

### Adding New Endpoints
1. Define the route function in `app.py`
2. Add error handling
3. Update this documentation

### Data Sources
The API automatically loads data from:
- `../normalized_output/*.json` - Normalized product data
- `../images/*` - Product images

### Configuration
- **Host**: 0.0.0.0 (accessible from other machines)
- **Port**: 5000
- **Debug Mode**: Enabled in development
- **CORS**: Enabled for frontend access

## Support

For issues or questions:
1. Check the API logs for error details
2. Verify data files exist in `normalized_output/`
3. Ensure Flask dependencies are installed
4. Test endpoints with curl or Postman
