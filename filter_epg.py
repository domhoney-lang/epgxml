import gzip
import io
import requests
import xml.etree.ElementTree as ET

# Verified IDs for epgshare01 UK1 source
TARGET_IDS = {
    # Sports - Exact Matches
    'SkySp.Tennis.HD.uk', 'SkySp.F1.HD.uk', 'SkySp.Fball.uk', 'SkySp.Mix.HD.uk',
    'SkySpCricket.HD.uk', 'SkySp.Golf.uk', 'SkySp.Golf.HD.uk', 'SkySp.PL.HD.uk',
    'SkySp+HD.uk', 'SkySpMainEvHD.uk',
    'TNT.Sports.1.HD.uk', 'TNT.Sports.2.HD.uk', 'TNT.Sports.3.HD.uk', 'TNT.Sports.4.HD.uk',
    
    # Main Channels - Exact Matches
    'BBC.One.Lon.HD.uk', 'BBC.Two.HD.uk', 'ITV1.HD.uk',
    'Channel.4.HD.uk', 'Channel.5.HD.uk',
    
    # ITV Variations - common source IDs for UK1
    'ITV2.uk', 'ITV3.uk', 'ITV4.uk',
    # Adding HD versions just in case source updated recently
    'ITV2.HD.uk', 'ITV3.HD.uk', 'ITV4.HD.uk' 
}

url = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"

try:
    print(f"Downloading from {url}...")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    
    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
        tree = ET.parse(gz)
        root = tree.getroot()
        
        new_root = ET.Element('tv', root.attrib)
        
        # 1. Pull Channel Headers
        chan_count = 0
        found_ids = set()
        for channel in root.findall('channel'):
            cid = channel.get('id')
            if cid in TARGET_IDS:
                new_root.append(channel)
                found_ids.add(cid)
                chan_count += 1
        
        print(f"Match: Found {chan_count} out of {len(TARGET_IDS)} requested IDs.")

        # 2. Pull Listings
        prog_count = 0
        for programme in root.findall('programme'):
            if programme.get('channel') in found_ids:
                new_root.append(programme)
                prog_count += 1
        
        print(f"Success: Added {prog_count} programme entries.")

        # 3. Save
        new_tree = ET.ElementTree(new_root)
        new_tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
        print("Update complete. epg.xml is ready.")

except Exception as e:
    print(f"Critical Error: {e}")
    exit(1)
