# Once upon a Galaxy Wiki Scraper

This folder contains web scraping tools to extract card data from the Once upon a Galaxy wiki.

## Files

### **`full_scraper.py`** - Main Production Scraper
- **Purpose**: Scrapes ALL treasure cards from the wiki (118 total)
- **Usage**: `python3 full_scraper.py`
- **Time**: 6-8 minutes (with respectful 3-second delays)
- **Output**: Individual JSON files + combined `all_treasures.json`

### **`working_scraper.py`** - Test Scraper (Limited)
- **Purpose**: Test scraper that gets first 10 cards
- **Usage**: `python3 working_scraper.py`
- **Time**: ~1 minute
- **Output**: Individual JSON files for testing

### **`test_scraper.py`** - Connection Testing
- **Purpose**: Tests different approaches to access the wiki
- **Usage**: `python3 test_scraper.py`
- **Output**: Connection status and page accessibility info

### **`scraper.py`** - Original Scraper (Deprecated)
- **Purpose**: Original version with CORS issues
- **Status**: Replaced by working_scraper.py

### **`requirements.txt`** - Python Dependencies
- **Install**: `pip3 install -r requirements.txt`
- **Dependencies**: requests, beautifulsoup4, lxml

## How to Use

1. **Install dependencies**:
   ```bash
   cd scraper
   pip3 install -r requirements.txt
   ```

2. **Test the connection**:
   ```bash
   python3 test_scraper.py
   ```

3. **Run limited test** (recommended first):
   ```bash
   python3 working_scraper.py
   ```

4. **Run full scraping** (when ready):
   ```bash
   python3 full_scraper.py
   ```

## Output

- **Individual card files**: `cards/treasures/card-name.json`
- **Combined file**: `cards/treasures/all_treasures.json`
- **Debug files**: HTML dumps for troubleshooting

## Notes

- Uses `curl/7.68.0` user agent to bypass anti-bot measures
- Includes 3-second delays between requests to be respectful
- Filters out MediaWiki templates and infrastructure files
- Only scrapes actual game cards
