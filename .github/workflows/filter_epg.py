import gzip
import io
import requests
import xml.etree.ElementTree as ET

# List of Channel IDs you want to keep
ALLOWED_CHANNELS = {
    'BBC1.uk', 'BBC2.uk', 'ITV1.uk', 'Channel4.uk', 'Channel5.uk',
    'SkySportsMainEvent.uk', 'SkySportsPremierLeague.uk', 'SkySportsFootball.uk',
    'SkySportsCricket.uk', 'SkySportsGolf.uk', 'SkySportsF1.uk', 
    'SkySportsAction.uk', 'SkySportsArena.uk', 'SkySportsNews.uk', 'SkySportsMix.uk',
    'TNTSports1.uk', 'TNTSports2.uk', 'TNTSports3.uk', 'TNTSports4.uk', 'TNTSportsUltimate.uk'
}

url = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"

print("Downloading and filtering EPG...")
response = requests.get(url)
with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
    # Use iterparse to handle the large file without crashing memory
    context = ET.iterparse(gz, events=('start', 'end'))
    
    # Create the root of our new, smaller XML
    new_root = ET.Element('tv', {'generator-info-name': 'Custom-Filter'})
    
    for event, elem in context:
        if event == 'end':
            # Check for <channel> tags
            if elem.tag == 'channel':
                if elem.get('id') in ALLOWED_CHANNELS:
                    new_root.append(elem)
                else:
                    elem.clear() # Discard unwanted channels
            
            # Check for <programme> tags
            elif elem.tag == 'programme':
                if elem.get('channel') in ALLOWED_CHANNELS:
                    new_root.append(elem)
                else:
                    elem.clear() # Discard unwanted programs

    # Save the small file
    tree = ET.ElementTree(new_root)
    tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
    print("Filtered EPG saved to epg.xml")
