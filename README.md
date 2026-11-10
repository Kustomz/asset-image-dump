# Kustomz Asset Image Dump

The Kustomz store for CSR2 game-asset images — car snapshots, UI/reward
icons, and event/news panels — maintained as the game updates.

## Scope

Images land here in source order:

1. **CDN first** — the snapshot CDN and the CDN asset bundles
   (Kustomz Imports pulls).
2. **Then APK/OBB extraction** — art that never rides the CDN comes out
   of the archived game files (Drive `csr2` folder) in a later pass.

Both sources belong in this repo; the CDN pass simply goes first.

## Rules of the house

- **Imports only.** Every asset in this repo entered through a logged
  **Kustomz Imports** pull (the Kustomz CDN/OBB asset line). No hand-dropped
  files, no screenshots of the game — snapshots and renders only.
- **Provenance is recorded.** `manifest.json` carries every asset's source,
  pull date, byte size, and SHA-256. `pulls.log` is the human-readable
  pull history.
- **Variant-exact.** A snapshot belongs to one CRDB. Reward and
  RewardRecycled are different cars with different renders — never
  substitute one variant's image for another's.

## Layout

| Folder       | Contents                                                        |
|--------------|-----------------------------------------------------------------|
| `snapshots/` | Official car snapshot renders, one PNG per CRDB, sharded by manufacturer (`snapshots/<Make>/<CRDB>.png`). Exception (Rick, 2026-11-10): for `Audi_RS6AvantReward_2020`, `Audi_RS6AvantRewardRecycled_2020` and `Bentley_MullinerBacalarRewardRecycled_2021` the file is the PreGen tighter crop from the UI bundle — his listing-preferred framing, labelled in the manifest; `pull_snapshots.py` will not overwrite those three. |
| `icons/`     | Game UI icons — currency, keys, fusions, reward art.            |
| `panels/`    | Event / news panels and other large-format game art.            |
| `characters/` | Character art — full textures plus cut-out sprites (`sprites/`). |
| `ui-art/<Category>/` | UI art from the csr2ui CDN bundles, landed by category: series art under its series name (Legends, FNF, ART6…), generic art under a content category (Backgrounds, Panels, Logos…); sprites under `sprites/`. Byte-duplicates land once. |
| `backgrounds/` | Background / backdrop art (moved out of `characters/` 2026-11-10 — these came in inside the characters bundle but aren't characters). |
| `snapshots-gacha/`, `snapshots-prize/`, `snapshots-reversed/` | The other official snapshot kinds, same per-make sharding. |
| `tools/`     | The pull scripts that feed this repo.                           |

## Adding snapshots

```bash
# specific cars
python3 tools/pull_snapshots.py Audi_RS3SportbackReward_2023 Nissan_KRCJapanGTRR35Reward_2017

# the full SnapshotCDN manifest
python3 tools/pull_snapshots.py --all
```

The script downloads each car's DEFAULT snapshot from the Zynga snapshot
CDN (URLs from the SnapshotCDN manifest), skips anything whose SHA-256 is
unchanged, and updates `manifest.json` + `pulls.log`.

## Fresh art (icons, panels)

New-game art that the snapshot CDN doesn't carry lives in the installed
game's APK/OBB texture packs. Those pulls run through Kustomz Imports
extraction from the archived version in the Drive `csr2` folder and land
in `icons/` and `panels/` with the same manifest provenance.

## Seeded

2026-11-10 — the eight ShowDown Season 281 Championship snapshots
(Temerario, KRC GT-R, 765LT Spider, RS 3 Sportback — Reward +
RewardRecycled each), pulled via Kustomz Imports for the Kustomz
ShowDown sheet.
