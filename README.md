# Path of Exile 2 OBS Rank Display

**This product isn't affiliated with or endorsed by Grinding Gear Games in any way.**

A Python utility for tracking and displaying character ranks from Path of Exile 2 leaderboards in OBS Studio.

## Features

- Tracks character rank and level from official Path of Exile 2 API
- Case-sensitive character name matching
- Supports all league types (Standard, Hardcore, SSF, HC SSF) 
- Supports both permanent leagues and Dawn of the Hunt event
- Configurable update interval
- Creates a text file that can be displayed in OBS

## Important Note About API Access

This tool uses the official Path of Exile API which requires OAuth authentication:

- You need to register an application by emailing oauth@grindinggear.com
- You need `service:leagues` and `service:leagues:ladder` scopes
- Only confidential clients with client credentials grant can access these endpoints
- You must provide your client_id and client_secret when running the tool

For more information, see the [official API documentation](https://www.pathofexile.com/developer/docs).

## Installation

1. Make sure you have Python 3.7+ installed on your system
2. Clone this repository:
   ```
   git clone https://github.com/yourusername/Path-of-Exile-2-OBS_RankDisplay.git
   cd Path-of-Exile-2-OBS_RankDisplay
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Register your application with Grinding Gear Games:
   - Email oauth@grindinggear.com requesting access
   - Include your PoE account name, application name, and required scopes
   - Specify that you need a confidential client with client_credentials grant
   - Mention that you need the `service:leagues` and `service:leagues:ladder` scopes

## Usage

Run the script with your character name and OAuth credentials:

```
python main.py CHARACTER_NAME --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET [options]
```

### Command-line Arguments

- `CHARACTER_NAME`: Your Path of Exile 2 character name (case-sensitive)
- `--client-id`: Your OAuth client ID (required)
- `--client-secret`: Your OAuth client secret (required)
- `--gamemode`: Game mode to check (choices: standard, hc, ssf, hcssf; default: standard)
- `--doth`: Use "Dawn of the Hunt" league instead of permanent leagues
- `--update`: Update interval in milliseconds (default: 60000 = 1 minute)
- `--output`: Output file path (default: poe2_rank.txt)
- `--debug`: Enable debug logging for troubleshooting

### Examples

Track character "WibaBONK" in Dawn of the Hunt HC SSF league, updating every minute:
```
python main.py WibaBONK --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --gamemode=hcssf --doth --update=60000
```

Track character "WibaBONK" in the standard Dawn of the Hunt league:
```
python main.py WibaBONK --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --doth
```

Track character "WibaBONK" in Hardcore SSF permanent league:
```
python main.py WibaBONK --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --gamemode=hcssf
```

Troubleshooting with debug mode:
```
python main.py WibaBONK --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --gamemode=hcssf --doth --debug
```

## API Rate Limiting

This tool respects the API rate limits as specified in the Path of Exile developer documentation. If you encounter rate limiting errors, the tool will log a warning and continue retrying at the specified interval.

To avoid rate limiting, consider:
- Increasing the update interval (--update parameter)
- Only running one instance of the tool at a time
- Limiting debug mode usage which may make additional API calls

## Displaying in OBS

1. Launch OBS Studio
2. Add a "Text (GDI+)" source to your scene
3. Check "Read from file" and select the output file (default: poe2_rank.txt)
4. Configure the text appearance (font, color, size, etc.) as desired
5. Optional: Add a background or other elements to improve visibility

The text will automatically update based on your configured update interval.

## Troubleshooting

- If your character isn't found, double-check the spelling and case of the name
- Make sure you're using the correct league/gamemode options
- Check the console output for any error messages
- Verify that the character appears on the official leaderboard
- If debug mode is enabled, check the ladder_debug.json file to see the raw API response
- If you see rate limit errors, increase your update interval
- If you get authorization errors, make sure your client_id and client_secret are correct and have the proper scopes

## OAuth Application Registration

To use the Path of Exile API, you need to register a confidential client:

1. Send an email to oauth@grindinggear.com with:
   - Your PoE account name
   - Your application's name
   - Client type: confidential
   - Grant type: client_credentials
   - Required scopes: `service:leagues` and `service:leagues:ladder`
   - A brief explanation of your application's purpose

2. Wait for GGG to respond with your client credentials
3. Use the provided client_id and client_secret with this tool

See the [Authorization documentation](https://www.pathofexile.com/developer/docs/authorization) for more details.

## License

See the [LICENSE](LICENSE.md) file for details.

# Acknowledgments

Special thanks to [Wiba](https://twitch.tv/wiba) for the idea.
