# Card Data Structure

This directory contains JSON files for each card in the "Once upon a Galaxy" game.

## File Naming Convention
- Use lowercase letters, numbers, and hyphens only
- No spaces or special characters
- Example: `galactic-explorer.json`, `star-destroyer.json`

## JSON Structure
Each card should follow this format:

```json
{
  "name": "Card Name",
  "description": "Card description text"
}
```

## Required Fields
- `name`: Display name of the card
- `description`: Main card text

## Adding New Cards
1. Create a new JSON file in this directory
2. Follow the structure above
3. Use a descriptive filename
4. Ensure the `id` field is unique across all cards
