import os
import json
import csv
import subprocess
import logging
from typing import List, Dict
import re
from datetime import datetime
from bs4 import BeautifulSoup  # Added BeautifulSoup for better HTML parsing

class Pond5CollectionParser:
    def __init__(self):
        # Verify curl is available
        try:
            subprocess.run(['curl', '--version'], capture_output=True)
        except FileNotFoundError:
            raise RuntimeError("curl is not installed or not available in PATH")

    def _fetch_collection(self, collection_id: str) -> Dict:
        """Fetch the collection data using curl"""
        url = f"https://www.pond5.com/collections/{collection_id}"
        logging.info(f"Fetching collection URL: {url}")
        
        try:
            # Run curl command with necessary headers
            headers = [
                '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                '-H', 'Accept-Language: en-US,en;q=0.9',
                '-H', 'Accept-Encoding: gzip, deflate, br',
                '-H', 'Cache-Control: max-age=0',
                '-H', 'Upgrade-Insecure-Requests: 1',
                '-H', 'Sec-Fetch-Site: none',
                '-H', 'Sec-Fetch-Mode: navigate',
                '-H', 'Sec-Fetch-User: ?1',
                '-H', 'Sec-Fetch-Dest: document',
                '-H', 'Connection: keep-alive',
                '--compressed'
            ]
            
            # Run curl command with necessary headers and verbose output
            curl_cmd = ['curl', '--verbose', '-L', '--cookie-jar', '/tmp/cookies.txt'] + headers + [url]
            logging.info(f"Running curl command: {' '.join(curl_cmd)}")
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True)
            
            # Log both stdout and stderr for debugging
            logging.info(f"Curl stdout: {result.stdout}")
            logging.info(f"Curl stderr: {result.stderr}")
            
            if result.returncode != 0:
                raise Exception(f"curl failed with return code {result.returncode}: {result.stderr}")
            
            if not result.stdout.strip():
                logging.error("Received empty response from server")
                raise Exception("Empty response received from server")
            
            return self._parse_html_response(result.stdout)
            
        except Exception as e:
            logging.error(f"Curl command failed: {str(e)}")
            raise

    def _parse_html_response(self, html_content: str) -> List[Dict]:
        """Parse the HTML response to extract collection data"""
        collection_data = []
        
        try:
            logging.info(f"HTML content length: {len(html_content)}")
            # Parse HTML using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all search result items
            items = soup.find_all('div', class_='SearchResultsV3-item')
            logging.info(f"Found {len(items)} items in collection")
            
            # Print first item's HTML for debugging
            if items:
                logging.info("First item HTML:")
                logging.info(items[0].prettify())
            
            for item in items:
                try:
                    # Find the video object data
                    video_obj = item.find('div', {'itemtype': 'http://schema.org/VideoObject'})
                    if not video_obj:
                        continue
                        
                    # Extract metadata
                    metadata = {}
                    for meta in video_obj.find_all('meta', {'itemprop': True}):
                        metadata[meta.get('itemprop')] = meta.get('content')
                    
                    # Get formats data from the data attribute
                    formats_data = {}
                    formats_elem = item.find('a', {'formats_data': True})
                    if formats_elem:
                        try:
                            formats_data = json.loads(formats_elem['formats_data'])
                        except:
                            logging.warning("Failed to parse formats_data JSON")
                    
                    # Create record combining metadata and formats data
                    # Get URL from the anchor tag - with detailed debugging
                    anchor = item.find('a', {'class': ['SearchResultV3', 'js-searchResult', 'js-awProductLink']})
                    logging.info(f"Found anchor tag: {anchor is not None}")
                    if anchor:
                        logging.info(f"Anchor attributes: {anchor.attrs}")
                        url = anchor.get('href', '')
                        logging.info(f"Extracted URL: {url}")
                    else:
                        url = ''
                    
                    # Try alternate selectors if no URL found
                    if not url:
                        logging.info("Trying alternate selector")
                        # Try direct CSS selector
                        anchor = item.select_one('a.SearchResultV3')
                        if anchor:
                            url = anchor.get('href', '')
                            logging.info(f"Found URL with alternate selector: {url}")
                            
                    formats_data_elem = item.find('a', {'formats_data': True})
                    if formats_data_elem:
                        logging.info(f"formats_data element found: {formats_data_elem['formats_data'][:100]}")
                    
                    record = {
                        'item_id': formats_data.get('id', ''),
                        'title': metadata.get('name', ''),
                        'description': metadata.get('description', ''),
                        'url': url,
                        'thumbnail_url': metadata.get('thumbnailURL', ''),
                        'artist': formats_data.get('artistname', ''),
                        'duration_ms': formats_data.get('durationms', ''),
                        'variant': formats_data.get('variant', ''),
                        'price_range': formats_data.get('prang', ''),
                        'upload_date': metadata.get('uploadDate', ''),
                        'resolution': f"{formats_data.get('x', '')}x{formats_data.get('y', '')}",
                        'category': formats_data.get('cat', ''),
                        'is_exclusive': formats_data.get('isExclusive', False),
                        'is_free': formats_data.get('isFree', False),
                        'min_price_usd': formats_data.get('usd_lo', ''),
                        'max_price_usd': formats_data.get('usd_hi', ''),
                        'content_url': metadata.get('contentUrl', '')
                    }
                    collection_data.append(record)
                    
                except Exception as e:
                    logging.error(f"Failed to parse item data: {str(e)}")
                    continue
                    
            return collection_data
            
        except Exception as e:
            logging.error(f"Failed to parse HTML response: {str(e)}")
            raise

    def parse(self, collection_url: str) -> List[Dict]:
        collection_id = collection_url.split('/')[-1]
        collection_id = collection_id.split('-')[0]  # Handle URLs with slugs
        
        try:
            logging.info(f"Fetching collection ID: {collection_id}")
            collection_data = self._fetch_collection(collection_id)
            
            if not collection_data:
                logging.info("No items found in collection")
                return []
            
            # Add collection_id and source_url to each record
            for record in collection_data:
                record['collection_id'] = collection_id
                record['source_url'] = collection_url
            
            return collection_data
            
        except Exception as e:
            logging.error(f"Error processing collection {collection_id}: {str(e)}")
            raise

