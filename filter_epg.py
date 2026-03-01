import gzip
import io
import requests
import xml.etree.ElementTree as ET

# Your exact list of IDs
TARGET_IDS = {
    'SkySp.Tennis.HD.uk', 'SkySp.F1.HD.uk', 'SkySp.Fball.uk', 'SkySp.Mix.HD.uk',
    'SkySpCricket.HD.uk', 'SkySp.Golf.uk', 'SkySp.Golf.HD.uk', 'SkySp.PL.HD.uk',
    'TNT.Sports.1.HD.uk', 'TNT.Sports.2.HD.uk', 'TNT.Sports.3.HD.uk', 'TNT.Sports.4.HD.uk',
    'BBC.One.Lon.HD.uk', 'BBC.Two.HD.uk', 'ITV1.HD.uk', 'Channel.4.HD.uk', 'Channel.5.HD.uk'
}

url = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"

try:
    print("Fetching data...")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    
    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
        # We use iterparse for memory efficiency
        context = ET.iterparse(gz, events=('start', 'end'))
        new_root = ET.Element('tv', {'generator-info-name': 'Gemini-Final-Filter'})
        
        for event, elem in context:
            if event == 'end':
                # Check BOTH channels and programmes
                if elem.tag == 'channel' and elem.get('id') in TARGET_IDS:
                    new_root.append(elem)
                elif elem.tag == 'programme' and elem.get('channel') in TARGET_IDS:
                    # This captures the <title> and everything inside the programme
                    new_root.append(elem)
                
                # Clear memory for elements we don't need
                if elem.tag not in ['channel', 'programme', 'tv']:
                    elem.clear()

        # Save to file
        tree = ET.ElementTree(new_root)
        tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
        print("Filtering complete. File saved as epg.xml")

except Exception as e:
    print(f"Error: {e}")
