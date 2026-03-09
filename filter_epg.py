import gzip
import io
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from html import unescape
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

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
AMAZON_PRIME_CHANNEL_ID = "Amazon.Prime.Video.uk"
AMAZON_PRIME_CHANNEL_NAME = "Amazon Prime Video"
AMAZON_PRIME_SCHEDULE_URL = "https://www.live-footballontv.com/live-football-on-amazon.html"
AMAZON_PRIME_LOGO = (
    "https://assets.aboutamazon.com/8a/37/cb335bec4ddc8756f920138c2be2/"
    "prime-logo-rgb-prime-blue-master.png"
)
LONDON_TZ = ZoneInfo("Europe/London")


def clean_text(value):
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def parse_fixture_date(date_text):
    normalized = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", clean_text(date_text))
    return datetime.strptime(normalized, "%A %d %B %Y")


def build_xmltv_timestamp(date_obj):
    return date_obj.strftime("%Y%m%d%H%M%S %z")


def fetch_amazon_prime_matches():
    response = requests.get(
        AMAZON_PRIME_SCHEDULE_URL,
        headers={"User-Agent": "Mozilla/5.0 tvsports-hub-epg-updater/1.0"},
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    matches = []
    now_london = datetime.now(LONDON_TZ)
    cutoff = now_london - timedelta(days=1)

    for group in soup.select("div.fixture-group"):
        date_node = group.select_one("div.fixture-date")
        if not date_node:
            continue

        try:
            fixture_day = parse_fixture_date(date_node.get_text(" ", strip=True))
        except ValueError:
            continue

        for fixture in group.select("div.fixture"):
            competition = clean_text(
                fixture.select_one("div.fixture__competition").get_text(" ", strip=True)
                if fixture.select_one("div.fixture__competition")
                else ""
            )
            channel = clean_text(
                fixture.select_one("div.fixture__channel").get_text(" ", strip=True)
                if fixture.select_one("div.fixture__channel")
                else ""
            )
            teams = clean_text(
                fixture.select_one("div.fixture__teams").get_text(" ", strip=True)
                if fixture.select_one("div.fixture__teams")
                else ""
            )
            kick_off = clean_text(
                fixture.select_one("div.fixture__time").get_text(" ", strip=True)
                if fixture.select_one("div.fixture__time")
                else ""
            )

            if "Amazon Prime Video" not in channel:
                continue
            if "UEFA Champions League" not in competition:
                continue
            if " v " not in teams or not kick_off:
                continue

            try:
                start_local = datetime.strptime(
                    f"{fixture_day.strftime('%Y-%m-%d')} {kick_off}", "%Y-%m-%d %H:%M"
                ).replace(tzinfo=LONDON_TZ)
            except ValueError:
                continue

            if start_local < cutoff:
                continue

            stage = competition.replace("UEFA Champions League", "").strip()
            desc = (
                f"Live UEFA Champions League coverage on Amazon Prime Video as {teams} "
                f"meet in the {stage or 'Tuesday night top-pick match'}."
            )

            matches.append(
                {
                    "title": f"Live: {teams}",
                    "sub_title": competition,
                    "desc": desc,
                    "start": start_local,
                    "stop": start_local + timedelta(hours=2, minutes=45),
                }
            )

    deduped = []
    seen = set()
    for match in sorted(matches, key=lambda entry: entry["start"]):
        key = (match["title"], match["start"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(match)

    return deduped


def append_amazon_prime_channel(root):
    existing = root.find(f"./channel[@id='{AMAZON_PRIME_CHANNEL_ID}']")
    if existing is not None:
        return

    channel = ET.SubElement(root, "channel", {"id": AMAZON_PRIME_CHANNEL_ID})
    ET.SubElement(channel, "icon", {"src": AMAZON_PRIME_LOGO})
    ET.SubElement(channel, "url").text = "https://www.amazon.co.uk/gp/video/storefront/"
    ET.SubElement(channel, "display-name", {"lang": "en"}).text = AMAZON_PRIME_CHANNEL_NAME


def append_amazon_prime_programmes(root, matches):
    existing_keys = {
        (
            programme.get("channel"),
            programme.get("start"),
            clean_text(programme.findtext("title", default="")),
        )
        for programme in root.findall("programme")
    }

    added = 0
    for match in matches:
        start_stamp = build_xmltv_timestamp(match["start"])
        stop_stamp = build_xmltv_timestamp(match["stop"])
        key = (AMAZON_PRIME_CHANNEL_ID, start_stamp, clean_text(match["title"]))
        if key in existing_keys:
            continue

        programme = ET.SubElement(
            root,
            "programme",
            {
                "channel": AMAZON_PRIME_CHANNEL_ID,
                "start": start_stamp,
                "stop": stop_stamp,
            },
        )
        ET.SubElement(programme, "title", {"lang": "en"}).text = match["title"]
        ET.SubElement(programme, "sub-title", {"lang": "en"}).text = match["sub_title"]
        ET.SubElement(programme, "desc", {"lang": "en"}).text = match["desc"]
        ET.SubElement(programme, "category", {"lang": "en"}).text = "Football"
        ET.SubElement(programme, "category", {"lang": "en"}).text = "UEFA Champions League"
        ET.SubElement(programme, "icon", {"src": AMAZON_PRIME_LOGO})
        existing_keys.add(key)
        added += 1

    return added

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

        amazon_matches = fetch_amazon_prime_matches()
        append_amazon_prime_channel(new_root)
        amazon_added = append_amazon_prime_programmes(new_root, amazon_matches)
        print(
            f"Amazon Prime overlay: {len(amazon_matches)} matches found, "
            f"{amazon_added} programme entries appended."
        )

        # 3. Save
        new_tree = ET.ElementTree(new_root)
        new_tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
        print("Update complete. epg.xml is ready.")

except Exception as e:
    print(f"Critical Error: {e}")
    exit(1)
