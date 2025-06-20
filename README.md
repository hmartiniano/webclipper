# webclipper

**webclipper** is a simple Python tool to fetch the main content of a webpage and convert it into clean, readable Markdown or plain text. It removes clutter like ads, headers, and navigation bars, letting you focus on the article's text.

It can be used as a command-line application for quick conversions in your terminal or as a library in your own Python projects.

### Features

* **Content Extraction:** Uses `readibility` to identify and extract the primary article or content from a URL.
* **Dual Output:** Convertis cleaned HTML to either Markdown or plain text.
* **Flexible Usage:** Works as both a standalone command-line tool and an importable Python library.

### Installation

To install `webclipper`, you can clone the repository and install it using `pip`.

```

# Clone the repository (if you haven't already)

git clone [https://github.com/your-username/webclipper.git](https://www.google.com/search?q=https://github.com/your-username/webclipper.git)
cd webclipper

# Install the package in editable mode

# (Your changes to the source code will be reflected immediately)

pip install -e .

```

This will install the package and its dependencies, and also make the `webclipper` command available in your terminal.

### How to Use

#### As a Command-Line App

Once installed, you can use the `webclipper` command directly from your terminal. The output is sent to standard output, so you can easily redirect it to a file.

**Basic Usage (get plain text):**

```

webclipper "[https://en.wikipedia.org/wiki/Python\_(programming\_language](https://en.wikipedia.org/wiki/Python_\(programming_language\))"

```

**Get Markdown Output:**

Use the `-m` or `--markdown` flag.

```

webclipper "[https://www.some-article-url.com](https://www.google.com/search?q=https://www.some-article-url.com)" --markdown

```

**Include the Source URL:**

Use the `-i` or `--include-url` flag to append the source URL at the end of the output.

```

webclipper "[https://www.some-article-url.com](https://www.google.com/search?q=https://www.some-article-url.com)" -m -i

```

**Redirect to a File:**

You can save the output using standard shell redirection.

```

webclipper "[https://www.some-article-url.com](https://www.google.com/search?q=https://www.some-article-url.com)" \> my\_article.txt

```

#### As a Library

You can also import `webclipper` into your own Python scripts to integrate its functionality. The `get_url_content` function is all you need.

```python

from webclipper import get\_url\_content

# The URL of the article you want to clip

article\_url = "[https://en.wikipedia.org/wiki/Web\_scraping](https://en.wikipedia.org/wiki/Web_scraping)"

try:
    # Get the content as Markdown
    markdown\_content = get\_url\_content(article\_url, output\_format='markdown')
    print("--- MARKDOWN ---")
    print(markdown\_content)

    # Get the content as plain text
    text_content = get_url_content(article_url, output_format='text')
    print("\n--- PLAIN TEXT ---")
    print(text_content)

except Exception as e:
    print(f"An error occurred: {e}")

```

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.
