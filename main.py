import argparse
import time
import os
import sys
import logging
import json
import requests
from urllib.parse import quote

# Set up logging - will configure fully in main()
logger = logging.getLogger(__name__)

def configure_logging(debug=False):
    """Configure logging based on debug flag."""
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Path of Exile 2 Ladder Rank Tracker')
    parser.add_argument('character_name', help='Character name to search for (case-sensitive)')
    parser.add_argument('--gamemode', choices=['standard', 'hc', 'ssf', 'hcssf'], default='standard',
                        help='Game mode to check (default: standard)')
    parser.add_argument('--doth', action='store_true', 
                        help='Use Dawn of the Hunt league instead of permanent leagues')
    parser.add_argument('--update', type=int, default=60000,
                        help='Update interval in milliseconds (default: 60000)')
    parser.add_argument('--output', default='poe2_rank.txt',
                        help='Output file path (default: poe2_rank.txt)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging for troubleshooting')
    parser.add_argument('--client-id', 
                        help='OAuth client ID for PoE API (required for API access)')
    parser.add_argument('--client-secret', 
                        help='OAuth client secret for PoE API (required for API access)')
    
    return parser.parse_args()

def get_oauth_token(client_id, client_secret):
    """Get an OAuth access token using client credentials flow."""
    if not client_id or not client_secret:
        logger.error("OAuth client_id and client_secret are required for API access")
        return None
    
    token_url = "https://www.pathofexile.com/oauth/token"
    
    # Set required headers and parameters for the token request
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'OAuth PoE2-Ladder-Rank-Tracker/1.0.0 (contact: your-email@example.com)'
    }
    
    # Parameters for client credentials grant
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': 'service:leagues service:leagues:ladder'
    }
    
    try:
        logger.debug("Requesting OAuth token...")
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to get OAuth token. Status code: {response.status_code}")
            logger.debug(f"Response content: {response.text}")
            return None
        
        token_data = response.json()
        logger.debug("Successfully obtained OAuth token")
        
        return token_data.get('access_token')
        
    except Exception as e:
        logger.error(f"Error requesting OAuth token: {e}")
        if logger.getEffectiveLevel() == logging.DEBUG:
            import traceback
            traceback.print_exc()
        return None

def get_league_name(gamemode, use_doth):
    """Get the appropriate league name based on game mode and league option."""
    if use_doth:
        # Dawn of the Hunt leagues
        if gamemode == 'standard':
            return "Dawn of the Hunt"
        elif gamemode == 'hc':
            return "HC Dawn of the Hunt"
        elif gamemode == 'ssf':
            return "SSF Dawn of the Hunt"
        elif gamemode == 'hcssf':
            return "HC SSF Dawn of the Hunt"
    else:
        # Permanent leagues
        if gamemode == 'standard':
            return "Standard"
        elif gamemode == 'hc':
            return "Hardcore"
        elif gamemode == 'ssf':
            return "Solo Self-Found"
        elif gamemode == 'hcssf':
            return "Hardcore SSF"
    
    return "Unknown"

