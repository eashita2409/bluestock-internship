import sys
from pathlib import Path
import json
import requests
import pandas as pd

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.utils import get_data_dir

def fetch_live_nav():
    raw_dir = get_data_dir("raw")
    
    # The 5 specific scheme codes requested:
    scheme_codes = [125497, 119551, 120503, 118632, 119092]
    
    summary_data = []
    
    print("STARTING LIVE NAV FETCH FROM mfapi.in...")
    print(f"Targeting scheme codes: {scheme_codes}\n")
    
    for code in scheme_codes:
        url = f"https://api.mfapi.in/mf/{code}"
        print(f"Fetching NAV data for scheme {code} from {url}...")
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status() # Raise error for bad response status (e.g. 404, 500)
            
            # Parse response as JSON
            data_json = response.json()
            
            # 1. Save the raw JSON data to data/raw/live_nav_{code}.json
            output_json_path = raw_dir / f"live_nav_{code}.json"
            with open(output_json_path, "w", encoding="utf-8") as jf:
                json.dump(data_json, jf, indent=2)
            print(f" -> Saved raw JSON to: {output_json_path.name}")
            
            # 2. Extract latest NAV details
            meta = data_json.get("meta", {})
            nav_history = data_json.get("data", [])
            
            scheme_name = meta.get("scheme_name", "Unknown Scheme")
            
            if nav_history:
                # The first item in the 'data' array is the latest NAV entry
                latest_entry = nav_history[0]
                latest_date = latest_entry.get("date", "N/A")
                latest_nav = latest_entry.get("nav", "N/A")
                
                print(f" -> Scheme Name: {scheme_name}")
                print(f" -> Latest Date: {latest_date} | Latest NAV: {latest_nav}")
                
                summary_data.append({
                    "amfi_code": code,
                    "scheme_name": scheme_name,
                    "date": latest_date,
                    "nav": latest_nav
                })
            else:
                print(f" -> Warning: No NAV history found in API response for scheme {code}.")
                summary_data.append({
                    "amfi_code": code,
                    "scheme_name": scheme_name,
                    "date": "N/A",
                    "nav": "N/A"
                })
                
        except requests.exceptions.RequestException as req_err:
            print(f" -> API Connection Error for scheme {code}: {req_err}")
            summary_data.append({
                "amfi_code": code,
                "scheme_name": "API Connection Error",
                "date": "N/A",
                "nav": "N/A"
            })
        except json.JSONDecodeError as json_err:
            print(f" -> JSON Decoding Error for scheme {code}: {json_err}")
            summary_data.append({
                "amfi_code": code,
                "scheme_name": "API JSON Parse Error",
                "date": "N/A",
                "nav": "N/A"
            })
        except Exception as e:
            print(f" -> Unexpected error fetching scheme {code}: {e}")
            summary_data.append({
                "amfi_code": code,
                "scheme_name": f"Error: {str(e)}",
                "date": "N/A",
                "nav": "N/A"
            })
        print("-" * 60)
        
    # Save the consolidated summary table to data/raw/live_nav_summary.csv
    summary_df = pd.DataFrame(summary_data)
    summary_csv_path = raw_dir / "live_nav_summary.csv"
    summary_df.to_csv(summary_csv_path, index=False)
    
    print("\n" + "="*80)
    print(f"CONSOLIDATED LIVE NAV SUMMARY SAVED TO: {summary_csv_path.name}")
    print("="*80)
    print(summary_df.to_string(index=False))
    print("="*80 + "\n")

if __name__ == "__main__":
    fetch_live_nav()