class WebCrawler:
    def __init__(self, output_file: str = "collection_data.csv", exclude_columns: List[str] = None):
        """
        Initialize the web crawler.
        
        Args:
            output_file (str): Path to the CSV output file
            exclude_columns (List[str]): List of column names to exclude from the output
        """
        logging.basicConfig(
            level=logging.INFO,  # Changed to INFO for less verbosity
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.output_file = output_file
        self.exclude_columns = exclude_columns or []
        self.existing_records = set()
        self.parser = Pond5CollectionParser()
        self._load_existing_records()
        
        # Log excluded columns
        if self.exclude_columns:
            logging.info(f"The following columns will be excluded: {', '.join(self.exclude_columns)}")

    def _filter_record(self, record: Dict) -> Dict:
        """Remove excluded columns from a record."""
        return {k: v for k, v in record.items() if k not in self.exclude_columns}

    def _load_existing_records(self):
        try:
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        record_id = f"{row['collection_id']}_{row['item_id']}"
                        self.existing_records.add(record_id)
                    logging.info(f"Loaded {len(self.existing_records)} existing records")
            else:
                logging.info("No existing records file found - will create new one")
        except Exception as e:
            logging.error(f"Error loading existing records: {str(e)}")
            if os.path.exists(self.output_file):
                os.rename(self.output_file, f"{self.output_file}.error")
            logging.info("Renamed problematic file and will start fresh")

    def _save_records(self, records: List[Dict]):
        if not records:
            logging.info("No new records to save")
            return

        try:
            # Filter excluded columns from records
            filtered_records = [self._filter_record(record) for record in records]
            
            new_records = []
            for record in filtered_records:
                record_id = f"{record['collection_id']}_{record['item_id']}"
                if record_id not in self.existing_records:
                    new_records.append(record)
                    self.existing_records.add(record_id)

            if not new_records:
                logging.info("No new unique records found")
                return

            file_exists = os.path.exists(self.output_file)
            mode = 'a' if file_exists else 'w'
            
            with open(self.output_file, mode, newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=new_records[0].keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerows(new_records)
                
            logging.info(f"Saved {len(new_records)} new records")
        except Exception as e:
            logging.error(f"Error saving records: {str(e)}")
            raise

    def crawl_collections(self, urls: List[str]):
        for url in urls:
            try:
                logging.info(f"Processing collection: {url}")
                records = self.parser.parse(url)
                self._save_records(records)
                logging.info(f"Successfully processed {len(records)} records")
            except Exception as e:
                logging.error(f"Failed to process {url}: {str(e)}")

def main():
    # Example: exclude certain columns
    exclude_columns = [
        'source_url',        # Hide source URLs
        'thumbnail_url',     # Hide thumbnail URLs
        'content_url'        # Hide content URLs
    ]
    
    urls = [
        "https://www.pond5.com/collections/6421444-judds-appalachia",
    ]
    
    crawler = WebCrawler(
        output_file="pond5_collection_data.csv",
        exclude_columns=exclude_columns
    )
    crawler.crawl_collections(urls)

if __name__ == "__main__":
    main()