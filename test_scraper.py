#!/usr/bin/env python3
"""
Test script to try different approaches for accessing the Once upon a Galaxy wiki
"""

import requests
from bs4 import BeautifulSoup
import json

def test_different_approaches():
    """Test different user agents and approaches"""
    
    urls_to_test = [
        "https://onceuponagalaxy.wiki.gg/wiki/Category:Treasures",
        "https://onceuponagalaxy.wiki.gg/wiki/Special:AllPages",
        "https://onceuponagalaxy.wiki.gg/wiki/Main_Page"
    ]
    
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'curl/7.68.0'
    ]
    
    for url in urls_to_test:
        print(f"\n=== Testing URL: {url} ===")
        
        for user_agent in user_agents:
            print(f"\nTrying User-Agent: {user_agent[:50]}...")
            
            try:
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    print("SUCCESS! Page accessible")
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try to find the title
                    title = soup.find('title')
                    if title:
                        print(f"Page Title: {title.get_text()}")
                    
                    # Look for any links
                    links = soup.find_all('a', href=True)[:5]
                    print(f"First 5 links found:")
                    for link in links:
                        print(f"  - {link.get_text()[:50]} -> {link.get('href')}")
                    
                    break  # Success with this user agent
                    
                else:
                    print(f"Failed with status: {response.status_code}")
                    
            except Exception as e:
                print(f"Error: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_different_approaches()
