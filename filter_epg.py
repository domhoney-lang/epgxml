import gzip
import io
import requests
import xml.etree.ElementTree as ET

# We will look for these words inside the channel names
KEYWORDS = [
    'BBC One', 'BBC 1', 'BBC Two', 'BBC 2', 'ITV1', 'ITV 1', 
    'Channel 4', 'Channel 5', 'Sky Sports', 'TNT Sports'
]

url = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"

print(f"Downloading and filtering {url}...")
try:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    
    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
        context = ET.iterparse(gz, events=('start', 'end'))
        new_root = ET.Element('tv', {'generator-info-name': 'Gemini-Fuzzy-Filter'})
        
        target_ids = set()
        
        for event, elem in context:
            if event == 'end':
                # Phase 1: Identify Channels by Name
                if elem.tag == 'channel':
                    display_name = elem.findtext('display-name') or ""
                    # Check if any of our keywords are in the channel name
                    if any(key.lower() in display_name.lower() for key in KEYWORDS):
                        new_root.append(elem)
                        target_ids.add(elem.get('id'))
                    else:
                        elem.clear()
                
                # Phase 2: Grab Programs for those identified IDs
                elif elem.tag == 'programme':
                    if elem.get('channel') in target_ids:
                        new_root.append(elem)
                    else:
                        elem.clear()
                
                # Clean up memory
                if elem.tag not in ['channel', 'programme', 'tv']:
                    elem.clear()

        tree = ET.ElementTree(new_root)
        tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
        print(f"Success! Found {len(target_ids)} matching channels.")
        print(f"Channels found: {', '.join(list(target_ids)[:10])}...")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
