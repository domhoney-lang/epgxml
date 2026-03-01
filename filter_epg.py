import gzip
import io
import requests
import xml.etree.ElementTree as ET

# Broader keywords to ensure we catch everything
KEYWORDS = [
    'BBC', 'ITV', 'Channel 4', 'Channel 5', 'Sky', 'TNT'
]

url = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"

print(f"Starting Download and Filter...")
try:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    
    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
        # Load the full XML into memory (GitHub Runners have 7GB RAM, plenty for this)
        tree = ET.parse(gz)
        root = tree.getroot()
        
        # Start a new XML structure
        new_root = ET.Element('tv', root.attrib)
        target_ids = set()

        # 1. SCAN CHANNELS
        for channel in root.findall('channel'):
            channel_id = str(channel.get('id', '')).lower()
            # Get all display names (sometimes there are multiple)
            display_names = [dn.text.lower() for dn in channel.findall('display-name') if dn.text]
            
            # Check if any keyword matches the ID or any Display Name
            match_found = False
            for key in KEYWORDS:
                k = key.lower()
                if k in channel_id or any(k in name for name in display_names):
                    match_found = True
                    break
            
            if match_found:
                new_root.append(channel)
                target_ids.add(channel.get('id'))

        print(f"Match phase complete. Found {len(target_ids)} channels.")

        # 2. FILTER PROGRAMMES
        # We only keep programs if their 'channel' attribute is in our target_ids list
        programme_count = 0
        for prog in root.findall('programme'):
            if prog.get('channel') in target_ids:
                new_root.append(prog)
                programme_count += 1
        
        print(f"Programme phase complete. Added {programme_count} listings.")

        # 3. SAVE THE FILTERED FILE
        new_tree = ET.ElementTree(new_root)
        new_tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
        
        print(f"SUCCESS: epg.xml created with {len(target_ids)} channels.")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    exit(1)
