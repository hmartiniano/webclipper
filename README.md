# webclip

**webclip** is a powerful Python tool to fetch, extract, and convert the main content of webpages into clean, readable Markdown or plain text. It intelligently removes clutter like ads, headers, and navigation bars, letting you focus on the article's core content.

It can be used as a command-line application for quick conversions, batch processing, or as a library in your own Python projects.

## Features

* **Smart Content Extraction:** Uses `readability` to identify and extract the primary article or content from any URL
* **Dual Output Formats:** Converts cleaned HTML to either rich Markdown or customizable plain text
* **Batch Processing:** Process multiple URLs from files or stdin for automation
* **Robust Network Handling:** Built-in retry logic with exponential backoff for unreliable connections
* **Flexible Text Options:** Fine-tune output by removing links, images, emphasis, tables, or lists
* **Metadata Extraction:** Optionally include page titles, status codes, and content information
* **Multiple Input Methods:** Single URLs, file lists, or piped input from other commands
* **Library Integration:** Clean API for use in your own Python projects

## Installation

To install `webclip`, you can clone the repository and install it using `pip`:

```bash
# Clone the repository
git clone https://github.com/your-username/webclip.git
cd webclip

# Install the package in editable mode
# (Your changes to the source code will be reflected immediately)
pip install -e .
```

This will install the package and its dependencies, and make the `webclip` command available in your terminal.

### Dependencies

```
requests
readability-lxml
html2text
```

## Command-Line Usage

### Basic Examples

**Get plain text content:**
```bash
webclip "https://en.wikipedia.org/wiki/Python_(programming_language)"
```

**Get Markdown output:**
```bash
webclip "https://www.example.com/article" --markdown
```

**Include source URL and metadata:**
```bash
webclip "https://www.example.com/article" -m -i --metadata
```

### Batch Processing

**Process URLs from a file:**
```bash
# Create a file with URLs (one per line)
echo "https://example.com/article1" > urls.txt
echo "https://example.com/article2" >> urls.txt

# Process all URLs and save to file
webclip -f urls.txt -o results.txt
```

**Process URLs from stdin:**
```bash
echo "https://example.com" | webclip --markdown
# or
cat urls.txt | webclip -m --no-links
```

### Text Formatting Options

**Clean text output (remove formatting elements):**
```bash
webclip "https://example.com" --no-links --no-images --no-emphasis
```

**Minimal text output:**
```bash
webclip "https://example.com" --no-links --no-images --no-tables --no-lists
```

**Preserve original formatting:**
```bash
webclip "https://example.com" --preserve-formatting --preserve-whitespace
```

### Network Configuration

**Custom timeout and retry settings:**
```bash
webclip "https://slow-site.com" --timeout 30 --retries 5 --delay 2.0
```

**Quiet mode for scripting:**
```bash
webclip "https://example.com" --quiet > content.txt
```

### Complete Command Reference

```
usage: webclip [-h] [-f FILE] [-o OUTPUT] [-m] [-i] [--metadata]
               [--no-links] [--no-images] [--no-emphasis] [--no-tables]
               [--no-lists] [--preserve-whitespace] [--preserve-formatting]
               [--timeout TIMEOUT] [--retries RETRIES] [--delay DELAY]
               [--quiet] [--version]
               [url]

Examples:
  webclip https://example.com                    # Basic usage
  webclip https://example.com -m -i              # Markdown with source URL
  echo "https://example.com" | webclip           # From stdin
  webclip -f urls.txt -o output.txt              # Process file of URLs
  webclip https://example.com --no-links --quiet # Clean text output

Options:
  -h, --help            show this help message and exit
  url                   URL to process (optional if using -f or stdin)
  -f FILE, --file FILE  File containing URLs to process (one per line)
  -o OUTPUT, --output OUTPUT
                        Output file (default: stdout)
  -m, --markdown        Output in Markdown format (default: plain text)
  -i, --include-url     Include source URL in output
  --metadata            Include metadata (title, status, etc.) in output
  --quiet               Suppress progress messages
  --version             show program's version number and exit

Text Formatting (ignored with -m):
  --no-links            Remove links
  --no-images           Remove image references
  --no-emphasis         Remove bold/italic
  --no-tables           Remove tables
  --no-lists            Remove list formatting
  --preserve-whitespace Don't clean up excessive whitespace
  --preserve-formatting Preserve original formatting quirks

Network Options:
  --timeout TIMEOUT     Request timeout (default: 15s)
  --retries RETRIES     Retry attempts (default: 3)
  --delay DELAY         Delay between retries (default: 1.0s)
```

## Library Usage

You can import `webclip` into your own Python scripts for programmatic content extraction:

### Basic Usage

```python
from webclip.main import WebClip, TextOptions

# Initialize WebClip
webclip = WebClip()

# Extract content from a URL
url = "https://en.wikipedia.org/wiki/Web_scraping"

try:
    # Get Markdown content
    markdown_content, metadata = webclip.get_url_content(url, output_format='markdown')
    print("--- MARKDOWN ---")
    print(markdown_content)
    print(f"Title: {metadata['title']}")
    
    # Get plain text content with custom options
    text_options = TextOptions(no_links=True, no_images=True)
    text_content, _ = webclip.get_url_content(url, output_format='text', text_options=text_options)
    print("\n--- CLEAN TEXT ---")
    print(text_content)
    
except Exception as e:
    print(f"Error: {e}")
```

### Advanced Usage

```python
from webclip.main import WebClip, TextOptions

# Initialize with custom settings
webclip = WebClip(timeout=30, retries=5, delay=2.0)

# Custom text processing options
text_options = TextOptions(
    no_links=True,
    no_images=True,
    no_emphasis=False,  # Keep bold/italic
    strip_whitespace=True,
    preserve_formatting=False
)

urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
]

results = []
for url in urls:
    try:
        content, metadata = webclip.get_url_content(
            url, 
            output_format='text', 
            text_options=text_options
        )
        results.append({
            'url': url,
            'title': metadata['title'],
            'content': content,
            'success': True
        })
    except Exception as e:
        results.append({
            'url': url,
            'error': str(e),
            'success': False
        })

# Process results
successful = [r for r in results if r['success']]
failed = [r for r in results if not r['success']]

print(f"Successfully processed: {len(successful)}")
print(f"Failed: {len(failed)}")
```

### TextOptions Configuration

```python
from webclip.main import TextOptions

# Maximum cleanup - minimal text output
minimal_options = TextOptions(
    no_links=True,
    no_images=True,
    no_emphasis=True,
    no_tables=True,
    no_lists=True,
    strip_whitespace=True
)

# Preserve formatting - keep original structure
preserve_options = TextOptions(
    no_links=False,
    no_images=False,
    no_emphasis=False,
    no_tables=False,
    no_lists=False,
    strip_whitespace=False,
    preserve_formatting=True
)
```

## Error Handling

webclip includes comprehensive error handling for common web scraping issues:

- **Network timeouts** - Automatic retry with exponential backoff
- **HTTP errors** - Proper handling of 4xx/5xx status codes
- **Invalid URLs** - URL validation and normalization
- **Content extraction failures** - Graceful fallback to raw HTML
- **Encoding issues** - Automatic encoding detection and handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

