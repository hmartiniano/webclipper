# src/webclip/main.py
import requests
from readability import Document
import html2text
import argparse
import sys
import re

def get_url_content(url, output_format='text', text_options=None):
    """
    Fetches a URL, extracts the main content, and converts it to a specified format
    with granular control over the text output.
    """
    if text_options is None:
        text_options = {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    doc = Document(response.text)
    cleaned_html = doc.summary()

    h = html2text.HTML2Text()
    h.body_width = 0

    if output_format == 'markdown':
        # Markdown format gets the default, rich conversion
        return h.handle(cleaned_html)
    else:
        # Plain text format respects the user-defined options
        h.ignore_links = text_options.get('no_links', False)
        h.ignore_images = text_options.get('no_images', False)
        h.ignore_emphasis = text_options.get('no_emphasis', False)
        h.ignore_tables = text_options.get('no_tables', False)

        plain_text = h.handle(cleaned_html)
        
        # Consolidate excessive newlines for cleaner output
        return re.sub(r'\n{3,}', '\n\n', plain_text).strip()

def process_url(url, output_format, text_options, include_url_option):
    """
    Processes a single URL: fetches, converts, and prints the content.
    """
    try:
        print(f"Fetching and converting {url} to {output_format}...", file=sys.stderr)
        content = get_url_content(url, output_format, text_options)
        print(content) # to stdout
        if include_url_option:
            print(f"\nSource: {url}") # to stdout
        # Add a separator for clarity when processing multiple URLs
        print("\n---\n", file=sys.stdout)
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}", file=sys.stderr)

def main():
    """
    Main function to parse command-line arguments and run the conversion.
    """
    parser = argparse.ArgumentParser(
        description="Fetch the main content of a webpage and output as Markdown or plain text. Reads from stdin if no URL is provided.",
        epilog="Example: webclip https://example.com -i"
    )
    # --- Primary Arguments ---
    # The URL is now optional, denoted by '?'
    parser.add_argument("url", nargs='?', default=None, help="The URL to process. If omitted, reads URLs from stdin.")
    parser.add_argument("-m", "--markdown", action="store_true", help="Output in Markdown format. Default is rich plain text.")
    parser.add_argument("-i", "--include-url", action="store_true", help="Append the source URL at the end of the output.")
    
    # --- Plain Text Formatting Arguments ---
    text_group = parser.add_argument_group('Plain Text Formatting (ignored if -m is used)')
    text_group.add_argument("--no-links", action="store_true", help="Remove links from plain text output.")
    text_group.add_argument("--no-images", action="store_true", help="Remove image references from plain text output.")
    text_group.add_argument("--no-emphasis", action="store_true", help="Remove bold/italic markers from plain text output.")
    text_group.add_argument("--no-tables", action="store_true", help="Remove tables from plain text output.")

    args = parser.parse_args()
    output_format = 'markdown' if args.markdown else 'text'

    text_options = {
        'no_links': args.no_links,
        'no_images': args.no_images,
        'no_emphasis': args.no_emphasis,
        'no_tables': args.no_tables,
    }

    if args.url:
        # If a URL is provided as an argument, process it.
        process_url(args.url, output_format, text_options, args.include_url)
    else:
        # If no URL argument, check for piped input from stdin.
        if not sys.stdin.isatty():
            for line in sys.stdin:
                url = line.strip()
                if url:
                    process_url(url, output_format, text_options, args.include_url)
        else:
            print("No URL provided and no data from stdin. Use -h for help.", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()

