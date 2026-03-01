import gzip
import io
import requests
import xml.etree.ElementTree as ET

# These are the EXACT internal IDs from the epg_ripper_UK1.xml.gz file
TARGET_IDS = {
    'SkySp.Tennis.HD.uk',
    'SkySp.F1.HD.uk',
    'SkySp.Fball.uk',
    'SkySp.Mix.HD.uk',
    'SkySpCricket.HD.uk',
    'SkySp.Golf.uk',
    'SkySp.Golf.HD.uk',
    'SkySp.PL.HD.uk',
    'TNT.Sports.1.HD.uk',
    'TNT.Sports.2.HD.uk',
    'TNT.Sports.3.HD.uk',
    'TNT.Sports.4.HD.uk',
    'BBC.One.Lon.HD.uk',
    'BBC.Two.HD.uk',
    'ITV1.HD.uk',
    'Channel.4.HD.uk',
    'Channel.5.HD.uk'
}

url = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"

print(f"Filtering for {len(TARGET_IDS)} specific channels...")

try:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    
    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
        # We use iterparse for maximum speed and lowest memory footprint
        context = ET.iterparse(gz, events=('start', 'end'))
        
        # Initialize the new XML document
        new_root = ET.Element('tv', {'generator-info-name': 'Gemini-Exact-Filter'})
        
        for event, elem in context:
            if event == 'end':
                # Match <channel id="...">
                if elem.tag == 'channel':
                    if elem.get('id') in TARGET_IDS:
                        new_root.append(elem)
                    else:
                        elem.clear() # Wipe non-matches from memory
                
                # Match <programme channel="...">
                elif elem.tag == 'programme':
                    if elem.get('channel') in TARGET_IDS:
                        new_root.append(elem)
                    else:
                        elem.clear() # Wipe non-matches from memory
                
                # Cleanup other tags to keep RAM low
                if elem.tag not in ['channel', 'programme', 'tv']:
                    elem.clear()

        # Save the filtered results
        tree = ET.ElementTree(new_root)
        tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
        print(f"Successfully wrote epg.xml. Filtering complete.")

except Exception as e:
    print(f"An error occurred: {e}")
    exit(1)
