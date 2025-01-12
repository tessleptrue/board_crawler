import os
import json
import csv
import subprocess
import logging
from typing import List, Dict
import re
from datetime import datetime

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
                '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                '-H', 'Accept-Language: en-US,en;q=0.9',
                '-H', 'Accept-Encoding: gzip, deflate, br',
                '--compressed'
            ]
            
            result = subprocess.run(['curl', '--verbose'] + headers + [url], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"curl failed with return code {result.returncode}: {result.stderr}")
            
            # Log the first part of the response to debug
            logging.debug(f"First 500 chars of response: {result.stdout[:500]}")
            
            return self._parse_html_response(result.stdout)
            
        except Exception as e:
            logging.error(f"Curl command failed: {str(e)}")
            raise

    def _parse_html_response(self, html_content: str) -> List[Dict]:
        """Parse the HTML response to extract collection data"""
        collection_data = []
        
        try:
            # Find all formats_data JSON strings
            # First look for all SearchResultV3 items
            search_results = re.findall(r'class="SearchResultV3[^>]*formats_data="([^"]*)"', html_content)
            logging.info(f"Found {len(search_results)} items in collection")
            
            if not search_results:
                # Debug: Look for some recognizable parts
                if 'SearchResultV3' in html_content:
                    logging.debug("Found SearchResultV3 in content, but couldn't extract items")
                if 'formats_data' in html_content:
                    logging.debug("Found formats_data in content, but couldn't extract items")
                
                formats_data_matches = re.findall(r'formats_data="([^"]*)"', html_content)
            else:
                formats_data_matches = search_results
            
            logging.info(f"Extracted {len(formats_data_matches)} format data entries")
            
            for formats_data_str in formats_data_matches:
                try:
                    # Unescape the JSON string and parse it
                    formats_data_str = formats_data_str.replace('&quot;', '"')
                    item_data = json.loads(formats_data_str)
                    
                    # Extract the video object data
                    video_obj = item_data.get('videoObject', {})
                    
                    # Create record
                    record = {
                        'item_id': item_data.get('id', ''),
                        'title': item_data.get('title', ''),
                        'description': video_obj.get('description', ''),
                        'url': f"https://www.pond5.com/stock-footage/item/{item_data.get('id')}",
                        'thumbnail_url': item_data.get('iurl', ''),
                        'artist': item_data.get('artistname', ''),
                        'duration_ms': item_data.get('durationms', ''),
                        'variant': item_data.get('variant', ''),
                        'price_range': item_data.get('prang', ''),
                        'upload_date': video_obj.get('uploadDate', ''),
                        'resolution': f"{item_data.get('x', '')}x{item_data.get('y', '')}",
                        'category': item_data.get('cat', ''),
                        'is_exclusive': item_data.get('isExclusive', False),
                        'is_free': item_data.get('isFree', False),
                        'min_price_usd': item_data.get('usd_lo', ''),
                        'max_price_usd': item_data.get('usd_hi', ''),
                        'content_url': video_obj.get('contentUrl', '')
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
            level=logging.DEBUG,  # Changed to DEBUG level for more verbose output
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