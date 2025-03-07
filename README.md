# Web Crawler

A modular web crawler with Pinecone vector database integration.

## Setup

1. Make sure you have Python 3.10+ installed
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure the Pinecone API keys in the `.env` file:
   ```
   # Pinecone configuration
   PINECONE_API_KEY=your_api_key
   PINECONE_ENVIRONMENT=your_environment
   PINECONE_INDEX_NAME=your_default_index_name
   ```

## Running the Web Crawler

### Quick Start (Recommended)
Simply double-click the `crawl.bat` file or run:
```
python -m src.utils.simple_crawler
```

This will:
1. Prompt you for the Pinecone index name to use (with default from .env)
2. Prompt you for the website URL to crawl
3. Ask if you want to use the website's sitemap
4. Ask if you want to specify additional URLs manually
5. Start crawling immediately

### Advanced Configuration
If you need more control over the configuration, edit the `.env` file directly with all configuration options:
```
# Crawler configuration
START_URL=https://example.com
USE_START_URL=true
USE_SITEMAP=false
USE_MANUAL_URLS=false
SITEMAP_URL=https://example.com/sitemap.xml
MANUAL_URLS=https://example.com/page1,https://example.com/page2

# Quality settings for cleanup
MIN_TEXT_LENGTH=50
EMBEDDING_NEAR_ZERO_EPSILON=1e-6
MAX_ITERATIONS=100
SCAN_BATCH_SIZE=1000
```

Then run:
```
python main.py
```

## Running the Cleanup Utility

The cleanup utility scans the Pinecone index for bad vectors and allows you to delete them.

Double-click the `run_cleanup.bat` file or run:
```
python cleanup.py
```

## Project Structure

```
WebCrawler/
├── .env                  # Environment variables
├── main.py               # Main entry point
├── cleanup.py            # Cleanup entry point
├── crawl.bat             # Quick start batch file for running the crawler
├── run_cleanup.bat       # Windows batch file for running the cleanup utility
├── requirements.txt      # Python dependencies
├── src/
│   ├── config/           # Configuration modules
│   ├── crawlers/         # Web crawling modules
│   ├── indexers/         # Pinecone indexing modules
│   ├── processors/       # Content processing modules
│   ├── utils/            # Utility modules
│   │   ├── simple_crawler.py # Simplified crawler with minimal input
│   │   └── ...
│   ├── main.py           # Main execution logic
│   └── cleanup.py        # Cleanup utility logic
└── logs/                 # Log files
``` 