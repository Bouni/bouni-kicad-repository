import sys
import json
import hashlib
import re
import time
from datetime import datetime as dt

VERSION=sys.argv[1]
DOWNLOAD_SHA256=sys.argv[2]
DOWNLOAD_SIZE=sys.argv[3]
DOWNLOAD_URL=sys.argv[4]
INSTALL_SIZE=sys.argv[5]
# The KiCad range is optional. With neither end given, as from a caller that
# passes only the five values above, a new entry gets the old "6.0" with no
# maximum and a re-published entry keeps the range it already has. Otherwise
# an empty minimum means "6.0" and an empty maximum means none.
KICAD_VERSION=sys.argv[6] if len(sys.argv) > 6 else ""
KICAD_VERSION_MAX=sys.argv[7] if len(sys.argv) > 7 else ""
RANGE_GIVEN=bool(KICAD_VERSION or KICAD_VERSION_MAX)
KICAD_VERSION=KICAD_VERSION or "6.0"

# KiCad checks packages.json against its PCM schema, and one bad entry stops the
# whole repository from loading, so refuse anything the schema would reject.
for value in (KICAD_VERSION, KICAD_VERSION_MAX):
    if value and not re.fullmatch(r"[0-9]{1,2}(\.[0-9]{1,2}){0,2}", value):
        sys.exit(f"Invalid KiCad version {value!r}, expected major[.minor[.patch]]")

def version_tuple(value, missing):
    parts = [int(part) for part in value.split(".")]
    return tuple(parts + [missing] * (3 - len(parts)))

# KiCad fills a missing part with 0 in a minimum and 999 in a maximum. A range
# that no KiCad falls inside would hide the release from everyone.
if KICAD_VERSION_MAX and version_tuple(KICAD_VERSION, 0) > version_tuple(KICAD_VERSION_MAX, 999):
    sys.exit(f"Empty KiCad range: {KICAD_VERSION} is above {KICAD_VERSION_MAX}")

with open("packages.json", "r+") as f:
    data = json.load(f)
    versions = data["packages"][0]["versions"]
    # An entry is matched by its version alone. Publishing two archives for one
    # version, such as a SWIG build and an IPC build for KiCad 11, will need a
    # richer key, for example the version together with its KiCad range.
    index = None
    for i, version in enumerate(versions):
        if version["version"] == VERSION:
            index = i
            break
    if index is not None and not RANGE_GIVEN:
        KICAD_VERSION = versions[index].get("kicad_version", KICAD_VERSION)
        KICAD_VERSION_MAX = versions[index].get("kicad_version_max", "")
    info = {
          "version": VERSION,
          "status": "testing",
          "kicad_version": KICAD_VERSION,
          "kicad_version_max": KICAD_VERSION_MAX,
          "download_sha256": DOWNLOAD_SHA256,
          "download_size": int(DOWNLOAD_SIZE),
          "download_url": DOWNLOAD_URL, 
          "install_size": int(INSTALL_SIZE)
    }
    if not KICAD_VERSION_MAX:
        del info["kicad_version_max"]
    if index is not None:
        versions[index] = info
    else:
        versions.append(info)
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


