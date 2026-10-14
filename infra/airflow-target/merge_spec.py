import json, subprocess, sys


def load(p):
    if p.endswith((".yaml", ".yml")):
        r = subprocess.run(["ruby", "-ryaml", "-rjson", "-e",
                            "print JSON.dump(YAML.safe_load(File.read(ARGV[0]), aliases: true))", p],
                           capture_output=True, text=True, check=True)
        return json.loads(r.stdout)
    with open(p) as f:
        return json.load(f)


def main(core_path, fab_path, out_path):
    core, fab = load(core_path), load(fab_path)
    merged = dict(core)
    merged["paths"] = dict(core.get("paths") or {})
    clash_paths = []
    for p, item in (fab.get("paths") or {}).items():
        if p in merged["paths"]:
            clash_paths.append(p)
        merged["paths"][p] = item
    comp = dict(core.get("components") or {})
    clash_schemas = []
    for sect, vals in (fab.get("components") or {}).items():
        tgt = dict(comp.get(sect) or {})
        for k, v in vals.items():
            if k in tgt and json.dumps(tgt[k], sort_keys=True) != json.dumps(v, sort_keys=True):
                clash_schemas.append("%s/%s" % (sect, k))
            tgt[k] = v
        comp[sect] = tgt
    merged["components"] = comp
    merged["info"] = {"title": "airflow-core-plus-fab", "version": "merged"}
    with open(out_path, "w") as f:
        json.dump(merged, f, indent=1)
    print("core paths", len(core.get("paths") or {}), "fab paths", len(fab.get("paths") or {}),
          "merged", len(merged["paths"]))
    print("path clashes:", clash_paths or "none")
    print("schema clashes:", clash_schemas or "none")
    print("openapi:", core.get("openapi"), fab.get("openapi"))


if __name__ == "__main__":
    main(*sys.argv[1:])
