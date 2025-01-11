# Getty Images Board Crawler

A Python-based web crawler designed to extract comprehensive metadata from Getty Images Board pages. This tool can scrape board information, asset details, and rich metadata while handling both JSON and HTML data sources.

## Features

- Complete metadata extraction from Getty Images boards
- Support for both image and video assets
- Duplicate record detection and prevention
- Comprehensive logging system
- CSV output with rich metadata fields
- Error handling and recovery
- Extensible parser architecture for multiple domains

## Prerequisites

- Python 3.6+
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/getty-board-crawler.git
cd getty-board-crawler
```

2. Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install requests beautifulsoup4
```

## Configuration

Create a configuration file `config.json` (optional):

```json
{
    "output_file": "getty_boards_data.csv",
    "existing_records_file": "existing_records.csv",
    "log_level": "INFO"
}
```

## Usage

### Basic Usage

```python
from getty_crawler import WebCrawler

urls = [
    "https://www.gettyimages.com/collaboration/boards/YOUR-BOARD-ID"
]

crawler = WebCrawler(
    urls=urls,
    output_file="getty_boards_data.csv"
)
crawler.crawl()
```

### Advanced Usage

```python
from getty_crawler import WebCrawler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='crawler.log'
)

# Initialize crawler with existing records
crawler = WebCrawler(
    urls=["https://www.gettyimages.com/collaboration/boards/YOUR-BOARD-ID"],
    output_file="getty_boards_data.csv",
    existing_records_file="existing_records.csv"
)

try:
    crawler.crawl()
except Exception as e:
    logging.error(f"Crawl failed: {str(e)}")
```

## Output Format

The crawler generates a CSV file with the following fields:

### Board Information
- `board_name`: Name of the Getty Images board
- `board_description`: Description of the board
- `board_created_date`: Board creation timestamp
- `board_last_updated`: Last update timestamp

### Asset Information
- `asset_id`: Unique identifier for each asset
- `asset_family`: Asset type (Editorial/Creative)
- `license_type`: License type (ED/RF/RR)
- `title`: Full asset title
- `date_created`: Original creation date
- `credit`: Artist/photographer credit
- `collection`: Collection name
- `is_video`: Boolean flag for video assets
- `preview_url`: Thumbnail image URL
- `video_preview_url`: Video preview URL (if available)
- `added_by_id`: User ID who added the asset
- `added_date`: When the asset was added
- `comments`: Number of comments on the asset
- `source_url`: Original URL where the asset was found

## Error Handling

The crawler includes comprehensive error handling:

- Network error recovery
- Malformed HTML handling
- File I/O error management
- Invalid URL detection
- JSON parsing error recovery
- Duplicate record handling

## Extending the Crawler

### Adding New Domains

1. Create a new parser class:

```python
class NewDomainParser:
    def parse(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        records = []
        # Add domain-specific parsing logic
        return records
```

2. Register the parser in WebCrawler:

```python
self.parsers = {
    'www.gettyimages.com': GettyBoardParser(),
    'www.newdomain.com': NewDomainParser(),
    'default': GenericParser()
}
```

### Adding New Metadata Fields

1. Update the GettyBoardParser class:

```python
def parse(self, soup: BeautifulSoup, url: str) -> List[Dict]:
    records = []
    # Add your new metadata extraction logic
    record['new_field'] = extract_new_field(soup)
    return records
```

2. Update the CSV output handling in WebCrawler.

## Logging

The crawler uses Python's built-in logging module with the following levels:

- DEBUG: Detailed information for debugging
- INFO: General information about crawler operation
- WARNING: Warning messages for potential issues
- ERROR: Error messages for failed operations
- CRITICAL: Critical errors that stop the crawler

Configure logging level in your code:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to new functions
- Include docstrings for new classes and methods
- Add unit tests for new features
- Update documentation as needed

## Testing

Run the test suite:

```bash
python -m unittest tests/test_crawler.py
```

## Common Issues and Solutions

### Rate Limiting

The crawler implements basic rate limiting by default. If you encounter rate limiting issues:

```python
crawler = WebCrawler(
    urls=urls,
    delay_between_requests=2.0  # Add delay in seconds
)
```

### Memory Usage

For large boards, implement batch processing:

```python
crawler = WebCrawler(
    urls=urls,
    batch_size=100  # Process in batches of 100 records
)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses BeautifulSoup4 for HTML parsing
- Uses requests library for HTTP operations
- Inspired by Getty Images board structure