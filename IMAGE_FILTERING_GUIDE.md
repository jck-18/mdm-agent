# Image Filtering Guide

The MDM Agent now supports selective image downloading to focus on product-related images and avoid downloading irrelevant content like logos, ads, and icons.

## How It Works

The system uses a multi-stage filtering approach:

1. **CSS Selector Targeting** - Searches within specific HTML sections that likely contain product images
2. **Keyword Filtering** - Excludes images with URLs/attributes containing unwanted keywords  
3. **Size Filtering** - Skips images below minimum dimensions or file sizes
4. **Content Validation** - Verifies downloaded content is actually an image

## Configuration

Add an `image_selectors` section to your YAML config files:

```yaml
image_selectors:
  # CSS selectors for product sections
  product_selectors:
    - "#imageBlock"              # Amazon main image block
    - "#altImages"               # Amazon alternative images
    - "._396cs4"                 # Flipkart main product image
    - "._1BweB8"                 # Flipkart image gallery
    - '[data-testid*="product"]' # Generic product containers
    - '.gallery'                 # Common gallery classes
    - 'main'                     # Main content area
    
  # Keywords to exclude from URLs/attributes
  exclude_keywords:
    - "logo"
    - "icon" 
    - "banner"
    - "ad"
    - "nav"
    - "header"
    - "footer"
    - "social"
    - "thumbnail"
    
  # Minimum image dimensions (pixels)
  min_size:
    width: 200
    height: 200
    
  # Minimum file size (bytes)
  min_file_size: 10000  # 10KB
```

## Default Behavior

If no `image_selectors` are configured, the system uses sensible defaults:

- **Product Selectors**: Common e-commerce product containers, Amazon/Flipkart specific selectors
- **Exclude Keywords**: Standard list of logos, ads, navigation elements
- **Min Size**: 100x100 pixels
- **Min File Size**: 5KB

## Examples by Product Type

### Phones
```yaml
image_selectors:
  min_size:
    width: 200
    height: 200
  min_file_size: 10000
```

### TVs  
```yaml
image_selectors:
  min_size:
    width: 300    # TVs should have larger images
    height: 200
  min_file_size: 15000  # 15KB
```

### Watches
```yaml
image_selectors:
  min_size:
    width: 150    # Smaller images acceptable for watches
    height: 150
  min_file_size: 8000   # 8KB
```

## Debugging Tips

- Check the logs for `"Found X potential product images"` to see how many images were found
- Look for `"No images found in product sections"` to see if fallback mode was used
- Use `"Downloaded product image:"` logs to see which images were actually saved
- Warnings like `"Failed to download image"` show which images were filtered out or failed

## Advanced Selectors

### Site-Specific Targeting

**Amazon:**
```yaml
product_selectors:
  - "#imageBlock"
  - "#imageBlock_feature_div" 
  - ".imgTagWrapper"
  - "#main-image-container"
```

**Flipkart:**
```yaml
product_selectors:
  - "._396cs4"
  - "._1BweB8" 
  - "._20Gt85"
  - "._1BweB8 ._396cs4"
```

### Custom Exclusions
```yaml
exclude_keywords:
  - "promo"          # Promotional banners
  - "sponsor"        # Sponsored content
  - "related"        # Related products
  - "recommendation" # Product recommendations
  - "review"         # Review images
```

## File Naming

Downloaded images are saved as:
`{source}_{timestamp}_{hash}.{ext}`

Example: `amazon_20250602_134512_a1b2c3d4e5f6.jpg`

- **source**: amazon, flipkart, etc.
- **timestamp**: YYYYMMDD_HHMMSS when scraping started
- **hash**: MD5 hash of image URL (prevents duplicates)
- **ext**: Original file extension (.jpg, .png, .webp, etc.)
