"""
Simple crawler utility that takes minimal input and runs immediately.
"""
import os
import sys
import time
import asyncio
import logging
from dotenv import load_dotenv

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60 + "\n")

def get_input(prompt: str, default=None):
    """Get user input with a prompt and optional default value."""
    if default is not None:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    user_input = input(full_prompt).strip()
    if not user_input and default is not None:
        return default
    return user_input

def get_boolean_input(prompt: str, default: bool = False) -> bool:
    """Get a boolean input from the user."""
    default_str = "y" if default else "n"
    response = get_input(f"{prompt} (y/n)", default_str)
    return response.lower() in ("y", "yes", "true")

def setup_logging():
    """Configure and return a logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def run_crawler():
    """Run the crawler with user-provided settings."""
    # Load environment variables for API keys
    load_dotenv()
    
    # Check if required API keys are present
    api_key = os.getenv("PINECONE_API_KEY")
    environment = os.getenv("PINECONE_ENVIRONMENT")
    default_index_name = os.getenv("PINECONE_INDEX_NAME")
    
    if not all([api_key, environment]):
        print("Error: Missing Pinecone API configuration in .env file.")
        print("Please make sure you have the following variables set:")
        print("  - PINECONE_API_KEY")
        print("  - PINECONE_ENVIRONMENT")
        input("\nPress Enter to exit...")
        return
    
    # Get crawler settings from user
    clear_screen()
    print_header("Web Crawler Quick Start")
    
    # Get the Pinecone index name
    index_name = get_input("Enter the Pinecone index name to use", default_index_name)
    if not index_name:
        print("Error: Index name cannot be empty.")
        input("\nPress Enter to exit...")
        return
    
    # Ask for crawling method preferences first
    use_sitemap = get_boolean_input("Do you want to use a sitemap?", False)
    use_manual_urls = get_boolean_input("Do you want to specify URLs manually?", False)
    
    # Get the start URL only if not using sitemap or manual URLs
    start_url = ""
    use_start_url = False
    
    if not use_sitemap and not use_manual_urls:
        start_url = get_input("Enter the website URL to crawl (e.g., https://example.com)")
        if not start_url:
            print("Error: URL cannot be empty when not using sitemap or manual URLs.")
            input("\nPress Enter to exit...")
            return
        use_start_url = True
    
    # Get sitemap URL if using sitemap
    sitemap_url = ""
    if use_sitemap:
        sitemap_url = get_input("Enter the sitemap URL (e.g., https://example.com/sitemap.xml)")
        if not sitemap_url:
            print("Warning: Sitemap URL is empty. Sitemap crawling will be disabled.")
            use_sitemap = False
            # If sitemap was the only method and it's now disabled, require a website URL
            if not use_start_url and not use_manual_urls:
                start_url = get_input("Enter the website URL to crawl (e.g., https://example.com)")
                if not start_url:
                    print("Error: You must provide at least one method to crawl.")
                    input("\nPress Enter to exit...")
                    return
                use_start_url = True
    
    # Get manual URLs if using manual URLs
    manual_urls = ""
    if use_manual_urls:
        manual_urls = get_input("Enter comma-separated URLs (e.g., https://example.com/page1,https://example.com/page2)")
        if not manual_urls:
            print("Warning: No manual URLs provided. Manual URL crawling will be disabled.")
            use_manual_urls = False
            # If manual URLs was the only method and it's now disabled, require a website URL
            if not use_start_url and not use_sitemap:
                start_url = get_input("Enter the website URL to crawl (e.g., https://example.com)")
                if not start_url:
                    print("Error: You must provide at least one method to crawl.")
                    input("\nPress Enter to exit...")
                    return
                use_start_url = True
    
    # Ensure at least one crawling method is enabled
    if not use_start_url and not use_sitemap and not use_manual_urls:
        print("Error: You must enable at least one crawling method.")
        input("\nPress Enter to exit...")
        return
    
    # Set environment variables for the crawler
    os.environ["PINECONE_INDEX_NAME"] = index_name
    os.environ["START_URL"] = start_url
    os.environ["USE_START_URL"] = str(use_start_url).lower()
    os.environ["USE_SITEMAP"] = str(use_sitemap).lower()
    os.environ["SITEMAP_URL"] = sitemap_url
    os.environ["USE_MANUAL_URLS"] = str(use_manual_urls).lower()
    os.environ["MANUAL_URLS"] = manual_urls
    
    # Run the crawler
    print_header("Starting Web Crawler")
    print(f"Using Pinecone index: {index_name}")
    if use_start_url:
        print(f"Crawling website: {start_url}")
    if use_sitemap:
        print(f"Using sitemap: {sitemap_url}")
    if use_manual_urls:
        print(f"Using manual URLs: {manual_urls}")
    print("\nPress Ctrl+C to stop the crawler at any time.\n")
    
    # Import and run the main function from src.main
    try:
        from src.main import main
        main()
    except KeyboardInterrupt:
        print("\nCrawler stopped by user.")
    except Exception as e:
        print(f"\nError running crawler: {e}")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    run_crawler() 