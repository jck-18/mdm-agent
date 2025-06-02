# [START — imports at top]
import asyncio
import json
import logging
import yaml
import requests
import hashlib
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser
import os

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMConfig
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# [Setup logging]
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)

# [Main ScrapeRunner class]
class ScrapeRunner:
    AMAZON_SCHEMA = {
        "type": "array",
        "baseSelector": "table#productDetails_techSpec_section_1 tr",
        "fields": [
            {"name": "label",  "selector": "th", "type": "text"},
            {"name": "value",  "selector": "td", "type": "text"}
        ],
    }

    FLIPKART_SCHEMA = {
        "type": "array",
        "baseSelector": "table._0ZhAN9 tr",
        "fields": [
            {"name": "label", "selector": "td:nth-child(1)", "type": "text"},
            {"name": "value", "selector": "td:nth-child(2) li", "type": "text", "multiple": True}
        ],
    }

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.load_config()
        self.output_base = Path("output")
        self.output_base.mkdir(exist_ok=True)

    def load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as fh:
            self.cfg = yaml.safe_load(fh)

        required_keys = ["category", "urls", "api_token_primary", "api_token_secondary"]
        for key in required_keys:
            if key not in self.cfg:
                raise KeyError(f"Missing '{key}' in config {self.config_path}")

        self.category = self.cfg["category"]
        self.urls = self.cfg["urls"]
        self.api_token_primary = self.cfg["api_token_primary"]
        self.api_token_secondary = self.cfg["api_token_secondary"]

        if not isinstance(self.urls, list) or len(self.urls) == 0:
            raise ValueError("Config 'urls' must be a non-empty list")
        for entry in self.urls:
            if "source" not in entry or "url" not in entry:
                raise KeyError("Each entry in 'urls' must have 'source' and 'url'")

    async def run(self):
        results = []
        for entry in self.urls:
            source = entry["source"].lower()
            url = entry["url"]
            token = self.api_token_primary if source == "amazon" else self.api_token_secondary
            res = await self.scrape_one(source, url, token)
            results.append(res)

        for res in results:
            src = res.get("source", "?")
            status = res.get("status", "unknown")
            if status == "success":
                logger.info(f"  ✓ {src} → success")
            else:
                logger.error(f"  ✗ {src} → {res.get('error')}")

    async def scrape_one(self, source: str, url: str, api_token: str) -> dict:
        logger.info(f"Scraping '{source}' @ {url!r}")

        browser_cfg = BrowserConfig(
            browser_type="chromium",
            headless=True,
            extra_args=[
                "--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled",
                "--disable-extensions", "--no-first-run", "--disable-default-apps", "--disable-infobars",
            ],
            viewport_width=1280,
            viewport_height=800,
            text_mode=False,
            verbose=False,
        )

        llm_cfg = LLMConfig(
            provider="gemini/gemma-3-27b-it",
            api_token=api_token
        )

        schema = ScrapeRunner.AMAZON_SCHEMA if source == "amazon" else ScrapeRunner.FLIPKART_SCHEMA
        wait_for = "css:table#productDetails_techSpec_section_1" if source == "amazon" else "css:table._0ZhAN9"

        strategy = JsonCssExtractionStrategy(schema=schema, multiple=False)

        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=strategy,
            wait_for=wait_for,
            page_timeout=120_000,
            js_code=["window.scrollTo(0, document.body.scrollHeight);"],
            delay_before_return_html=2.0,
            screenshot=False,
            verbose=False
        )

        try:
            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                result = await crawler.arun(url=url, config=run_cfg)
        except Exception as e:
            logger.exception(f"Exception while scraping {source}")
            return {"source": source, "status": "error", "error": str(e)}

        if not getattr(result, "success", False):
            return {"source": source, "status": "error", "error": getattr(result, "error_message", "unknown")}

        def _clean_text(s: str) -> str:
            return s.replace("\u200e", "").strip()

        raw_extracted = result.extracted_content
        cleaned_rows = []
        if isinstance(raw_extracted, list):
            for row in raw_extracted:
                lbl = row.get("label", "")
                val = row.get("value", "")
                cleaned_rows.append({"label": _clean_text(lbl), "value": _clean_text(val)})
            extracted = cleaned_rows
        elif isinstance(raw_extracted, str):
            try:
                parsed = json.loads(raw_extracted)
                for row in parsed:
                    lbl = row.get("label", "")
                    val = row.get("value", "")
                    cleaned_rows.append({"label": _clean_text(lbl), "value": _clean_text(val)})
                extracted = cleaned_rows
            except Exception:
                extracted = _clean_text(raw_extracted)

        # Save JSON
        json_path = self.output_base / f"{self.category}_{source}_{datetime.now():%Y%m%d_%H%M%S}.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(extracted, f, indent=2, ensure_ascii=False)        # EXTRA — Download images with selective filtering
        def download_images_from_html(html, source, date_str):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            img_dir = Path(project_root) / "images"
            img_dir.mkdir(exist_ok=True)  # Ensure the images directory exists
            soup = BeautifulSoup(html, "html.parser")
            
            # Get image selectors from config or use defaults
            product_selectors = [
                "#imageBlock", "#altImages", "#main-image-container", ".imgTagWrapper", "#imageBlock_feature_div",
                "#productImageContainer", "div.Pz+aTd", "div._1BweB8", "img._0DkuPH", "div._396cs4",
                "._20Gt85", "._2KpZ6l", "._30XEf0", ".CXW8mj", "._1AtVbE", "[data-id='LSTMOBGJXXADKMAVHZGXXMJT']",
                '[data-testid*="product"]', '[class*="product"]', '.gallery', '.product-gallery', 'main',
                'article', 'div[class*="image"]', 'div[class*="gallery"]'
]

            exclude_keywords = [
                'logo', 'icon', 'banner', 'ad', 'advertisement', 'promo', 'nav', 'navigation', 'header',
                'footer', 'sidebar', 'social', 'facebook', 'twitter', 'instagram', 'placeholder', 'loading',
                'spinner', 'avatar', 'badge', 'star', 'rating-star', 'checkout', 'cart', 'thumbnail'
    ]   

            min_size = {"width": 200, "height": 200}
            min_file_size = 10000
            max_file_size = 5000000  # 5 MB
            # Default selectors if none provided in config
            if not product_selectors:
                product_selectors = [
                    # Common product image containers
                    '[data-testid*="product"]',
                    '[class*="product"]',
                    '[id*="product"]',
                    '.gallery',
                    '.product-gallery',
                    '.product-images',
                    '.product-photos',
                    '.item-gallery',
                    '#product-details',
                    '#product-info',
                    '.pdp-', # Product Detail Page
                    '[data-component*="product"]',
                    '.main-content',
                    '.content-main',
                    # Amazon specific
                    '#feature-bullets',
                    '#productDetails',
                    '#detailBullets_feature_div',
                    '.a-carousel-container',
                    '.image-wrapper',
                    '.imgTagWrapper',
                    # Generic content areas (avoid headers, footers, ads)
                    'main',
                    'article',
                    '.container:has(img)',
                ]
            
            # Default exclude keywords if none provided
            if not exclude_keywords:
                exclude_keywords = [
                    'logo', 'icon', 'banner', 'ad', 'advertisement', 'promo',
                    'nav', 'navigation', 'header', 'footer', 'sidebar',
                    'social', 'facebook', 'twitter', 'instagram',                    'placeholder', 'loading', 'spinner', 'avatar',
                    'badge', 'star', 'rating-star', 'checkout', 'cart'
                ]
            
            saved_images = []
            images_found = []
            downloaded_urls = set()  # Track URLs to avoid duplicates
            
            # First, try to find images in specific product sections
            for selector in product_selectors:
                try:
                    sections = soup.select(selector)
                    for section in sections:
                        section_images = section.find_all("img")
                        images_found.extend(section_images)
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}")
                    continue
              # If no images found in specific sections, fall back to all images but with stricter filtering
            if not images_found:
                logger.info(f"No images found in product sections for {source}, falling back to all images with filtering")
                images_found = soup.find_all("img")
            
            logger.info(f"Found {len(images_found)} potential product images for {source}")
            
            processed_count = 0
            for img in images_found:
                processed_count += 1
                # Get image source
                src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if not src:
                    logger.debug(f"Image {processed_count}: No src found")
                    continue
                
                # Make relative URLs absolute
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/") and not src.startswith("//"):
                    # Skip relative URLs for now - would need base URL to resolve
                    continue
                elif not src.startswith("http"):
                    continue
                  # Skip if already downloaded
                if src in downloaded_urls:
                    continue
                    
                # Filter out unwanted images by URL patterns
                src_lower = src.lower()
                if any(keyword in src_lower for keyword in exclude_keywords):
                    logger.debug(f"Skipping image due to exclude keyword: {src}")
                    continue
                
                # Filter out very small images (likely icons/logos)
                width = img.get("width")
                height = img.get("height")
                if width and height:
                    try:
                        w, h = int(width), int(height)
                        if w < min_size["width"] or h < min_size["height"]:
                            continue
                    except:
                        pass
                
                # Filter by image classes and attributes
                img_class = " ".join(img.get("class", []))
                img_alt = img.get("alt", "")
                img_attrs = img_class + " " + img_alt + " " + str(img.get("data-testid", ""))
                if any(keyword in img_attrs.lower() for keyword in exclude_keywords):
                    logger.debug(f"Skipping image due to attribute keyword: {src}")
                    continue
                
                try:
                    # Get file extension from URL or default to jpg
                    file_ext = ".jpg"
                    if "." in src.split("/")[-1]:
                        potential_ext = "." + src.split(".")[-1].split("?")[0]
                        if potential_ext.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                            file_ext = potential_ext
                    
                    filename = hashlib.md5(src.encode()).hexdigest() + file_ext
                    filepath = filepath = img_dir / f"{self.category}_{source}_{date_str}_{filename}"

                    
                    # Download with headers to avoid blocking
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(src, timeout=10, headers=headers)
                    response.raise_for_status()
                    
                    # Check if it's actually an image by content type
                    content_type = response.headers.get('content-type', '')
                    if 'image' not in content_type.lower():
                        continue
                    
                    # Check minimum file size (avoid tiny images)
                    if len(response.content) < min_file_size:
                        continue
                    with open(filepath, "wb") as img_file:
                        img_file.write(response.content)
                    
                    downloaded_urls.add(src)  # Mark as downloaded
                    saved_images.append(str(filepath))
                    logger.info(f"Downloaded product image: {src}")
                    
                except Exception as e:
                    logger.warning(f"Failed to download image {src}: {e}")
            
            logger.info(f"Successfully downloaded {len(saved_images)} product images for {source}")
            return saved_images

        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        images_saved = download_images_from_html(result.html, source, date_str)

        return {
            "source": source,
            "status": "success",
            "json_file": str(json_path),
            "images": images_saved
        }

# ────────────────────────────────
if __name__ == "__main__":
    parser = ArgumentParser(description="Run a category scraper based on a YAML config")
    parser.add_argument("--config", "-c", required=True, help="Path to YAML config (e.g. configs/phones.yaml)")
    args = parser.parse_args()

    runner = ScrapeRunner(Path(args.config))
    asyncio.run(runner.run())
