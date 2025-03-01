# Web Crawler

A modular web crawler with Pinecone vector database integration.

## Setup

1. Make sure you have Python 3.10+ installed
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following variables:
   ```
   # Pinecone configuration
   PINECONE_API_KEY=your_api_key
   PINECONE_ENVIRONMENT=your_environment
   PINECONE_INDEX_NAME=your_index_name
   
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

## Running the Web Crawler

### On Windows:
Double-click the `run_crawler.bat` file or run the following command in a terminal:
```
python main.py
```

### On Linux/Mac:
```
./main.py
```

## Running the Cleanup Utility

The cleanup utility scans the Pinecone index for bad vectors and allows you to delete them.

### On Windows:
Double-click the `run_cleanup.bat` file or run the following command in a terminal:
```
python cleanup.py
```

### On Linux/Mac:
```
./cleanup.py
```

## Project Structure

```
WebCrawler/
├── .env                  # Environment variables
├── main.py               # Main entry point
├── cleanup.py            # Cleanup entry point
├── run_crawler.bat       # Windows batch file for running the crawler
├── run_cleanup.bat       # Windows batch file for running the cleanup utility
├── requirements.txt      # Python dependencies
├── src/
│   ├── config/           # Configuration modules
│   ├── crawlers/         # Web crawling modules
│   ├── indexers/         # Pinecone indexing modules
│   ├── processors/       # Content processing modules
│   ├── utils/            # Utility modules
│   ├── main.py           # Main execution logic
│   └── cleanup.py        # Cleanup utility logic
└── logs/                 # Log files
``` 