def get_character_rank(league_name, character_name, access_token):
    """Fetch character rank data from the official Path of Exile API."""
    logger.info(f"Checking ladder for league: {league_name}")
    
    if not access_token:
        logger.error("No OAuth token available. Cannot access API.")
        return None
    
    # According to API docs, use the proper API endpoint and version
    base_url = "https://api.pathofexile.com"
    
    # Set User-Agent according to API guidelines and include the bearer token
    headers = {
        'User-Agent': 'OAuth PoE2-Ladder-Rank-Tracker/1.0.0 (contact: your-email@example.com)',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        # First, get the list of active leagues to validate our league exists
        leagues_url = f"{base_url}/league?realm=poe2"
        logger.debug(f"Fetching leagues from: {leagues_url}")
        
        try:
            # Fetch the leagues for PoE2
            leagues_response = requests.get(leagues_url, headers=headers)
            
            if leagues_response.status_code != 200:
                logger.error(f"Failed to fetch leagues. Status code: {leagues_response.status_code}")
                logger.debug(f"Response content: {leagues_response.text[:500]}...")
                return None
            
            leagues_data = leagues_response.json()
            
            # Check if the league exists
            league_id = None
            leagues_list = leagues_data.get('leagues', [])
            
            for league in leagues_list:
                if league.get('name') == league_name:
                    league_id = league.get('id')
                    break
            
            if not league_id:
                logger.error(f"League '{league_name}' not found in active leagues")
                return None
            
        except Exception as e:
            logger.error(f"Error fetching leagues: {e}")
            # Continue with the assumption that the league exists
            # Use the name as the ID as a fallback
            league_id = league_name
        
        # Encode the league name for URL
        encoded_league = quote(league_id)
        
        # Get the ladder for the league - according to docs, this is the correct endpoint
        ladder_url = f"{base_url}/league/{encoded_league}/ladder?realm=poe2&limit=200"
        logger.debug(f"Fetching ladder from: {ladder_url}")
        
        response = requests.get(ladder_url, headers=headers)
        
        # Check for rate limiting headers
        if 'X-Rate-Limit-Client-State' in response.headers:
            logger.debug(f"Rate limit state: {response.headers['X-Rate-Limit-Client-State']}")
        
        if response.status_code == 429:  # Too Many Requests
            retry_after = response.headers.get('Retry-After', '60')
            logger.warning(f"Rate limited. Retry after {retry_after} seconds")
            return None
        
        if response.status_code != 200:
            logger.error(f"API request failed. Status code: {response.status_code}")
            logger.debug(f"Response content: {response.text[:500]}...")
            
            # If we're getting 404, the league might not exist
            if response.status_code == 404:
                logger.error(f"League '{league_name}' not found")
            
            return None
        
        try:
            ladder_data = response.json()
            
            # Debug: write full ladder data to file if in debug mode
            if logger.getEffectiveLevel() == logging.DEBUG:
                with open('ladder_debug.json', 'w', encoding='utf-8') as f:
                    json.dump(ladder_data, f, indent=2)
                logger.debug("Saved full JSON to ladder_debug.json for analysis")
            
            # Extract entries from the ladder based on API structure
            # According to docs, the path should be ladder.entries
            ladder_obj = ladder_data.get('ladder', {})
            entries = ladder_obj.get('entries', [])
            
            if not entries:
                logger.warning("No entries found in ladder response")
                return None
            
            # Search for the character in ladder entries
            for entry in entries:
                # The character info structure based on API docs
                character = entry.get('character', {})
                entry_name = character.get('name', '')
                
                if entry_name == character_name:
                    # Extract character data
                    level = character.get('level', 'Unknown')
                    rank = entry.get('rank', 'Unknown')
                    
                    # Check for dead or retired status
                    status = None
                    if character.get('dead', False):
                        status = "DEAD"
                    elif character.get('retired', False):
                        status = "RETIRED"
                    
                    character_data = {
                        'level': level,
                        'rank': rank,
                        'status': status
                    }
                    
                    logger.info(f"Found character {character_name} at rank {rank}, level {level}, status: {status}")
                    return character_data
            
            # If we've checked all entries and didn't find the character
            logger.warning(f"Character [{character_name}] not found in ladder entries")
            
            # If the API supports pagination, we could implement that here
            # This would depend on the structure of the API response
            
            return None
            
        except ValueError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error processing API request: {e}")
        if logger.getEffectiveLevel() == logging.DEBUG:
            import traceback
            traceback.print_exc()
        return None

def write_output(output_file, character_data, ladder_name):
    """Write character data to output file."""
    try:
        if character_data:
            # Format the output differently if the character has a status
            if character_data.get('status'):
                content = f"Level: {character_data['level']} | Rank: [{character_data['status']}] {character_data['rank']} | {ladder_name}"
            else:
                content = f"Level: {character_data['level']} | Rank: {character_data['rank']} | {ladder_name}"
                
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Updated rank information: {content}")
        else:
            # Write empty file if character not found
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("")
            logger.info("Wrote empty file (character not found)")
    except Exception as e:
        logger.error(f"Error writing output file: {e}")

def main():
    """Main function to run the ladder tracker."""
    # Print the disclaimer
    print("This product isn't affiliated with or endorsed by Grinding Gear Games in any way.")
    
    args = parse_arguments()
    
    # Configure logging based on debug flag
    configure_logging(args.debug)
    
    character_name = args.character_name
    gamemode = args.gamemode
    use_doth = args.doth
    update_interval_ms = args.update
    output_file = args.output
    client_id = args.client_id
    client_secret = args.client_secret
    
    # Get OAuth token
    access_token = get_oauth_token(client_id, client_secret)
    
    # If we can't get a token, exit
    if not access_token:
        logger.error("Could not obtain OAuth token. Make sure you have registered your application.")
        logger.error("Visit https://www.pathofexile.com/developer/docs/authorization for more information.")
        logger.error("Run with --client-id and --client-secret parameters.")
        return
    
    # Convert milliseconds to seconds for sleep
    update_interval_sec = update_interval_ms / 1000
    
    league_name = get_league_name(gamemode, use_doth)
    
    logger.info(f"Starting PoE2 Ladder Tracker for character: {character_name}")
    logger.info(f"Game mode: {gamemode}, League: {league_name}")
    logger.info(f"Update interval: {update_interval_ms}ms, Output file: {output_file}")
    
    try:
        while True:
            character_data = get_character_rank(league_name, character_name, access_token)
            write_output(output_file, character_data, league_name)
            
            logger.info(f"Waiting {update_interval_sec} seconds until next update...")
            time.sleep(update_interval_sec)
    except KeyboardInterrupt:
        logger.info("Tracker stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 