# MDM Agent - Master Data Management for Samsung Products

A Master Data Management (MDM) Agent that scrapes, ingests, normalizes, and enriches Samsung product data from multiple sources including e-commerce websites and internal documents.

## 🎯 Project Overview

This MDM Agent focuses on creating a unified master dataset for Samsung Galaxy S24 with enriched product features by:

- **Web Scraping**: Using crawl4ai with LLM extraction strategy to scrape product data from e-commerce sites
- **Data Ingestion**: Processing internal CSV/PDF files containing product specifications
- **Data Normalization**: Creating structured master records using Pydantic models
- **Data Enhancement**: Using LLM to enrich and normalize product features
- **Export Capabilities**: Generating JSON and brochure-style PDF outputs

## 🏗️ Project Structure

```
mdm-agent-mvp/
├── src/                     # Core application code
│   ├── scraper.py          # Web scraping with crawl4ai/BeautifulSoup
│   ├── load_csv.py         # CSV data loader
│   ├── load_pdf.py         # PDF data loader
│   ├── llm_normalizer.py   # LLM-based data normalization
│   ├── validate.py         # Data validation using Pydantic
│   └── brochure_exporter.py # PDF/HTML brochure generation
├── data/                    # Internal data files
│   ├── internal_specs.csv  # Simulated internal product data
│   └── internal_specs.pdf  # PDF version of specs
├── schema/                  # Pydantic models and JSON schemas
│   ├── product_schema.py   # Main product schema
│   └── flat_product_specs.json # Exported JSON schema
├── raw_html/               # Scraped HTML content
├── brochures/              # Generated PDF brochures
├── output/                 # Pipeline output files
├── notebooks/              # Jupyter notebooks for analysis
├── run.py                  # Main CLI entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

1. **Clone and setup environment:**
```bash
python -m venv mdm-agent-env
# Windows
mdm-agent-env\Scripts\activate
# Linux/Mac
source mdm-agent-env/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Usage

#### Option 1: Run Complete Pipeline (Recommended)
```bash
python run.py run
```

This runs the entire MDM pipeline: ingest → normalize → validate → export

#### Option 2: Run Individual Steps
```bash
# Step 1: Ingest data from all sources
python run.py ingest --output-dir output

# Step 2: Normalize the ingested data
python run.py normalize --input-file output/raw_ingestion_YYYYMMDD_HHMMSS.json

# Step 3: Validate normalized data
python run.py validate --input-file output/normalized_data_YYYYMMDD_HHMMSS.json

# Step 4: Export to various formats
python run.py export --input-file output/normalized_data_YYYYMMDD_HHMMSS.json --formats json,pdf,html
```

### Testing Individual Components

```bash
# Test schema export
python export_schema.py

# Test CSV loader
python src/load_csv.py

# Test PDF loader
python src/load_pdf.py

# Test normalizer
python src/llm_normalizer.py

# Test validator
python src/validate.py

# Test brochure exporter
python src/brochure_exporter.py
```

## 📊 Data Sources

### Web Sources (Galaxy S24)
- **Samsung Official**: https://www.samsung.com/in/smartphones/galaxy-s24/specs/
- **Amazon India**: Product page with specifications
- **Flipkart**: Product page with specifications

### Internal Sources
- **CSV**: `data/internal_specs.csv` - Simulated internal product database
- **PDF**: `data/internal_specs.pdf` - Simulated internal documentation

## 🔧 Key Technologies

- **Web Scraping**: crawl4ai, BeautifulSoup4, aiohttp
- **Data Validation**: Pydantic v2
- **Data Processing**: pandas
- **PDF Generation**: WeasyPrint, Jinja2
- **CLI Interface**: Click
- **LLM Integration**: OpenAI (with mock implementation)

## 📋 Schema Structure

The master product record follows a comprehensive Pydantic schema with nested models:

- **Basic Info**: Product name, model, brand, category
- **Display**: Size, resolution, type, refresh rate
- **Performance**: Processor, RAM, storage
- **Camera**: Main, ultra-wide, telephoto, front cameras
- **Battery**: Capacity, charging speeds
- **Physical**: Dimensions, weight, materials
- **Features**: Special capabilities, connectivity

## 🎨 Output Formats

### 1. JSON Export
Structured JSON with complete product specifications:
```json
{
  "product_name": "Galaxy S24",
  "model_number": "SM-S921B",
  "display": {
    "size": "6.2 inches",
    "resolution": "2340 x 1080",
    "display_type": "Dynamic AMOLED 2X"
  },
  "confidence_score": 0.92
}
```

### 2. PDF Brochure
Professional product brochure with:
- Elegant design with Samsung brand colors
- Organized sections (Display, Performance, Camera, etc.)
- Visual specifications grid
- Color options and features list

### 3. Validation Report
Detailed validation results with:
- Schema compliance checking
- Business logic validation
- Data quality warnings
- Confidence scoring

## 🔍 Validation Features

- **Schema Validation**: Pydantic model compliance
- **Business Rules**: Price ranges, specification limits
- **Data Quality**: Completeness scoring
- **Source Tracking**: Multi-source data provenance

## 🧠 LLM Integration

The system includes a mock LLM normalizer that:
- Extracts and standardizes product specifications
- Handles multiple data formats and sources
- Provides confidence scoring
- Merges data from multiple sources intelligently

*Note: For production use, integrate with OpenAI API or other LLM services.*

## 📈 Data Quality Metrics

- **Confidence Score**: Calculated based on data completeness
- **Source Diversity**: Tracks multiple data sources
- **Validation Status**: Schema compliance and business rules
- **Completeness**: Percentage of filled essential fields

## 🛠️ Development

### Adding New Product Categories
1. Extend the Pydantic schema in `schema/product_schema.py`
2. Update normalization rules in `src/llm_normalizer.py`
3. Add category-specific validation in `src/validate.py`

### Adding New Data Sources
1. Implement new loader in `src/load_*.py`
2. Add source handling in `src/scraper.py`
3. Update normalization logic for new source format

### Customizing Output
1. Modify HTML template in `src/brochure_exporter.py`
2. Add new export formats as needed
3. Customize validation rules in `src/validate.py`

## 📄 License

This project is for demonstration purposes. Please respect the terms of service of scraped websites and ensure compliance with data usage policies.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For questions or issues, please refer to the project documentation or create an issue in the repository.

---

**Built with ❤️ for Samsung Product Data Management**
