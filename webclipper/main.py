# src/webclip/main.py
import requests
from readability import Document
import html2text
import argparse
import sys
import re
import json
import time
from urllib.parse import urlparse, urljoin
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class TextOptions:
    """Configuration options for text formatting."""
    no_links: bool = False
    no_images: bool = False
    no_emphasis: bool = False
    no_tables: bool = False
    no_lists: bool = False
    strip_whitespace: bool = True
    preserve_formatting: bool = False

class WebClipError(Exception):
    """Custom exception for WebClip errors."""
    pass

class WebClip:
    """Main WebClip class for fetching and processing web content."""
    
    def __init__(self, timeout: int = 15, retries: int = 3, delay: float = 1.0):
        self.timeout = timeout
        self.retries = retries
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stderr)]
        )
        self.logger = logging.getLogger(__name__)

    def validate_url(self, url: str) -> str:
        """Validate and normalize URL."""
        if not url or not url.strip():
            raise WebClipError("Empty URL provided")
        
        url = url.strip()
        
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Validate URL structure
        parsed = urlparse(url)
        if not parsed.netloc:
            raise WebClipError(f"Invalid URL format: {url}")
        
        return url

    def fetch_with_retry(self, url: str) -> requests.Response:
        """Fetch URL with retry logic and better error handling."""
        url = self.validate_url(url)
        
        for attempt in range(self.retries):
            try:
                self.logger.info(f"Fetching {url} (attempt {attempt + 1}/{self.retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout for {url} on attempt {attempt + 1}")
                if attempt < self.retries - 1:
                    time.sleep(self.delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise WebClipError(f"Timeout after {self.retries} attempts")
                    
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error for {url} on attempt {attempt + 1}")
                if attempt < self.retries - 1:
                    time.sleep(self.delay * (2 ** attempt))
                else:
                    raise WebClipError(f"Connection failed after {self.retries} attempts")
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [429, 502, 503, 504]:  # Retry on server errors
                    self.logger.warning(f"Server error {e.response.status_code} for {url} on attempt {attempt + 1}")
                    if attempt < self.retries - 1:
                        time.sleep(self.delay * (2 ** attempt))
                        continue
                raise WebClipError(f"HTTP {e.response.status_code}: {e.response.reason}")
                
            except Exception as e:
                raise WebClipError(f"Unexpected error: {str(e)}")

    def extract_content(self, response: requests.Response) -> str:
        """Extract main content using readability."""
        try:
            doc = Document(response.text)
            return doc.summary()
        except Exception as e:
            self.logger.warning(f"Readability extraction failed: {e}")
            # Fallback to raw HTML
            return response.text

    def setup_html2text(self, output_format: str, text_options: TextOptions) -> html2text.HTML2Text:
        """Configure html2text converter based on options."""
        h = html2text.HTML2Text()
        h.body_width = 0
        h.unicode_snob = True  # Better Unicode handling
        h.escape_all = False   # Don't escape special characters unnecessarily
        
        if output_format == 'markdown':
            # Markdown format gets rich formatting
            h.ignore_links = False
            h.ignore_images = False
            h.ignore_emphasis = False
            h.ignore_tables = False
        else:
            # Plain text format respects user options
            h.ignore_links = text_options.no_links
            h.ignore_images = text_options.no_images
            h.ignore_emphasis = text_options.no_emphasis
            h.ignore_tables = text_options.no_tables
            
            # Additional plain text options
            if text_options.no_lists:
                h.ul_item_mark = ''
                h.ol_item_mark = ''
            
        return h

    def post_process_text(self, text: str, text_options: TextOptions) -> str:
        """Apply post-processing to the converted text."""
        if text_options.strip_whitespace:
            # Consolidate excessive newlines
            text = re.sub(r'\n{3,}', '\n\n', text)
            # Remove trailing whitespace from lines
            text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
            text = text.strip()
        
        if not text_options.preserve_formatting:
            # Clean up common formatting issues
            text = re.sub(r'^\s*\*\s*$', '', text, flags=re.MULTILINE)  # Remove lone asterisks
            text = re.sub(r'^\s*-\s*$', '', text, flags=re.MULTILINE)   # Remove lone dashes
            text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)               # Consolidate blank lines
        
        return text

    def get_url_content(self, url: str, output_format: str = 'text', 
                       text_options: Optional[TextOptions] = None) -> Tuple[str, Dict]:
        """
        Fetch URL content and convert to specified format.
        Returns tuple of (content, metadata).
        """
        if text_options is None:
            text_options = TextOptions()

        response = self.fetch_with_retry(url)
        cleaned_html = self.extract_content(response)
        
        # Extract metadata
        metadata = {
            'url': response.url,  # Final URL after redirects
            'status_code': response.status_code,
            'content_type': response.headers.get('content-type', ''),
            'content_length': len(response.text),
            'title': self._extract_title(cleaned_html),
            'encoding': response.encoding or 'utf-8'
        }

        h = self.setup_html2text(output_format, text_options)
        converted_text = h.handle(cleaned_html)
        processed_text = self.post_process_text(converted_text, text_options)
        
        return processed_text, metadata

    def _extract_title(self, html_content: str) -> str:
        """Extract title from HTML content."""
        try:
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            if title_match:
                return title_match.group(1).strip()
        except Exception:
            pass
        return "Untitled"

    def process_url(self, url: str, output_format: str, text_options: TextOptions, 
                   include_url: bool = False, include_metadata: bool = False, 
                   output_file: Optional[str] = None) -> bool:
        """
        Process a single URL and output the result.
        Returns True if successful, False otherwise.
        """
        try:
            content, metadata = self.get_url_content(url, output_format, text_options)
            
            # Prepare output
            output_lines = [content]
            
            if include_url:
                output_lines.append(f"\nSource: {metadata['url']}")
            
            if include_metadata:
                output_lines.append(f"\nMetadata:")
                output_lines.append(f"  Title: {metadata['title']}")
                output_lines.append(f"  Status: {metadata['status_code']}")
                output_lines.append(f"  Content-Type: {metadata['content_type']}")
                output_lines.append(f"  Length: {metadata['content_length']} chars")
            
            result = '\n'.join(output_lines)
            
            # Output to file or stdout
            if output_file:
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(result + "\n---\n\n")
                self.logger.info(f"Content saved to {output_file}")
            else:
                print(result)
                print("\n---\n")
            
            return True
            
        except WebClipError as e:
            self.logger.error(f"Failed to process {url}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error processing {url}: {e}")
            return False

    def process_urls_from_file(self, file_path: str, **kwargs) -> Tuple[int, int]:
        """
        Process URLs from a file.
        Returns tuple of (successful_count, total_count).
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            raise WebClipError(f"File not found: {file_path}")
        except Exception as e:
            raise WebClipError(f"Error reading file {file_path}: {e}")
        
        successful = 0
        total = len(urls)
        
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Processing URL {i}/{total}: {url}")
            if self.process_url(url, **kwargs):
                successful += 1
        
        return successful, total

def create_text_options(args) -> TextOptions:
    """Create TextOptions from command line arguments."""
    return TextOptions(
        no_links=args.no_links,
        no_images=args.no_images,
        no_emphasis=args.no_emphasis,
        no_tables=args.no_tables,
        no_lists=args.no_lists,
        strip_whitespace=not args.preserve_whitespace,
        preserve_formatting=args.preserve_formatting
    )

def main():
    """Main function to parse command-line arguments and run the conversion."""
    parser = argparse.ArgumentParser(
        description="Fetch and extract the main content of webpages with advanced options.",
        epilog="""
