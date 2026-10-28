"""Compare hash strings in the clean build's manifest.json with the project's (no data or label file is opened)."""
import json, sys
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
def flat(d, p=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items(): out.update(flat(v, f"{p}/{k}"))
    elif isinstance(d, list):
        for i, v in enumerate(d): out.update(flat(v, f"{p}[{i}]"))
    else: out[p] = d
    return out
fa, fb = flat(a), flat(b)
hk = [k for k in fb if isinstance(fb[k], str) and len(fb[k]) == 64 and all(c in "0123456789abcdef" for c in fb[k])]
diff = [k for k in hk if fa.get(k) != fb[k]]
other = [k for k in fb if k not in hk and fa.get(k) != fb[k]]
print("hash strings compared:", len(hk), "differ:", len(diff), diff[:10])
print("non-hash fields differing:", len(other), other[:15])
print("keys only in clean:", [k for k in fa if k not in fb][:10])
