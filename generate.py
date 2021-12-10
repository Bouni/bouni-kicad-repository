import sys
import json
import hashlib
import time
from datetime import datetime as dt

VERSION=sys.argv[1]
DOWNLOAD_SHA256=sys.argv[2]
DOWNLOAD_SIZE=sys.argv[3]
DOWNLOAD_URL=sys.argv[4]
INSTALL_SIZE=sys.argv[5]

with open("packages.json", "r+") as f:
    data = json.load(f)
    info = {
          "version": VERSION,
          "status": "testing",
          "kicad_version": "6.0",
          "download_sha256": DOWNLOAD_SHA256,
          "download_size": int(DOWNLOAD_SIZE),
          "download_url": DOWNLOAD_URL, 
          "install_size": int(INSTALL_SIZE)
    }
    index = None
    for i, version in enumerate(data["packages"][0]["versions"]):
        if version["version"] == VERSION:
            index = i
            break
    if index is not None:
        data["packages"][0]["versions"][index] = info
    else:
        data["packages"][0]["versions"].append(info)
    f.seek(0)
    json.dump(data, f, indent=4)
    f.truncate()

with open("packages.json", "rb") as f:
    bytes = f.read()
    PACKAGES_SHA256 = hashlib.sha256(bytes).hexdigest();

with open("repository.json", "r+") as f:
    data = json.load(f)
    date = dt.utcnow()
    data["packages"]["sha256"] = PACKAGES_SHA256
    data["packages"]["update_time_utc"] = date.strftime("%Y-%m-%d %H:%M:%S") 
    data["packages"]["update_timestamp"] = int(time.mktime(date.timetuple()))
    f.seek(0)
    json.dump(data, f, indent=4)
    f.truncate()


