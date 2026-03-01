import gzip
import io
import requests
import xml.etree.ElementTree as ET

TARGET_IDS = {
    'SkySp.Tennis.HD.uk', 'SkySp.F1.HD.uk', 'SkySp.Fball.uk', 'SkySp.Mix.HD.uk',
    'SkySpCricket.HD.uk', 'SkySp.Golf.uk', 'SkySp.Golf.HD.uk', 'SkySp.PL.HD.uk',
    'TNT.Sports.1.HD.uk', 'TNT.Sports.2.HD.uk', 'TNT.Sports.3.HD.uk', 'TNT.Sports.4.HD.uk',
    'BBC.One.Lon.HD.uk', 'BBC.Two.HD.uk', 'ITV1.HD.uk', 'Channel.4.HD.uk', 'Channel.5.HD.uk'
}

url = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"

try:
    print(f"Downloading from {url}...")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    
    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
        # Load the whole file to ensure we don't miss anything in the stream
        tree = ET.parse(gz)
        root = tree.getroot()
        
        # New root for our filtered file
        new_root = ET.Element('tv', root.attrib)
        
        # 1. Pull the Channel Definitions
        chan_count = 0
        for channel in root.findall('channel'):
            if channel.get('id') in TARGET_IDS:
                new_root.append(channel)
                chan_count += 1
        print(f"Found {chan_count} out of {len(TARGET_IDS)} channel headers.")

        # 2. Pull the Programme Listings
        prog_counts = {cid: 0 for cid in TARGET_IDS}
        for programme in root.findall('programme'):
            channel_id = programme.get('channel')
            if channel_id in TARGET_IDS:
                new_root.append(programme)
                prog_counts[channel_id] = prog_counts.get(channel_id, 0) + 1
        
        # 3. Print a report to the logs so we can see what's happening
        total_progs = sum(prog_counts.values())
        print(f"Total programme listings added: {total_progs}")
        for cid, count in prog_counts.items():
            if count > 0:
                print(f" - {cid}: {count} programs")
            else:
                print(f" - {cid}: EMPTY (No programs found!)")

        # 4. Save
        new_tree = ET.ElementTree(new_root)
        new_tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
        print("File saved successfully.")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
