import gzip
import io
import requests
import xml.etree.ElementTree as ET

# Updated IDs to match epgshare01 UK1 source exactly
ALLOWED_CHANNELS = {
    'BBC1.uk', 'BBC2.uk', 'ITV1.uk', 'Channel4.uk', 'Channel5.uk',
    'SkySportsMainEvent.uk', 'SkySportsPremierLeague.uk', 'SkySportsFootball.uk',
    'SkySportsCricket.uk', 'SkySportsGolf.uk', 'SkySportsF1.uk', 
    'SkySportsAction.uk', 'SkySportsArena.uk', 'SkySportsNews.uk', 'SkySportsMix.uk',
    'TNTSports1.uk', 'TNTSports2.uk', 'TNTSports3.uk', 'TNTSports4.uk', 'TNTSportsUltimate.uk'
}

url = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"

print(f"Downloading {url}...")
try:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    
    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
        context = ET.iterparse(gz, events=('start', 'end'))
        new_root = ET.Element('tv', {'generator-info-name': 'Gemini-Filter'})
        
        found_channels = set()
        
        for event, elem in context:
            if event == 'end':
                if elem.tag == 'channel':
                    cid = elem.get('id')
                    if cid in ALLOWED_CHANNELS:
                        new_root.append(elem)
                        found_channels.add(cid)
                    else:
                        elem.clear()
                
                elif elem.tag == 'programme':
                    if elem.get('channel') in ALLOWED_CHANNELS:
                        new_root.append(elem)
                    else:
                        elem.clear()
                
                # Free memory
                if elem.tag not in ['channel', 'programme', 'tv']:
                    elem.clear()

        tree = ET.ElementTree(new_root)
        tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
        print(f"Success! Filtered {len(found_channels)} channels into epg.xml")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
