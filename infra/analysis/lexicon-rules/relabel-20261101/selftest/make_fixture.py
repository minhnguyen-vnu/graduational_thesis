import json, os, sys

W = sys.argv[1]
manifest = {"train": {}, "known": {}, "test": {}}
sizes = {"train": 9, "known": 1, "test": 4}
for stage, n in sizes.items():
    d = os.path.join(W, "blocks", stage)
    os.makedirs(d)
    for i in range(1, n + 1):
        name = "chunk-%03d" % i
        ids = ["%s%02d-N%04d" % (stage[:2].upper(), i, k) for k in range(1, 4)]
        manifest[stage][name] = ids
        text = "\n".join("## %s  POST /x\n" % r for r in ids)
        if stage == "test" and i == 3:
            text += "BADBLOCK\n"
        open(os.path.join(d, name + ".txt"), "w").write(text)
json.dump(manifest, open(os.path.join(W, "manifest.json"), "w"))
