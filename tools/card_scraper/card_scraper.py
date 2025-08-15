#!/usr/bin/env python3
"""
Working scraper for Once upon a Galaxy wiki using curl user agent
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
import argparse
from urllib.parse import urljoin

class CardScraper:
    def __init__(self):
        self.base_url = "https://onceuponagalaxy.wiki.gg"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'curl/7.68.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def get_page_content(self, url):
        """Fetch page content with error handling"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def scrape_category(self, category_name, limit=10):
        """Scrape any category page to get card data"""
        category_url = f"https://onceuponagalaxy.wiki.gg/wiki/Category:{category_name}"
        print(f"Scraping {category_name} category: {category_url}")
        
        content = self.get_page_content(category_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Save the raw HTML for inspection
        with open(f'debug_{category_name.lower()}_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved debug HTML to debug_{category_name.lower()}_page.html")
        
        # Look for the main content area
        main_content = soup.find('div', id='mw-content-text')
        if not main_content:
            print("Could not find main content area")
            return []
        
        # Look for links to individual card pages
        card_links = []
        
        # Try different approaches to find card links
        # 1. Look for links in the category listing
        links = main_content.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            
            # Filter for likely card pages (not templates or categories)
            if (href.startswith('/wiki/') and 
                not href.startswith('/wiki/Template:') and
                not href.startswith('/wiki/Category:') and
                not href.startswith('/wiki/User:') and
                not href.startswith('/wiki/Talk:') and
                not href.startswith('/wiki/File:') and
                not href.startswith('/wiki/Help:') and
                not href.startswith('/wiki/Special:') and
                text and len(text) > 1 and
                not text.startswith('Template:')):
                
                card_links.append({
                    'url': urljoin(self.base_url, href),
                    'name': text,
                    'href': href
                })
        
        print(f"Found {len(card_links)} potential {category_name} links")
        
        # Remove duplicates based on URL
        unique_links = []
        seen_urls = set()
        for link in card_links:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        print(f"After deduplication: {len(unique_links)} unique {category_name} links")
        
        # Scrape each card page
        cards = []
        # Handle unlimited case
        if limit is None:
            links_to_process = unique_links
            total_count = len(unique_links)
        else:
            links_to_process = unique_links[:limit]
            total_count = min(limit, len(unique_links))
        
        for i, link in enumerate(links_to_process):
            print(f"\nScraping {category_name} {i+1}/{total_count}: {link['name']}")
            card_data = self.scrape_card_page(link['url'], link['name'], category_name.lower())
            if card_data:
                cards.append(card_data)
                # Save the card immediately after scraping
                self.save_single_card_to_json(card_data, category_name.lower())
                print(f"Successfully scraped and saved: {card_data['name']}")
            else:
                print(f"Failed to scrape: {link['name']}")
            
            time.sleep(2)  # Be respectful to the server
        
        return cards
    
    def scrape_card_page(self, card_url, expected_name, card_type_name):
        """Scrape individual card page to extract card data"""
        content = self.get_page_content(card_url)
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract card name
        card_name = self.extract_card_name(soup, expected_name)
        if not card_name:
            return None
        
        # Extract other card properties if available
        card_type = self.extract_card_type(soup)
        card_rarity = self.extract_card_rarity(soup)
        card_cost = self.extract_card_cost(soup)
        card_images = self.extract_card_images(soup)
        
        # Extract character-specific properties
        card_traits = self.extract_card_traits(soup)
        card_attack = self.extract_card_attack(soup)
        card_health = self.extract_card_health(soup)
        card_deck_type = self.extract_card_deck_type(soup)
        
        # Extract abilities as a list
        card_abilities = self.extract_card_abilities(soup)
        
        # Extract description only for non-character cards (treasures, spells)
        card_description = None
        if card_type_name.lower() != "characters":
            card_description = self.extract_card_description(soup)
        
        card_data = {
            "name": card_name,
            "type": card_type_name  # Use the category name as the card type
        }
        
        # Add optional fields if found
        if card_description:
            card_data["description"] = card_description
        if card_rarity:
            card_data["rarity"] = card_rarity
        if card_cost:
            card_data["cost"] = card_cost
        if card_images:
            card_data["images"] = card_images
        if card_traits:
            card_data["traits"] = card_traits
        if card_abilities:
            card_data["abilities"] = card_abilities
        if card_attack:
            card_data["attack"] = card_attack
        if card_health:
            card_data["health"] = card_health
        if card_deck_type:
            card_data["deck_type"] = card_deck_type
        
        return card_data
    
    def extract_card_name(self, soup, expected_name):
        """Extract card name from the page"""
        # Try to find the main heading (h1)
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text().strip()
            if name and name != expected_name:
                print(f"  Name mismatch: expected '{expected_name}', got '{name}'")
            return name or expected_name
        
        # Fallback to page title
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()
            # Remove common wiki suffixes
            if ' - Once Upon a Galaxy Wiki' in title_text:
                return title_text.replace(' - Once Upon a Galaxy Wiki', '').strip()
            return title_text
        
        return expected_name
    
    def extract_card_description(self, soup):
        """Extract card description/effect text"""
        # Look for description in the druid-infobox (card attributes)
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            # Try different possible description row names
            description_selectors = [
                'druid-row-ability_2_description',  # Zeus style
                'druid-row-ability_description',    # Barrel of Monkeys style
                'druid-row-ability'                 # Treasure style
            ]
            
            for selector in description_selectors:
                ability_desc_row = infobox.find('div', class_=selector)
                if ability_desc_row:
                    # Try to find the corresponding data div
                    data_selector = selector.replace('druid-row-', 'druid-data-')
                    ability_desc_data = ability_desc_row.find('div', class_=data_selector)
                    if ability_desc_data:
                        # Get the text content, but clean up links
                        ability_text = ability_desc_data.get_text().strip()
                        if ability_text:
                            return ability_text
            
            # Fallback: Look for any other descriptive text in data cells, but exclude traits
            all_data = infobox.find_all('div', class_='druid-data')
            for data in all_data:
                text = data.get_text().strip()
                if (text and 
                    not text.startswith('http') and 
                    not text.lower() in ['secret rare', 'ultra rare', 'super rare', 'rare', 'uncommon', 'common'] and
                    not text in ['Dragon', 'Villain'] and  # Exclude trait values
                    not any(trait in text for trait in ['Dragon', 'Villain', 'Mage', 'Hero', 'Celestial'])):  # Exclude trait-like text
                    return text
        
        # Fallback to main content area
        main_content = soup.find('div', id='mw-content-text')
        if main_content:
            # Find paragraphs that might contain card effects
            paragraphs = main_content.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if text and not text.startswith('This page was last edited'):
                    return text
        
        return None
    
    def extract_card_type(self, soup):
        """Extract card type if available"""
        # Look for type information in druid-infobox
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            # Look for type/class information
            type_row = infobox.find('div', class_='druid-row-type')
            if type_row:
                type_data = type_row.find('div', class_='druid-data-type')
                if type_data:
                    return type_data.get_text().strip()
        
        return None
    
    def extract_card_rarity(self, soup):
        """Extract card rarity if available"""
        # Look for rarity information in druid-infobox
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            rarity_row = infobox.find('div', class_='druid-row-rarity')
            if rarity_row:
                rarity_data = rarity_row.find('div', class_='druid-data-rarity')
                if rarity_data:
                    # Get the text content, but clean up links
                    rarity_text = rarity_data.get_text().strip()
                    if rarity_text:
                        return rarity_text.lower()
        
        return None
    
    def extract_card_cost(self, soup):
        """Extract card cost if available"""
        # Look for cost information in content
        main_content = soup.find('div', id='mw-content-text')
        if main_content:
            text = main_content.get_text()
            # Look for cost patterns like "Cost: 3" or "3 cost"
            cost_match = re.search(r'cost[:\s]*(\d+)', text.lower())
            if cost_match:
                try:
                    return int(cost_match.group(1))
                except ValueError:
                    pass
        return None
    
    def extract_card_traits(self, soup):
        """Extract card traits if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            traits_row = infobox.find('div', class_='druid-row-traits')
            if traits_row:
                traits_data = traits_row.find('div', class_='druid-data-traits')
                if traits_data:
                    # Extract trait links
                    trait_links = traits_data.find_all('a')
                    if trait_links:
                        return [link.get_text().strip() for link in trait_links]
        return None
    
    def extract_card_ability_type(self, soup):
        """Extract card ability type if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            ability_type_row = infobox.find('div', class_='druid-row-ability_type')
            if ability_type_row:
                ability_type_data = ability_type_row.find('div', class_='druid-data-ability_type')
                if ability_type_data:
                    return ability_type_data.get_text().strip()
        return None
    
    def extract_card_attack(self, soup):
        """Extract card attack value if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            attack_row = infobox.find('div', class_='druid-row-attack')
            if attack_row:
                attack_data = attack_row.find('div', class_='druid-data-attack')
                if attack_data:
                    try:
                        return int(attack_data.get_text().strip())
                    except ValueError:
                        pass
        return None
    
    def extract_card_health(self, soup):
        """Extract card health value if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            health_row = infobox.find('div', class_='druid-row-health')
            if health_row:
                health_data = health_row.find('div', class_='druid-data-health')
                if health_data:
                    try:
                        return int(health_data.get_text().strip())
                    except ValueError:
                        pass
        return None
    
    def extract_card_deck_type(self, soup):
        """Extract card deck type if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            deck_type_row = infobox.find('div', class_='druid-row-deck_type')
            if deck_type_row:
                deck_type_data = deck_type_row.find('div', class_='druid-data-deck_type')
                if deck_type_data:
                    return deck_type_data.get_text().strip()
        return None
    
    def extract_card_images(self, soup):
        """Extract art and card images from the page"""
        images = []
        
        # Method 1: Look for Open Graph images (most reliable)
        og_images = soup.find_all('meta', property='og:image')
        # Only process the first Open Graph image (usually the best quality)
        if og_images:
            og_img = og_images[0]  # Take only the first one
            url = og_img.get('content')
            if url and url.startswith('http'):
                # For Open Graph images, convert thumbnails to original format
                if 'thumb' in url:
                    # Convert thumbnail to original format
                    # Remove /thumb/ and the size part, keep the base path
                    parts = url.split('/')
                    if 'thumb' in parts:
                        thumb_index = parts.index('thumb')
                        # Keep everything before 'thumb' (base path)
                        base_parts = parts[:thumb_index]
                        # The directories are the parts after 'thumb' but before the filename
                        # The filename is the part before the size variant
                        directories = parts[thumb_index + 1:thumb_index + 3]  # Get both directory parts (e.g., 'd', 'd5')
                        filename = parts[thumb_index + 3]  # This is the actual filename
                        size_variant = parts[thumb_index + 4]  # This is the size variant
                        
                        # Reconstruct the URL: base_parts + directories + filename
                        original_url = '/'.join(base_parts + directories) + '/' + filename
                        
                        # Add format=original parameter
                        if '?' in original_url:
                            original_url += '&format=original'
                        else:
                            original_url += '?format=original'
                    
                    images.append({
                        'url': original_url,
                        'type': 'art'
                    })
                else:
                    # Already an original image, add format=original if needed
                    if '?' in url:
                        url += '&format=original'
                    else:
                        url += '?format=original'
                    
                    images.append({
                        'url': url,
                        'type': 'art'
                    })
        
        # Method 2: Look for images in druid-infobox (most specific)
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            # Find the main images section
            main_images = infobox.find('div', class_='druid-main-images')
            if main_images:
                # Look for image files (not tabs)
                image_files = main_images.find_all('div', class_='druid-main-images-file')
                
                for img_file in image_files:
                    # Get the tab key to determine type
                    tab_key = img_file.get('data-druid-tab-key', 'unknown')
                    
                    # Find the img tag within this file div
                    img_tag = img_file.find('img', src=True)
                    if img_tag:
                        src = img_tag.get('src')
                        alt = img_tag.get('alt', '')
                        
                        if src and not src.startswith('http'):
                            src = urljoin(self.base_url, src)
                        
                        # Convert thumbnail to original format
                        if 'thumb' in src:
                            # Convert thumbnail to original format
                            parts = src.split('/')
                            if 'thumb' in parts:
                                thumb_index = parts.index('thumb')
                                # Keep everything before 'thumb' (base path)
                                base_parts = parts[:thumb_index]
                                # The directories are the parts after 'thumb' but before the filename
                                # The filename is the part before the size variant
                                directories = parts[thumb_index + 1:thumb_index + 3]  # Get both directory parts (e.g., 'd', 'd5')
                                filename = parts[thumb_index + 3]  # This is the actual filename
                                size_variant = parts[thumb_index + 4]  # This is the size variant
                                
                                # Reconstruct the URL: base_parts + directories + filename
                                original_url = '/'.join(base_parts + directories) + '/' + filename
                                # Add format=original parameter
                                if '?' in original_url:
                                    original_url += '&format=original'
                                else:
                                    original_url += '?format=original'
                        else:
                            original_url = src
                            # Add format=original parameter if not present
                            if '?' in original_url:
                                original_url += '&format=original'
                            else:
                                original_url += '?format=original'
                        
                        # Determine image type based on tab key
                        img_type = 'art' if tab_key == 'Art' else 'card' if tab_key == 'Card' else 'unknown'
                        
                        # Only add if it's a different image (not a duplicate)
                        is_duplicate = False
                        for existing_img in images:
                            # Check if this is essentially the same image (same filename, different cache params)
                            existing_filename = existing_img['url'].split('/')[-1].split('?')[0]
                            new_filename = original_url.split('/')[-1].split('?')[0]
                            if existing_filename == new_filename:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            images.append({
                                'url': original_url,
                                'type': img_type
                            })
        
        # Remove duplicates based on URL (final cleanup)
        unique_images = []
        seen_urls = set()
        for img in images:
            # Normalize URL by removing cache parameters for comparison
            normalized_url = img['url'].split('?')[0]
            if normalized_url not in seen_urls:
                unique_images.append(img)
                seen_urls.add(normalized_url)
        
        return unique_images
    
    def merge_image_data(self, new_images, old_images):
        """Merge new image data with old local image paths using URL as key"""
        if not old_images:
            return new_images
        
        # Create a mapping of old images by URL
        old_image_map = {}
        for old_img in old_images:
            if old_img.get('url'):
                old_image_map[old_img['url']] = old_img
        
        # Merge new images with old local paths, preserving original field order
        merged_images = []
        for new_img in new_images:
            if new_img.get('url') and new_img['url'] in old_image_map:
                # Use the old image structure to preserve field order
                old_img = old_image_map[new_img['url']]
                merged_img = old_img.copy()
                # Update only the fields that should change, preserving original order
                if 'type' in new_img:
                    merged_img['type'] = new_img['type']
                if 'url' in new_img:
                    merged_img['url'] = new_img['url']
            else:
                # For new images, create with consistent field order matching original files
                merged_img = {
                    'url': new_img.get('url', ''),
                    'type': new_img.get('type', 'unknown')
                }
            merged_images.append(merged_img)
        
        return merged_images

    def save_card_with_image_preservation(self, card, category_name, is_batch=False):
        """Save a single card to JSON file while preserving local image paths"""
        # Use absolute path to ensure files are saved to the correct location
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up one more level to project root
        output_dir = f"cards/{category_name.lower() if is_batch else category_name}"
        absolute_output_dir = os.path.join(project_root, output_dir)
        
        if not os.path.exists(absolute_output_dir):
            os.makedirs(absolute_output_dir)
        
        if card and card.get('name'):
            # Create filename from card name
            filename = card['name'].lower().replace(' ', '-').replace(':', '').replace('(', '').replace(')', '')
            filename = re.sub(r'[^a-z0-9\-]', '', filename)
            filename = os.path.join(absolute_output_dir, f"{filename}.json")
            
            # Try to read existing file to preserve local image paths
            old_image_data = None
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        old_data = json.load(f)
                        old_image_data = old_data.get('images', [])
                except (json.JSONDecodeError, IOError):
                    pass  # If file is corrupted or can't be read, ignore
            
            # Merge image data to preserve local paths
            if old_image_data:
                card['images'] = self.merge_image_data(card['images'], old_image_data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(card, f, indent=2, ensure_ascii=False)
            
            print_prefix = "  " if not is_batch else ""
            print(f"{print_prefix}Saved: {filename}")

    def save_cards_to_json(self, cards, category_name):
        """Save scraped cards to individual JSON files"""
        for card in cards:
            if card and card.get('name'):
                self.save_card_with_image_preservation(card, category_name, is_batch=True)
    
    def run(self, category_name, limit=10):
        """Main method to run the scraper for a single category"""
        print(f"Starting Working Once upon a Galaxy wiki scraper for {category_name}...")
        
        # Scrape the specified category
        cards = self.scrape_category(category_name, limit)
        
        print(f"\nScraped {len(cards)} cards")
        
        # Save cards to JSON files
        self.save_cards_to_json(cards, category_name)
        
        print("Scraping completed!")
    
    def save_single_card_to_json(self, card, category_name):
        """Save a single card to JSON file immediately"""
        self.save_card_with_image_preservation(card, category_name, is_batch=False)
    
    def run_all_categories(self):
        """Main method to run the scraper for all available categories"""
        print("Starting Working Once upon a Galaxy wiki scraper for all categories...")
        
        # Define available categories (only the ones that actually exist on the wiki)
        self.available_categories = ["Characters", "Treasures", "Spells"]
        
        for category in self.available_categories:
            try:
                print(f"\n{'='*50}")
                print(f"Processing category: {category}")
                print(f"{'='*50}")
                
                # Try to scrape this category (some might not exist yet)
                cards = self.scrape_category(category, limit=None)  # Unlimited
                
                if cards:
                    print(f"\nScraped {len(cards)} cards from {category}")
                    self.save_cards_to_json(cards, category)
                else:
                    print(f"No cards found for category: {category}")
                    
            except Exception as e:
                print(f"Error processing category {category}: {e}")
                continue
        
        print("\nAll categories processing completed!")
    
    def scrape_specific_cards(self, card_names, category_name):
        """Scrape specific cards by name from a category"""
        print(f"Scraping specific {category_name} cards: {', '.join(card_names)}")
        
        # First get the category page to find the card URLs
        category_url = f"{self.base_url}/wiki/Category:{category_name}"
        content = self.get_page_content(category_url)
        if not content:
            print(f"Could not access {category_name} category page")
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for the main content area
        main_content = soup.find('div', id='mw-content-text')
        if not main_content:
            print("Could not find main content area")
            return []
        
        # Find URLs for the specific cards
        card_urls = {}
        links = main_content.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            
            # Check if this link matches one of our target cards
            if (href.startswith('/wiki/') and 
                not href.startswith('/wiki/Template:') and
                not href.startswith('/wiki/Category:') and
                text in card_names):
                
                card_urls[text] = urljoin(self.base_url, href)
        
        print(f"Found URLs for {len(card_urls)} out of {len(card_names)} requested cards")
        
        # Scrape each found card
        cards = []
        for card_name, url in card_urls.items():
            card_data = self.scrape_card_page(url, card_name, category_name)
            if card_data:
                cards.append(card_data)
                print(f"Successfully scraped: {card_name}")
            else:
                print(f"Failed to scrape: {card_name}")
        
        return cards

    def extract_primary_ability_description(self, soup):
        """Extract primary ability description if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            # Look for primary ability description row names
            description_selectors = [
                'druid-row-ability_description'     # Primary ability description
            ]
            
            for selector in description_selectors:
                ability_desc_row = infobox.find('div', class_=selector)
                if ability_desc_row:
                    # Try to find the corresponding data div
                    data_selector = selector.replace('druid-row-', 'druid-data-')
                    ability_desc_data = ability_desc_row.find('div', class_=data_selector)
                    if ability_desc_data:
                        # Get the text content, but clean up links
                        ability_text = ability_desc_data.get_text().strip()
                        if ability_text:
                            return ability_text
        return None
    
    def extract_primary_ability_gold_description(self, soup):
        """Extract primary ability gold description if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            # Look for primary ability gold description row names
            gold_description_selectors = [
                'druid-row-ability_description_gold'     # Primary ability gold description
            ]
            
            for selector in gold_description_selectors:
                gold_desc_row = infobox.find('div', class_=selector)
                if gold_desc_row:
                    # Try to find the corresponding data div
                    data_selector = selector.replace('druid-row-', 'druid-data-')
                    gold_desc_data = gold_desc_row.find('div', class_=data_selector)
                    if gold_desc_data:
                        # Get the text content, but clean up links
                        gold_text = gold_desc_data.get_text().strip()
                        if gold_text:
                            return gold_text
        return None

    def extract_card_abilities(self, soup):
        """Extract all card abilities as a list"""
        abilities = []
        infobox = soup.find('div', class_='druid-infobox')
        if not infobox:
            return abilities
        
        # Look for primary ability
        primary_type = self.extract_card_ability_type(soup)
        primary_desc = self.extract_primary_ability_description(soup)
        primary_gold = self.extract_primary_ability_gold_description(soup)
        
        # Only add primary ability if it has meaningful content
        if primary_type or (primary_desc and primary_desc not in ['Dragon', 'Villain'] and len(primary_desc) > 0):
            abilities.append({
                "type": primary_type,
                "description": primary_desc,
                "gold_description": primary_gold
            })
        
        # Look for secondary ability
        secondary_type = self.extract_card_ability_2_type(soup)
        secondary_desc = self.extract_card_ability_2_description(soup)
        secondary_gold = self.extract_card_ability_2_gold_description(soup)
        
        if secondary_type or secondary_desc:
            abilities.append({
                "type": secondary_type,
                "description": secondary_desc,
                "gold_description": secondary_gold
            })
        
        # Look for tertiary ability (if exists)
        tertiary_type = self.extract_card_ability_3_type(soup)
        tertiary_desc = self.extract_card_ability_3_description(soup)
        tertiary_gold = self.extract_card_ability_3_gold_description(soup)
        
        if tertiary_type or tertiary_desc:
            abilities.append({
                "type": tertiary_type,
                "description": tertiary_desc,
                "gold_description": tertiary_gold
            })
        
        return abilities
    
    def extract_card_ability_2_type(self, soup):
        """Extract secondary ability type if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            ability_type_row = infobox.find('div', class_='druid-row-ability_2_type')
            if ability_type_row:
                ability_type_data = ability_type_row.find('div', class_='druid-data-ability_2_type')
                if ability_type_data:
                    return ability_type_data.get_text().strip()
        return None
    
    def extract_card_ability_2_description(self, soup):
        """Extract secondary ability description if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            ability_desc_row = infobox.find('div', class_='druid-row-ability_2_description')
            if ability_desc_row:
                ability_desc_data = ability_desc_row.find('div', class_='druid-data-ability_2_description')
                if ability_desc_data:
                    ability_text = ability_desc_data.get_text().strip()
                    if ability_text:
                        return ability_text
        return None
    
    def extract_card_ability_2_gold_description(self, soup):
        """Extract secondary ability gold description if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            # Try different possible gold description row names for secondary ability
            gold_description_selectors = [
                'druid-row-ability_2_description_gold',  # Zeus style
            ]
            
            for selector in gold_description_selectors:
                gold_desc_row = infobox.find('div', class_=selector)
                if gold_desc_row:
                    # Try to find the corresponding data div
                    data_selector = selector.replace('druid-row-', 'druid-data-')
                    gold_desc_data = gold_desc_row.find('div', class_=data_selector)
                    if gold_desc_data:
                        # Get the text content, but clean up links
                        gold_text = gold_desc_data.get_text().strip()
                        if gold_text:
                            return gold_text
        return None
    
    def extract_card_ability_3_type(self, soup):
        """Extract tertiary ability type if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            ability_type_row = infobox.find('div', class_='druid-row-ability_3_type')
            if ability_type_row:
                ability_type_data = ability_type_row.find('div', class_='druid-data-ability_3_type')
                if ability_type_data:
                    return ability_type_data.get_text().strip()
        return None
    
    def extract_card_ability_3_description(self, soup):
        """Extract tertiary ability description if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            ability_desc_row = infobox.find('div', class_='druid-row-ability_3_description')
            if ability_desc_row:
                ability_desc_data = ability_desc_row.find('div', class_='druid-data-ability_3_description')
                if ability_desc_data:
                    ability_text = ability_desc_data.get_text().strip()
                    if ability_text:
                        return ability_text
        return None
    
    def extract_card_ability_3_gold_description(self, soup):
        """Extract tertiary ability gold description if available"""
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            # Try different possible gold description row names for tertiary ability
            gold_description_selectors = [
                'druid-row-ability_3_description_gold',  # Zeus style
                'druid-row-ability_description_gold'     # Barrel of Monkeys style
            ]
            
            for selector in gold_description_selectors:
                gold_desc_row = infobox.find('div', class_=selector)
                if gold_desc_row:
                    # Try to find the corresponding data div
                    data_selector = selector.replace('druid-row-', 'druid-data-')
                    gold_desc_data = gold_desc_row.find('div', class_=data_selector)
                    if gold_desc_data:
                        # Get the text content, but clean up links
                        gold_text = gold_desc_data.get_text().strip()
                        if gold_text:
                            return gold_text
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape Once upon a Galaxy wiki cards')
    parser.add_argument('--categories', '-c', nargs='+', 
                       help='Categories to scrape (e.g., Characters Treasures Events). Default: all available categories')
    parser.add_argument('--limit', '-l', type=int, default=None,
                       help='Limit number of cards per category (default: unlimited)')
    parser.add_argument('--all', action='store_true',
                       help='Scrape all available categories with unlimited cards')
    parser.add_argument('--cards', '-n', nargs='+',
                       help='Specific card names to scrape (requires --categories)')
    
    args = parser.parse_args()
    
    scraper = CardScraper()
    
    if args.all:
        # Scrape all available categories with unlimited cards
        print("Scraping all available categories with unlimited cards...")
        scraper.run_all_categories()
    elif args.categories:
        if args.cards:
            # Scrape specific cards from specified categories
            for category in args.categories:
                print(f"\n{'='*50}")
                print(f"Scraping specific cards from {category}...")
                cards = scraper.scrape_specific_cards(args.cards, category)
                if cards:
                    scraper.save_cards_to_json(cards, category)
                    print(f"Scraped {len(cards)} specific cards from {category}")
                else:
                    print(f"No specific cards found in {category}")
        else:
            # Scrape specified categories with specified limit
            for category in args.categories:
                print(f"\n{'='*50}")
                scraper.run(category, args.limit)
    else:
        # Default: scrape Characters with 10 cards limit
        print("No categories specified. Using default: Characters with 10 card limit")
        scraper.run("Characters", 10)
