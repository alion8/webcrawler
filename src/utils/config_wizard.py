"""
Configuration wizard for the web crawler.
This utility helps users set up their .env file interactively.
"""
import os
import re
from typing import Dict, Any, Optional

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60 + "\n")

def get_input(prompt: str, default: Optional[str] = None, validator=None) -> str:
    """
    Get user input with a prompt and optional default value.
    
    Args:
        prompt: The prompt to display to the user.
        default: The default value to use if the user enters nothing.
        validator: A function that validates the input and returns True if valid.
        
    Returns:
        The user input or the default value.
    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    while True:
        user_input = input(full_prompt).strip()
        
        if not user_input and default:
            return default
        
        if not user_input:
            print("Input cannot be empty. Please try again.")
            continue
        
        if validator and not validator(user_input):
            continue
            
        return user_input

def get_boolean_input(prompt: str, default: bool = False) -> bool:
    """
    Get a boolean input from the user.
    
    Args:
        prompt: The prompt to display to the user.
        default: The default value to use if the user enters nothing.
        
    Returns:
        True if the user entered 'y', 'yes', or 'true', False otherwise.
    """
    default_str = "y" if default else "n"
    response = get_input(f"{prompt} (y/n)", default_str)
    return response.lower() in ("y", "yes", "true")

def validate_url(url: str) -> bool:
    """
    Validate a URL.
    
    Args:
        url: The URL to validate.
        
    Returns:
        True if the URL is valid, False otherwise.
    """
    # Simple URL validation
    pattern = re.compile(
        r'^(https?://)'  # http:// or https://
        r'([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+' # domain
        r'[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?' # domain
        r'(/[a-zA-Z0-9_-]+)*/?$'  # path
    )
    
    if not pattern.match(url):
        print("Invalid URL format. Please enter a valid URL (e.g., https://example.com).")
        return False
    return True

def validate_number(value: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
    """
    Validate a numeric input.
    
    Args:
        value: The value to validate.
        min_val: The minimum allowed value.
        max_val: The maximum allowed value.
        
    Returns:
        True if the value is valid, False otherwise.
    """
    try:
        num = float(value)
        if min_val is not None and num < min_val:
            print(f"Value must be at least {min_val}.")
            return False
        if max_val is not None and num > max_val:
            print(f"Value must be at most {max_val}.")
            return False
        return True
    except ValueError:
        print("Invalid number format. Please enter a valid number.")
        return False

def validate_comma_separated_urls(urls: str) -> bool:
    """
    Validate a comma-separated list of URLs.
    
    Args:
        urls: The comma-separated list of URLs to validate.
        
    Returns:
        True if all URLs are valid, False otherwise.
    """
    if not urls:
        return True
        
    for url in urls.split(','):
        url = url.strip()
        if url and not validate_url(url):
            return False
    return True

def get_pinecone_config() -> Dict[str, str]:
    """
    Get Pinecone configuration from the user.
    
    Returns:
        A dictionary containing the Pinecone configuration.
    """
    print_header("Pinecone Configuration")
    print("Please enter your Pinecone API credentials:")
    
    config = {}
    config["PINECONE_API_KEY"] = get_input("Pinecone API Key")
    config["PINECONE_ENVIRONMENT"] = get_input("Pinecone Environment (e.g., us-west1-gcp)")
    config["PINECONE_INDEX_NAME"] = get_input("Pinecone Index Name")
    
    return config

def get_crawler_config() -> Dict[str, str]:
    """
    Get crawler configuration from the user.
    
    Returns:
        A dictionary containing the crawler configuration.
    """
    print_header("Crawler Configuration")
    print("Configure how the crawler will find and process URLs:")
    
    config = {}
    
    # Start URL configuration
    use_start_url = get_boolean_input("Use a start URL for crawling?", True)
    config["USE_START_URL"] = "true" if use_start_url else "false"
    
    if use_start_url:
        config["START_URL"] = get_input("Start URL (e.g., https://example.com)", validator=validate_url)
    else:
        config["START_URL"] = ""
    
    # Sitemap configuration
    use_sitemap = get_boolean_input("Use a sitemap for crawling?", False)
    config["USE_SITEMAP"] = "true" if use_sitemap else "false"
    
    if use_sitemap:
        config["SITEMAP_URL"] = get_input("Sitemap URL (e.g., https://example.com/sitemap.xml)", validator=validate_url)
    else:
        config["SITEMAP_URL"] = ""
    
    # Manual URLs configuration
    use_manual_urls = get_boolean_input("Use manually specified URLs for crawling?", False)
    config["USE_MANUAL_URLS"] = "true" if use_manual_urls else "false"
    
    if use_manual_urls:
        config["MANUAL_URLS"] = get_input(
            "Manual URLs (comma-separated, e.g., https://example.com/page1,https://example.com/page2)",
            validator=validate_comma_separated_urls
        )
    else:
        config["MANUAL_URLS"] = ""
    
    return config

def get_quality_settings() -> Dict[str, str]:
    """
    Get quality settings for the cleanup utility from the user.
    
    Returns:
        A dictionary containing the quality settings.
    """
    print_header("Quality Settings for Cleanup")
    print("Configure the parameters used to identify bad vectors:")
    
    config = {}
    
    config["MIN_TEXT_LENGTH"] = get_input(
        "Minimum text length (vectors with shorter text will be flagged as bad)",
        "50",
        lambda x: validate_number(x, min_val=1)
    )
    
    config["EMBEDDING_NEAR_ZERO_EPSILON"] = get_input(
        "Epsilon for near-zero embeddings (vectors with sum of absolute values below this will be flagged)",
        "1e-6",
        lambda x: validate_number(x, min_val=0)
    )
    
    config["MAX_ITERATIONS"] = get_input(
        "Maximum iterations for scanning",
        "100",
        lambda x: validate_number(x, min_val=1)
    )
    
    config["SCAN_BATCH_SIZE"] = get_input(
        "Batch size for scanning",
        "1000",
        lambda x: validate_number(x, min_val=1)
    )
    
    return config

def write_env_file(config: Dict[str, str], filename: str = ".env") -> bool:
    """
    Write the configuration to a .env file.
    
    Args:
        config: The configuration to write.
        filename: The name of the file to write to.
        
    Returns:
        True if the file was written successfully, False otherwise.
    """
    try:
        with open(filename, "w") as f:
            f.write("# Pinecone configuration\n")
            f.write(f"PINECONE_API_KEY={config['PINECONE_API_KEY']}\n")
            f.write(f"PINECONE_ENVIRONMENT={config['PINECONE_ENVIRONMENT']}\n")
            f.write(f"PINECONE_INDEX_NAME={config['PINECONE_INDEX_NAME']}\n\n")
            
            f.write("# Crawler configuration\n")
            f.write(f"START_URL={config['START_URL']}\n")
            f.write(f"USE_START_URL={config['USE_START_URL']}\n")
            f.write(f"USE_SITEMAP={config['USE_SITEMAP']}\n")
            f.write(f"USE_MANUAL_URLS={config['USE_MANUAL_URLS']}\n")
            f.write(f"SITEMAP_URL={config['SITEMAP_URL']}\n")
            f.write(f"MANUAL_URLS={config['MANUAL_URLS']}\n\n")
            
            f.write("# Quality settings for cleanup\n")
            f.write(f"MIN_TEXT_LENGTH={config['MIN_TEXT_LENGTH']}\n")
            f.write(f"EMBEDDING_NEAR_ZERO_EPSILON={config['EMBEDDING_NEAR_ZERO_EPSILON']}\n")
            f.write(f"MAX_ITERATIONS={config['MAX_ITERATIONS']}\n")
            f.write(f"SCAN_BATCH_SIZE={config['SCAN_BATCH_SIZE']}\n")
        
        return True
    except Exception as e:
        print(f"Error writing .env file: {e}")
        return False

def main():
    """Main function to run the configuration wizard."""
    clear_screen()
    print_header("Web Crawler Configuration Wizard")
    print("This wizard will help you set up your web crawler configuration.")
    print("Press Ctrl+C at any time to exit.\n")
    
    try:
        # Get configurations
        pinecone_config = get_pinecone_config()
        crawler_config = get_crawler_config()
        quality_settings = get_quality_settings()
        
        # Combine all configurations
        config = {**pinecone_config, **crawler_config, **quality_settings}
        
        # Write to .env file
        print_header("Saving Configuration")
        if write_env_file(config):
            print("Configuration saved successfully to .env file.")
            print("\nYou can now run the web crawler with:")
            print("  - On Windows: Double-click run_crawler.bat or run 'python main.py'")
            print("  - On Linux/Mac: Run './main.py'")
            print("\nTo run the cleanup utility:")
            print("  - On Windows: Double-click run_cleanup.bat or run 'python cleanup.py'")
            print("  - On Linux/Mac: Run './cleanup.py'")
        else:
            print("Failed to save configuration.")
        
    except KeyboardInterrupt:
        print("\n\nConfiguration wizard cancelled.")
        return

if __name__ == "__main__":
    main() 