import os
import json
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import logging
from typing import List, Dict, Optional, Type
import re

class BaseBoardParser:
    """Base class for all board parsers"""
    
    def parse(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Parse the board content and return list of records."""
        raise NotImplementedError("Each parser must implement parse() method")
    
    def can_handle_url(self, url: str) -> bool:
        """Check if this parser can handle the given URL."""
        raise NotImplementedError("Each parser must implement can_handle_url() method")

class GettyBoardParser(BaseBoardParser):
    """Parser for Getty Images board pages"""
    
    def can_handle_url(self, url: str) -> bool:
        return "gettyimages.com/collaboration/boards" in url
    
    def parse(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        records = []
        
        # Find the board data which is stored in a JavaScript variable
        scripts = soup.find_all('script')
        board_data = None
        
        # Debug logging to see what we're getting
        logging.debug(f"Found {len(scripts)} script tags")
        
        for script in scripts:
            if script.string and "collaboration.initialBoard" in script.string:
                # Extract the JSON data
                try:
                    # Debug logging
                    logging.debug("Found collaboration.initialBoard script")
                    logging.debug(f"Script content: {script.string[:500]}...")  # First 500 chars
                    
                    match = re.search(r'collaboration\.initialBoard = JSON\.parse\((.*?)\);', script.string)
                    if match:
                        try:
                            board_json = json.loads(json.loads(match.group(1)))
                            board_data = board_json
                            logging.debug("Successfully parsed board JSON data")
                            break
                        except json.JSONDecodeError as e:
                            logging.error(f"JSON parsing error: {str(e)}")
                            logging.debug(f"Failed to parse JSON: {match.group(1)[:500]}...")
                except Exception as e:
                    logging.error(f"Error processing script tag: {str(e)}")
                    continue
        
        if not board_data:
            logging.error("Could not find or parse board data")
            # Let's peek at the HTML to see what we got
            logging.debug(f"Page content sample: {str(soup)[:1000]}...")
            return []

        if not isinstance(board_data, dict):
            logging.error(f"Unexpected board_data type: {type(board_data)}")
            return []
        
        if board_data:
            # Extract board metadata
            board_name = board_data.get('name', '')
            board_description = board_data.get('description', '')
            created_date = board_data.get('created_date', '')
            last_updated_date = board_data.get('last_updated_date', '')
            platform = "Getty Images"
            
            # Find all asset containers in the HTML
            asset_containers = soup.find_all('div', class_='board-item')
            
            # Extract assets information and combine with HTML metadata
            assets = board_data.get('assets', [])
            for asset, container in zip(assets, asset_containers):
                record = self._extract_asset_data(
                    asset, container, board_name, board_description,
                    created_date, last_updated_date, platform, url
                )
                records.append(record)
                
        return records
    
    def _extract_asset_data(self, asset: Dict, container: BeautifulSoup,
                          board_name: str, board_description: str,
                          created_date: str, last_updated_date: str,
                          platform: str, url: str) -> Dict:
        """Extract data for a single asset"""
        record = {
            'platform': platform,
            'board_name': board_name,
            'board_description': board_description,
            'board_created_date': created_date,
            'board_last_updated': last_updated_date,
            'asset_id': asset.get('uri', '').replace('gi:', ''),
            'added_by_id': asset.get('added_by_id', ''),
            'added_date': asset.get('added_date', ''),
            'comments': len(asset.get('comments', [])),
            'source_url': url
        }
        
        if container:
            # Extract additional metadata from HTML
            record.update(self._extract_html_metadata(container))
        
        return record
    
    def _extract_html_metadata(self, container: BeautifulSoup) -> Dict:
        """Extract metadata from HTML container"""
        metadata = {}
        
        elements = {
            'asset_family': ('span', {'class_': 'asset-family'}),
            'license_type': ('span', {'class_': 'license-type'}),
            'title': ('span', {'class_': 'title'}),
            'date_created': ('span', {'class_': 'date-created'}),
            'collection': ('span', {'class_': 'collection'})
        }
        
        for key, (tag, attrs) in elements.items():
            elem = container.find(tag, **attrs)
            if elem:
                metadata[key] = elem.text.strip()
        
        # Extract credit/artist information
        artist_elem = container.find('span', class_='artist')
        if artist_elem:
            metadata['credit'] = artist_elem.text.replace('Credit:', '').strip()
        
        # Determine if asset is video
        metadata['is_video'] = bool(container.find('a', class_='play'))
        
        # Extract preview URLs
        img_elem = container.find('img', class_='board-asset')
        if img_elem:
            metadata['preview_url'] = img_elem.get('src', '')
            
        video_preview = container.find('div', attrs={'gi-video-on-hover': True})
        if video_preview:
            metadata['video_preview_url'] = video_preview.get('gi-video-on-hover', '')
            
        return metadata

class WebCrawler:
    """Main crawler class that orchestrates the parsing process"""
    
    def __init__(self, urls: List[str], output_file: str = "board_data.csv",
                 existing_records_file: Optional[str] = None):
        """Initialize the web crawler."""
        self.urls = urls
        self.output_file = output_file
        self.existing_records = set()
        
        # Initialize parsers
        self.parsers = [GettyBoardParser()]
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Load existing records if provided
        if existing_records_file and os.path.exists(existing_records_file):
            self._load_existing_records(existing_records_file)

    def _load_existing_records(self, filename: str):
        """Load existing records to avoid duplicates."""
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    record_id = f"{row.get('platform', '')}_{row.get('asset_id', '')}_{row.get('board_name', '')}"
                    self.existing_records.add(record_id)
            self.logger.info(f"Loaded {len(self.existing_records)} existing records")
        except Exception as e:
            self.logger.error(f"Error loading existing records: {str(e)}")
            raise

    def _fetch_page(self, url: str) -> str:
        """Fetch the HTML content of a page."""
        try:
            # Custom headers including common required ones and Mac Chrome user agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.gettyimages.com/',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Create a session to handle cookies
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Debug log to see what we got
            logging.debug(f"Response status code: {response.status_code}")
            logging.debug(f"Response headers: {dict(response.headers)}")
            logging.debug(f"First 1000 characters of response: {response.text[:1000]}")
            
            if 'Sign In - Getty Images' in response.text:
                raise Exception("Authentication required. Please make sure you're signed in to Getty Images and the board is accessible.")

            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            raise

    def _find_parser(self, url: str) -> Optional[BaseBoardParser]:
        """Find appropriate parser for the given URL"""
        for parser in self.parsers:
            if parser.can_handle_url(url):
                return parser
        return None

    def _parse_html(self, html: str, url: str) -> List[Dict]:
        """Parse HTML content using appropriate parser."""
        soup = BeautifulSoup(html, 'html.parser')
        parser = self._find_parser(url)
        
        if not parser:
            self.logger.warning(f"No parser found for URL: {url}")
            return []
        
        try:
            records = parser.parse(soup, url)
            return records
        except Exception as e:
            self.logger.error(f"Error parsing HTML from {url}: {str(e)}")
            return []

    def _save_records(self, records: List[Dict]):
        """Save new records to CSV file."""
        if not records:
            self.logger.info("No new records to save")
            return

        try:
            file_exists = os.path.exists(self.output_file)
            new_records = []
            
            # Filter out existing records
            for record in records:
                record_id = f"{record.get('platform', '')}_{record.get('asset_id', '')}_{record.get('board_name', '')}"
                if record_id not in self.existing_records:
                    new_records.append(record)
                    self.existing_records.add(record_id)

            if not new_records:
                self.logger.info("No new unique records found")
                return

            mode = 'a' if file_exists else 'w'
            with open(self.output_file, mode, newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=new_records[0].keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerows(new_records)
                
            self.logger.info(f"Saved {len(new_records)} new records")
        except Exception as e:
            self.logger.error(f"Error saving records: {str(e)}")
            raise

    def crawl(self):
        """Execute the web crawling process."""
        all_records = []
        for url in self.urls:
            try:
                self.logger.info(f"Crawling {url}")
                html = self._fetch_page(url)
                records = self._parse_html(html, url)
                all_records.extend(records)
                self.logger.info(f"Found {len(records)} records from {url}")
            except Exception as e:
                self.logger.error(f"Failed to crawl {url}: {str(e)}")
                continue

        if all_records:
            self._save_records(all_records)
            self.logger.info("Crawl completed successfully")
        else:
            self.logger.warning("No records found from any URL")

def main():
    # Set up logging with debug level when needed
    logging.basicConfig(
        level=logging.DEBUG,  # Changed from INFO to DEBUG
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # List of board URLs to crawl
    urls = [
        "https://www.gettyimages.com/collaboration/boards/IihIOXzjIke8Mc_He0lTMw",
        # Add more Getty Images board URLs here
    ]
    
    logging.info("Starting crawler...")
    
    # Initialize and run crawler
    crawler = WebCrawler(urls=urls)
    crawler.crawl()

if __name__ == "__main__":
    main()