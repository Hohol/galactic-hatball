# Testing the Card Scraper

This directory contains all the tests for the Once upon a Galaxy card scraper.

## Directory Structure

```
tests/
├── test_card_scraper.py      # Unit tests for the scraper logic
├── test_html_display.py      # Data structure validation tests
├── run_tests.py              # Test runner script
├── test_requirements.txt     # Python dependencies for tests
└── TESTING.md                # This file
```

## Running Tests

### Option 1: Use the test runner (recommended)
```bash
cd tests
python3 run_tests.py
```

### Option 2: Use unittest directly
```bash
cd tests
python3 -m unittest test_card_scraper.TestCardScraper -v
```

### Option 3: Use pytest (if installed)
```bash
cd tests
pytest test_card_scraper.py -v
```

## Test Coverage

### Character-Specific Tests (10 tests)
- ✅ **Primary abilities**: Type only, type + description, type + description + gold
- ✅ **Secondary abilities**: Description only, description + gold  
- ✅ **Tertiary abilities**: Type + description
- ✅ **Character traits**: Multiple trait extraction
- ✅ **Character stats**: Attack and health values
- ✅ **Character deck types**: Deck type information
- ✅ **Edge cases**: No abilities, empty infobox, missing data

### Shared Functionality Tests (4 tests)
- ✅ **Rarity extraction**: Works for characters, treasures, and spells
- ✅ **Image extraction**: Basic image URL processing
- ✅ **Category handling**: Verifies scraper can handle different card types

### Data Structure Validation (1 test file)
- ✅ **Character JSON validation**: Ensures all character files have correct structure
- ✅ **Ability structure validation**: Verifies abilities array format and gold descriptions

## What This Prevents

1. **Breaking ability extraction** when modifying the scraper
2. **Corrupting the data structure** when changing JSON output
3. **Breaking rarity/image extraction** for any card type
4. **Accidentally removing required fields** from character data

## How to Use

- **Before committing scraper changes**: Run `cd tests && python3 run_tests.py`
- **Before deploying**: Run both test suites to ensure data integrity
- **When adding new features**: Add corresponding tests first

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running tests from the `tests/` directory:
```bash
cd tests
python3 run_tests.py
```

### Missing Dependencies
Install test dependencies:
```bash
pip3 install -r test_requirements.txt
```

### Test Failures
- Check that the scraper hasn't been modified in a way that breaks existing functionality
- Verify that the test data (mock HTML) matches the expected structure
- Run individual tests to isolate issues: `python3 -m unittest test_card_scraper.TestCardScraper.test_extract_card_abilities_primary_only -v`