Examples:
  webclip https://example.com                    # Basic usage
  webclip https://example.com -m -i              # Markdown with source URL
  echo "https://example.com" | webclip           # From stdin
  webclip -f urls.txt -o output.txt              # Process file of URLs
  webclip https://example.com --no-links --quiet # Clean text output
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Primary arguments
    parser.add_argument("url", nargs='?', help="URL to process (optional if using -f or stdin)")
    parser.add_argument("-f", "--file", help="File containing URLs to process (one per line)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    
    # Format options
    parser.add_argument("-m", "--markdown", action="store_true", 
                       help="Output in Markdown format (default: plain text)")
    parser.add_argument("-i", "--include-url", action="store_true", 
                       help="Include source URL in output")
    parser.add_argument("--metadata", action="store_true", 
                       help="Include metadata (title, status, etc.) in output")
    
    # Text formatting options
    text_group = parser.add_argument_group('Text Formatting (ignored with -m)')
    text_group.add_argument("--no-links", action="store_true", help="Remove links")
    text_group.add_argument("--no-images", action="store_true", help="Remove image references")
    text_group.add_argument("--no-emphasis", action="store_true", help="Remove bold/italic")
    text_group.add_argument("--no-tables", action="store_true", help="Remove tables")
    text_group.add_argument("--no-lists", action="store_true", help="Remove list formatting")
    text_group.add_argument("--preserve-whitespace", action="store_true", 
                           help="Don't clean up excessive whitespace")
    text_group.add_argument("--preserve-formatting", action="store_true", 
                           help="Preserve original formatting quirks")
    
    # Network options
    net_group = parser.add_argument_group('Network Options')
    net_group.add_argument("--timeout", type=int, default=15, help="Request timeout (default: 15s)")
    net_group.add_argument("--retries", type=int, default=3, help="Retry attempts (default: 3)")
    net_group.add_argument("--delay", type=float, default=1.0, help="Delay between retries (default: 1.0s)")
    
    # Other options
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    parser.add_argument("--version", action="version", version="webclip 2.0")

    args = parser.parse_args()
    
    # Configure logging
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Initialize WebClip
    webclip = WebClip(timeout=args.timeout, retries=args.retries, delay=args.delay)
    
    # Prepare options
    output_format = 'markdown' if args.markdown else 'text'
    text_options = create_text_options(args)
    
    process_kwargs = {
        'output_format': output_format,
        'text_options': text_options,
        'include_url': args.include_url,
        'include_metadata': args.metadata,
        'output_file': args.output
    }
    
    try:
        if args.file:
            # Process URLs from file
            successful, total = webclip.process_urls_from_file(args.file, **process_kwargs)
            webclip.logger.info(f"Processed {successful}/{total} URLs successfully")
            sys.exit(0 if successful == total else 1)
            
        elif args.url:
            # Process single URL from argument
            success = webclip.process_url(args.url, **process_kwargs)
            sys.exit(0 if success else 1)
            
        elif not sys.stdin.isatty():
            # Process URLs from stdin
            successful = 0
            total = 0
            
            for line in sys.stdin:
                url = line.strip()
                if url and not url.startswith('#'):
                    total += 1
                    if webclip.process_url(url, **process_kwargs):
                        successful += 1
            
            if total == 0:
                webclip.logger.error("No valid URLs found in stdin")
                sys.exit(1)
            
            webclip.logger.info(f"Processed {successful}/{total} URLs successfully")
            sys.exit(0 if successful == total else 1)
            
        else:
            parser.error("No URL provided. Use a URL argument, -f option, or pipe URLs to stdin.")
            
    except KeyboardInterrupt:
        webclip.logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        webclip.logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
