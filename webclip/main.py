# src/webclip/main.py
import requests
from bs4 import BeautifulSoup
from readability import Document
import html2text
import argparse
import sys

def get_url_content(url, output_format='text'):
    """
    Fetches a URL, extracts the main content, and converts it to a specified format.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    doc = Document(response.content)
    cleaned_html = doc.summary()

    if output_format == 'markdown':
        h = html2text.HTML2Text()
        h.body_width = 0
        return h.handle(cleaned_html)
    else:
        soup = BeautifulSoup(cleaned_html, 'html.parser')
        return soup.get_text(separator='\n', strip=True)

def main():
    """
    Main function to parse command-line arguments and run the conversion.
    """
    parser = argparse.ArgumentParser(
        description="Fetch the main content of a webpage and output as Markdown or plain text.",
        epilog="Example: webclip https://example.com -m -i"
    )
    parser.add_argument("url", help="The URL of the webpage to process.")
    parser.add_argument("-m", "--markdown", action="store_true", help="Output in Markdown format. Default is plain text.")
    parser.add_argument("-i", "--include-url", action="store_true", help="Append the source URL at the end of the output.")

    args = parser.parse_args()
    output_format = 'markdown' if args.markdown else 'text'

    print(f"Fetching and converting {args.url} to {output_format}...", file=sys.stderr)

    try:
        content = get_url_content(args.url, output_format)
        print(content) # to stdout
        if args.include_url:
            print(f"\nSource: {args.url}") # to stdout
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

