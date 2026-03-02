import requests
import os

# Your Dropbox Direct Link
URL = "https://www.dropbox.com/scl/fi/08m4uosb7gsp8meebhrcs/m3u4u-193909-700434-EPG.xml?rlkey=dc6wms3jt7lr57fkz7a7xkz1f&st=mutowiyn&dl=1"
FILENAME = "epg.xml"

def sync():
    print(f"Downloading {FILENAME} from Dropbox...")
    try:
        response = requests.get(URL, timeout=60)
        response.raise_for_status()
        
        # Write the content to the local epg.xml file
        with open(FILENAME, "wb") as f:
            f.write(response.content)
            
        print(f"Successfully downloaded. File size: {len(response.content) / 1024:.2f} KB")
        
    except Exception as e:
        print(f"Error syncing file: {e}")
        exit(1)

if __name__ == "__main__":
    sync()
