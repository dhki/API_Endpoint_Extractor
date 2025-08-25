import os
import xml.etree.ElementTree as ET

## parse xml file and return urls
## if component's value starts with http/https, consider it as API Endpoints
def parse_xml_values(path: str):
    if os.path.exists(path) is False:
        print("[!] File does not exist")
        print(f"    {path}")
        return []

    print("=" * 50)
    print(f"{'Parsing string.xml...'.center(50)}")
    print("-" * 50)
    ret = set()
    tree = ET.parse(path)
    root = tree.getroot()

    for elem in root.iter():
        if elem.text and (elem.text.startswith("http://") or elem.text.startswith("https://")):
           ret.add(elem.text.strip())
           print(elem.text.strip())
    
    print("=" * 50)
    return ret
    
