import re
import sys
import urllib.request

PORT = sys.argv[1]
for line in sys.stdin:
    sys.stdout.write(line)
    sys.stdout.flush()
    clean = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", line)
    m = re.search(r"Starting phase (\w+)", clean)
    label = m.group(1) if m else ("HTTP_ORACLE" if "Starting to apply HTTP oracle detection" in clean else None)
    if label:
        try:
            urllib.request.urlopen("http://localhost:%s/__mark/%s" % (PORT, label), timeout=5).read()
        except Exception as e:
            sys.stdout.write("MARK FAILED %s %s\n" % (label, e))
