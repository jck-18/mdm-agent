# MDM Agent - Master Data Management for Samsung Products

A comprehensive Master Data Management (MDM) Agent that scrapes, processes, normalizes, and enriches Samsung product data from multiple sources including e-commerce websites and internal documents.

## 🎯 Project Overview

This MDM Agent creates a unified master dataset for Samsung products (phones, watches, TVs) by:

- **Web Scraping**: Automated scraping from e-commerce sites (Amazon, Flipkart) using crawl4ai
- **Data Ingestion**: Processing internal CSV/PDF files with product specifications
- **Data Normalization**: LLM-based normalization for consistent data structure
- **Data Aggregation**: Combining data from multiple sources with intelligent merging
- **Data Enhancement**: Enriching product features using LLM
- **Export Capabilities**: Multiple output formats (JSON, PDF brochures, API)

## 🏗️ Project Structure

```
mdm-agent/
├── api/                    # REST API implementation
│   ├── app.py             # Flask/FastAPI server
│   ├── start_api.bat      # Windows startup script
│   └── start_api.sh       # Linux/Mac startup script
├── scripts/               # Core processing scripts
│   ├── scrape_runner.py   # Web scraping orchestrator
│   ├── aggregate_all_sources.py    # Data aggregation
│   ├── combine_and_normalize_product_specs.py  # Data normalization
│   ├── normalize_with_llm.py       # LLM-based normalization
│   ├── generate_brochure_pdf.py    # PDF generation
│   ├── load_internal_csv.py        # CSV data loader
│   └── load_scrapped_json.py       # JSON data loader
├── configs/               # Configuration files
│   ├── phones.yaml       # Phone scraping config
│   ├── watches.yaml      # Watch scraping config
│   └── tv.yaml          # TV scraping config
├── data/                 # Input data directory
│   ├── internal_specs.csv
│   └── internal_specs.pdf
├── output/               # Pipeline output directories
│   ├── raw/             # Raw scraped data
│   ├── combined/        # Combined source data
│   ├── normalized/      # Normalized data
│   └── aggregated/      # Final aggregated data
├── images/              # Product images
├── brochures/           # Generated PDF brochures
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- API keys for web scraping services (configured in YAML files)

### Installation

1. **Clone and setup environment:**
```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# Linux/Mac
source .venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## 🔄 Data Processing Pipeline

### 1. Web Scraping
```bash
python scripts/scrape_runner.py --config configs/phones.yaml
```
- Scrapes product data from configured e-commerce sites
- Saves raw data to `output/raw/`
- Supports multiple product categories (phones, watches, TV)

### 2. Data Aggregation
```bash
python scripts/aggregate_all_sources.py
```
- Combines data from web scraping and internal sources
- Performs initial data cleaning and structuring
- Output saved to `output/aggregated/`

### 3. Data Normalization
```bash
python scripts/normalize_with_llm.py
```
- Uses LLM to normalize and standardize data
- Applies consistent naming and formatting
- Creates unified data structure
- Output saved to `output/normalized/`

### 4. Generate Brochures
```bash
python scripts/generate_brochure_pdf.py
```
- Creates professional PDF brochures
- Includes product specifications and features
- Saves to `brochures/` directory

### 5. API Server (Optional)
```bash
# Windows
api\\start_api.bat
# Linux/Mac
./api/start_api.sh
```
- Serves normalized product data via REST API
- Supports multiple data formats
- Includes web interface for browsing data

## 🔍 Data Sources

### Web Sources
- **Amazon India**: Product listings and specifications
- **Flipkart**: Product details and features
- **Samsung Official**: Technical specifications

### Internal Sources
- **CSV Data**: Internal product database
- **PDF Documents**: Technical documentation and specifications

## 🛠️ Key Features

### Data Processing
- Multi-source data aggregation
- LLM-based data normalization
- Intelligent field mapping
- Data validation and quality checks

### Output Formats
- Structured JSON data
- Professional PDF brochures
- REST API endpoints
- Web interface for data browsing

### Automation
- Scheduled web scraping
- Automated data processing pipeline
- Configurable processing rules
- Error handling and logging

## 📊 Data Quality

The system includes several data quality measures:

- **Validation**: Schema-based validation using Pydantic
- **Normalization**: LLM-based field normalization
- **Deduplication**: Intelligent merging of duplicate data
- **Enrichment**: Additional context from LLM processing
- **Versioning**: Date-based versioning of product data

## 🔒 Security

- API key management through environment variables
- Rate limiting for web scraping
- Input validation and sanitization
- Secure API endpoints

## 📈 Monitoring

The system provides monitoring through:

- Detailed logging of all operations
- Data quality metrics
- Processing statistics
- API usage tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is proprietary and confidential. All rights reserved.

## 📞 Support

For issues and support:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information

---

**Built with ❤️ for Samsung Product Data Management**
