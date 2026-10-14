import json

with open("infra/analysis/corpus/apis-guru-list.json") as f:
    data = json.load(f)

n_apis = len(data)
providers_by_key = {k.split(":")[0] for k in data}
provider_names = set()
missing_xprovider = 0
for k, v in data.items():
    pref = v.get("preferred")
    versions = v.get("versions", {})
    entry = versions.get(pref) or (list(versions.values())[0] if versions else {})
    name = entry.get("info", {}).get("x-providerName")
    if name is None:
        missing_xprovider += 1
    else:
        provider_names.add(name)

print("n_apis", n_apis)
print("n_providers_key_prefix", len(providers_by_key))
print("n_providers_x_providerName", len(provider_names))
print("entries_missing_x_providerName", missing_xprovider)
print("key_prefix_equals_x_providerName", providers_by_key == provider_names)
