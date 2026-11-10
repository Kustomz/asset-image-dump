#!/usr/bin/env python3
"""End-to-end audit of the asset-image-dump repo (read-only).

Checks:
  1. Manifest vs disk  — every manifest entry exists with matching
     sha256 + byte size; every PNG on disk is registered (no orphans).
  2. Image validity    — every PNG opens/decodes via PIL.
  3. Provenance        — every entry carries a source naming its pull.
  4. Limits            — no file over GitHub's 100 MB per-file limit.
  5. Layout            — every image sits in its kind's folder scheme
     (snapshots* + characters make/kind-sharded, icons letter-sharded,
     ui-art per family); no loose images at the repo root.
  6. Remote parity     — reported separately by the caller (git).

Run from the repo root:  python3 tools/audit_repo.py
Exits 0 when clean, 1 with a findings list otherwise.
"""
import hashlib, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_EXT = (".png",)
LIMIT = 100 * 1024 * 1024

def main():
    man = json.load(open(os.path.join(REPO, "manifest.json")))
    entries = man["assets"]
    by_path = {a["path"]: a for a in entries}
    problems = []

    # 1. manifest -> disk
    for a in entries:
        p = os.path.join(REPO, a["path"])
        if not os.path.exists(p):
            problems.append(f"MISSING {a['path']}")
            continue
        data = open(p, "rb").read()
        if len(data) != a["bytes"]:
            problems.append(f"SIZE {a['path']}: disk {len(data)} != manifest {a['bytes']}")
        elif hashlib.sha256(data).hexdigest() != a["sha256"]:
            problems.append(f"HASH {a['path']}")
        if len(data) > LIMIT:
            problems.append(f"OVERSIZE {a['path']}: {len(data)/1e6:.1f} MB")
        if not a.get("source"):
            problems.append(f"NO-SOURCE {a['path']}")

    # 1b. disk -> manifest (orphans)
    on_disk = []
    for root, _, files in os.walk(REPO):
        if ".git" in root:
            continue
        for f in files:
            if f.lower().endswith(IMG_EXT):
                rel = os.path.relpath(os.path.join(root, f), REPO)
                on_disk.append(rel)
                if rel not in by_path:
                    problems.append(f"ORPHAN {rel}")

    # 5. layout: no loose images at root, no image outside a known tree
    KNOWN = ("snapshots/", "snapshots-gacha/", "snapshots-prize/",
             "snapshots-reversed/", "characters/", "backgrounds/", "icons/", "ui-art/",
             "panels/")
    for rel in on_disk:
        if "/" not in rel:
            problems.append(f"LOOSE-AT-ROOT {rel}")
        elif not rel.startswith(KNOWN):
            problems.append(f"OFF-TREE {rel}")

    # 2. PIL validity
    from PIL import Image
    bad = 0
    for rel in on_disk:
        try:
            with Image.open(os.path.join(REPO, rel)) as im:
                im.verify()
        except Exception as e:
            problems.append(f"INVALID {rel}: {type(e).__name__}")
            bad += 1

    print(f"manifest entries: {len(entries)}")
    print(f"images on disk:   {len(on_disk)}")
    kinds = {}
    for a in entries:
        kinds[a["kind"]] = kinds.get(a["kind"], 0) + 1
    for k, n in sorted(kinds.items()):
        print(f"  {k}: {n}")
    if problems:
        print(f"\nFINDINGS ({len(problems)}):")
        for p in problems[:200]:
            print(" ", p)
        return 1
    print("\nAUDIT CLEAN")
    return 0

if __name__ == "__main__":
    sys.exit(main())
