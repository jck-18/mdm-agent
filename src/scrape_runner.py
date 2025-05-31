import asyncio
import json
import logging
import yaml
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMConfig
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# ──────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)


class ScrapeRunner:
    """
    Generalized scraper that reads a 'product-category' YAML,
    then iterates over each {source, url} entry.
    The JSON-CSS schemas and wait_for selectors are fully hard-coded
    (Amazon vs Flipkart) so you only need to supply URLs, API tokens, etc.
    """

    # ─── HARD-CODED “JSON-CSS” SCHEMAS FOR AMAZON + FLIPKART ──────────────────
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
            {
                "name":     "label",
                "selector": "td:nth-child(1)",
                "type":     "text"
            },
            {
                "name":     "value",
                "selector": "td:nth-child(2) li",
                "type":     "text",
                "multiple": True
            }
        ],
    }


    # ────────────────────────────────────────────────────────────────────────────
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.load_config()
        self.output_base = Path("output")
        self.output_base.mkdir(exist_ok=True)

    def load_config(self):
        """Load and validate the YAML configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as fh:
            self.cfg = yaml.safe_load(fh)

        # Required keys in each YAML
        required_keys = [
            "category",
            "urls",
            "api_token_primary",
            "api_token_secondary"
        ]
        for key in required_keys:
            if key not in self.cfg:
                raise KeyError(f"Missing '{key}' in config {self.config_path}")

        self.category = self.cfg["category"]
        self.urls = self.cfg["urls"]
        self.api_token_primary   = self.cfg["api_token_primary"]
        self.api_token_secondary = self.cfg["api_token_secondary"]

        # Validate that 'urls' is a non-empty list of {source, url}
        if not isinstance(self.urls, list) or len(self.urls) == 0:
            raise ValueError("Config 'urls' must be a non-empty list")

        for entry in self.urls:
            if "source" not in entry or "url" not in entry:
                raise KeyError("Each entry in 'urls' must have 'source' and 'url'")

    async def run(self):
        """Run scraping for each source sequentially, without extra delays."""
        results = []

        for entry in self.urls:
            source = entry["source"].lower()
            url    = entry["url"]

            # Decide which API token to use
            if source == "amazon":
                token = self.api_token_primary
            elif source == "flipkart":
                token = self.api_token_secondary
            else:
                token = self.api_token_primary  # fallback

            res = await self.scrape_one(source, url, token)
            results.append(res)

        # Final summary
        for res in results:
            src    = res.get("source", "?")
            status = res.get("status", "unknown")
            if status == "success":
                logger.info(f"  ✓ {src} → success")
            else:
                logger.error(f"  ✗ {src} → {res.get('error')}")

    async def scrape_one(self, source: str, url: str, api_token: str) -> dict:
        """
        Run a single JSON-CSS scrape using the given API token.
        Returns a dict with status, source, html_file, json_file, etc.
        """
        logger.info(f"Scraping '{source}' @ {url!r}")

        # ─── 1) BrowserConfig ────────────────────────────────────────────────────
        browser_cfg = BrowserConfig(
            browser_type="chromium",
            headless=True,
            extra_args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--no-first-run",
                "--disable-default-apps",
                "--disable-infobars",
            ],
            viewport_width=1280,
            viewport_height=800,
            text_mode=False,
            verbose=False,
        )

        # ─── 2) LLMConfig (although not used by JsonCss, the runner still needs a valid LLMConfig) ───
        llm_cfg = LLMConfig(
            provider="gemini/gemma-3-27b-it",
            api_token=api_token
        )

        # ─── 3) Pick the correct JsonCss schema + wait_for selector ─────────────
        if source == "amazon":
            schema = ScrapeRunner.AMAZON_SCHEMA
            wait_for = "css:table#productDetails_techSpec_section_1"
        else:  # flipkart
            schema = ScrapeRunner.FLIPKART_SCHEMA
            wait_for = "css:table._0ZhAN9"

        strategy = JsonCssExtractionStrategy(
            schema=schema,
            multiple=False  # return a single list-of-rows as JSON
        )

        # ─── 4) Build CrawlerRunConfig ─────────────────────────────────────────
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

        # ─── 5) Execute the crawl ──────────────────────────────────────────────
        try:
            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                result = await crawler.arun(url=url, config=run_cfg)
        except Exception as e:
            logger.exception(f"Exception while scraping {source}")
            return {
                "source": source,
                "status": "error",
                "error": str(e)
            }

        # ─── 6) Process success vs. failure ────────────────────────────────────
        if not getattr(result, "success", False):
            return {
                "source": source,
                "status": "error",
                "error": getattr(result, "error_message", "unknown")
            }
        '''
        # Save raw HTML (for debugging/inspection)
        html_path = (
            self.output_base
            / f"{self.category}_{source}_{datetime.now():%Y%m%d_%H%M%S}.html"
        )
        html_path.write_text(result.html, encoding="utf-8")
        '''
        def _clean_text(s: str) -> str:
            # Remove LEFT‐to‐RIGHT MARK (U+200E) and other zero-width characters, then strip whitespace
            return s.replace("\u200e", "").strip()

        raw_extracted = result.extracted_content  # whatever JsonCss gave you

        # If JsonCss returns a Python list of dicts, do:
        cleaned_rows = []
        if isinstance(raw_extracted, list):
            for row in raw_extracted:
                lbl = row.get("label", "")
                val = row.get("value", "")
                cleaned_rows.append({
                    "label": _clean_text(lbl),
                    "value": _clean_text(val),
                })
            extracted = cleaned_rows

        # If JsonCss returned a JSON-string, you might do:
        elif isinstance(raw_extracted, str):
            parsed = json.loads(raw_extracted)
            if isinstance(parsed, list):
                for row in parsed:
                    lbl = row.get("label", "")
                    val = row.get("value", "")
                    cleaned_rows.append({
                        "label": _clean_text(lbl),
                        "value": _clean_text(val),
                    })
                extracted = cleaned_rows
            else:
                # fallback: just keep it as-is or strip any invisible marks
                extracted = _clean_text(raw_extracted)
        


        # Save the extracted JSON to disk
        json_path = (
            self.output_base
            / f"{self.category}_{source}_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(extracted, f, indent=2, ensure_ascii=False)

        return {
            "source": source,
            "status": "success",
            #"html_file": str(html_path),
            "json_file": str(json_path)
        }


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = ArgumentParser(
        description="Run a category scraper based on a YAML config"
    )
    parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="Path to YAML config (e.g. configs/phones.yaml)"
    )
    args = parser.parse_args()

    runner = ScrapeRunner(Path(args.config))
    asyncio.run(runner.run())
