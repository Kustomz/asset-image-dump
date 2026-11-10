#!/usr/bin/env python3
"""Pull official car snapshots into this repo via Kustomz Imports.

Source of truth for URLs is the SnapshotCDN manifest (the local copy the
Toolbox built from CDNSnapshots.meta: ~/workspace/toolbox/snapshot_kinds.json).
Each pull is logged to the repo manifest.json with sha256 + byte size, and a
human-readable line is appended to pulls.log.

Usage:
    python3 tools/pull_snapshots.py CRDB [CRDB ...]   # specific cars
    python3 tools/pull_snapshots.py --all             # full manifest (1,275 cars)

Snapshots are per-CRDB (variant-exact): Reward and RewardRecycled are
different CRDBs with different renders. Never substitute one variant's
image for another.
"""
import hashlib
import json
import os
import sys
from datetime import date

import requests

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_SRC = os.path.expanduser("~/workspace/toolbox/snapshot_kinds.json")
OUT_DIR = os.path.join(REPO, "snapshots")
MANIFEST = os.path.join(REPO, "manifest.json")
PULL_LOG = os.path.join(REPO, "pulls.log")


def load_manifest():
    if os.path.exists(MANIFEST):
        return json.load(open(MANIFEST))
    return {"repo": "Kustomz/asset-image-dump", "assets": []}


KIND_DIRS = {"DEFAULT": "snapshots", "GACHA": "snapshots-gacha",
             "PRIZE": "snapshots-prize", "DEFAULT_REVERSED": "snapshots-reversed"}


PREGEN_CROP_CARS = {"Audi_RS6AvantReward_2020", "Audi_RS6AvantRewardRecycled_2020",
                    "Bentley_MullinerBacalarRewardRecycled_2021"}


def main(argv):
    kind = "DEFAULT"
    if argv and argv[0] == "--kind":
        kind = argv[1].upper()
        argv = argv[2:]
    kinds = json.load(open(MANIFEST_SRC))["cars"]
    if argv == ["--all"]:
        want = sorted(kinds.keys())
    elif argv:
        want = argv
    else:
        print(__doc__)
        return 2
    man = load_manifest()
    by_path = {a["path"]: a for a in man["assets"]}
    added, skipped, failed = 0, 0, []
    for crdb in want:
        entry = kinds.get(crdb)
        url_key = f"{kind}_url"
        if not entry or url_key not in entry:
            failed.append((crdb, f"no {kind} snapshot in manifest"))
            continue
        path = f"{KIND_DIRS[kind]}/{crdb.split(chr(95))[0]}/{crdb}.png"
        dest = os.path.join(REPO, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        # Rick (2026-11-10): these three cars' snapshots/ files are the PreGen
        # tighter crops by his decision (listing-preferred framing). A DEFAULT
        # re-pull must not clobber them while the crop is intact on disk.
        if kind == "DEFAULT" and crdb in PREGEN_CROP_CARS and path in by_path and os.path.exists(dest):
            import hashlib as _h
            if _h.sha256(open(dest, "rb").read()).hexdigest() == by_path[path]["sha256"]:
                skipped += 1
                continue
        # fast path: registered + present at the recorded size -> no download
        if (path in by_path and os.path.exists(dest)
                and os.path.getsize(dest) == by_path[path].get("bytes")):
            skipped += 1
            continue
        r = None
        for attempt in (1, 2):
            try:
                r = requests.get(entry[url_key], timeout=30)
                break
            except requests.RequestException as e:
                if attempt == 2:
                    failed.append((crdb, f"fetch failed: {type(e).__name__}"))
                    r = None
        if r is None:
            continue
        if r.status_code != 200:
            failed.append((crdb, f"HTTP {r.status_code}"))
            continue
        sha = hashlib.sha256(r.content).hexdigest()
        if path in by_path and by_path[path]["sha256"] == sha and os.path.exists(dest):
            skipped += 1
            continue
        with open(dest, "wb") as fh:
            fh.write(r.content)
        by_path[path] = {
            "path": path, "kind": f"car_snapshot_{kind.lower()}", "crdb": crdb,
            "source": f"Kustomz Imports — SnapshotCDN manifest ({kind}), Zynga snapshot CDN",
            "pulled": str(date.today()), "bytes": len(r.content), "sha256": sha,
        }
        added += 1
    man["assets"] = sorted(by_path.values(), key=lambda a: a["path"])
    json.dump(man, open(MANIFEST, "w"), indent=1)
    with open(PULL_LOG, "a") as fh:
        fh.write(f"{date.today()} snapshots[{kind}]: +{added} new/changed, {skipped} unchanged, "
                 f"{len(failed)} failed {failed if failed else ''}\n")
    print(f"done: +{added} new/changed, {skipped} unchanged, {len(failed)} failed")
    for crdb, why in failed:
        print(f"  FAILED {crdb}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
