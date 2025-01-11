# Board Crawler

A simple web crawler for extracting content from board-style web platforms.

## Setup

1. Make sure you have Python 3.6 or newer installed

2. Set up a virtual environment:

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install requests beautifulsoup4
```

## Usage

1. Download `board_crawler.py`
2. Edit the `urls` list in the script to include your board URLs
3. Make sure your virtualenv is activated and run the script:

```bash
python board_crawler.py
```

The crawler will:
- Process all URLs in the list
- Save results to `board_data.csv`
- Show progress in the terminal

## Output

The script generates a CSV file containing:
- Platform information
- Board metadata
- Asset details
- Content information
- Timestamps and tracking data

## Currently Supported Platforms

- Getty Images boards

## Example URL Format

Getty Images boards should be in this format:
```
https://www.gettyimages.com/collaboration/boards/YOUR-BOARD-ID
```

## Troubleshooting

If you encounter any issues:
1. Check your internet connection
2. Verify the board URLs are correct and accessible
3. Ensure you have write permissions in the script's directory
4. Check the console output for error messages
5. Make sure your virtualenv is activated (you should see `(venv)` in your terminal prompt)

## Requirements

- Python 3.6+
- requests library
- beautifulsoup4 library

## Deactivating the Virtual Environment

When you're done, you can deactivate the virtual environment:

```bash
deactivate
```