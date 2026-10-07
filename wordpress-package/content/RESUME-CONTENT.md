# Resume the reviewed content/media handoff

The user authorized continuing the complete WordPress package and explicitly accepted the available original generator-native resolution. **Do not ask the 8K question again.** The persistent quality tier is source long edge **at least 1,024 pixels**, actual measured dimensions, **no upscaling and no native 8K claim**. Fully covered loose opaque clothing, full uncropped head/hair/nape, genuine views and coherent haircut identity remain required.

## Latest content checkpoint

The last content-side synchronization read the master media manifest and verified **14 existing source files**: **nine canonical front views, four canonical side views and one diagnostic-only probe**. It found **zero declared approved coherent three-angle looks**, **zero completed collections**, and **zero available guide-photo sets**. The media producer may have newer reviewed or pending files after this snapshot; rerun synchronization to obtain the actual current counts. Do not substitute remembered planned counts for the on-disk manifest and verified files.

The immediate disk inventory contains **17 PNG source files**: 16 canonical partial-view photos plus the probe. Three existing sources were not yet registered in the master manifest at this content snapshot: `natural-grey-01-front.png`, `feathered-01-side.png` and `wavy-01-side.png`. Preserve and reconcile their actual review/metadata with the media producer; do not regenerate them to fill a manifest gap. The root reports the16canonical views as10front/6side; content-side approved completion remainszero until genuine backs and coherent-set declarations exist.

There remain **154 complete launch looks / 462 original collection-view photos** across 22 primary collections. The 25 dedicated homepage photo roles and real `home-motion-film` have separate requirements. The homepage retains minimum75 unique photos and the current77-placement target. Each collection needs at least seven complete looks and20 unique approved photographs (planned7×3=21). Each public look needs actual approved front, side and back views. Guides require their allocated3/6real photographs.

`catalog.json` contains42block-editable page records,22collection definitions,7image-led guides, and the auditable keyword map. Planning briefs remain separate and are not imported as delivered looks. Current actual-only status is in `actual-source-counts.json`; current integrity evidence is `content-validation.json` (last run28/28passed).

## Source paths and commands

Canonical editable importer payload:

```text
/workspace/check.txt/wordpress-package/content/catalog.json
```

Actual master media aggregator:

```text
/workspace/check.txt/wordpress-package/media/manifest.json
```

Actual source files are rooted at `/workspace/check.txt/wordpress-package`, normally under `source-media/`; optimized renditions are under `media/`. Do not regenerate or overwrite an existing reviewed source merely to repeat the workflow. The separate production plan is not evidence of generated files.

Run after the media agent writes actual approved complete sets:

```bash
python /workspace/check.txt/wordpress-package/content/sync_reviewed_media.py
python /workspace/check.txt/wordpress-package/content/validate_content.py
```

For a separately delivered batch:

```bash
python /workspace/check.txt/wordpress-package/content/sync_reviewed_media.py --manifest /absolute/bundle/manifest.json --bundle-root /absolute/bundle
```

The default development verifier requires Python3 and Pillow. The installable WordPress package does not require Python. Synchronization is read-only on media and updates only this content folder. It rechecks earlier actual sets when merging later batches; no live WordPress database is changed by these commands.

## Exact actual-media schema

The source producer’s master manifest supplies `bundle_id`, `records` and `looks`. Each **approved actual source record** should include:

```json
{
  "key": "classic-01-front",
  "look_id": "classic-01",
  "angle": "front",
  "source_file": "source-media/classic-01-front.png",
  "file": "media/classic-01-front.webp",
  "width": 1122,
  "height": 1402,
  "sha256": "ACTUAL_SHA256_OF_NATIVE_SOURCE_FILE",
  "alt": "REVIEWED_DESCRIPTION_OF_THIS_ACTUAL_FRONT_IMAGE",
  "caption": "REVIEWED_FRONT_CAPTION",
  "approved": true,
  "review_status": "approved",
  "native_8k": false,
  "upscaled": false
}
```

The example dimensions are the observed pilot-front dimensions; every record must store its own real dimensions. Never copy these values blindly. The hash is for `source_file`, not the WebP rendition. Use only actual reviewed descriptions. IDs are `<collection>-01` through`<collection>-07`; view IDs append`-front`, `-side` or`-back`.

A **look declaration** confirms set-level coherence, beyond approving three unrelated images separately:

```json
{
  "key": "classic-01",
  "slug": "classic-01",
  "primary_collection": "classic",
  "title": "ACTUAL_REVIEWED_CONCEPT_TITLE",
  "excerpt": "A_SHORT_FACTUAL_DESCRIPTION_OF_THE_REVIEWED_SHAPE",
  "meta": {
    "texture": "ACTUALLY_REVIEWED_TEXTURE",
    "length": "ACTUALLY_REVIEWED_LENGTH",
    "fringe": "ACTUALLY_REVIEWED_FRINGE",
    "colour": "ACTUALLY_REVIEWED_COLOUR",
    "ai_concept": true
  },
  "approved": true,
  "review_status": "approved",
  "review": {
    "identity_consistency": "ACTUAL_REVIEW_RESULT",
    "haircut_consistency": "ACTUAL_REVIEW_RESULT",
    "attire_and_full_frame": "ACTUAL_REVIEW_RESULT"
  }
}
```

These JSON snippets specify the interface and must not themselves be inserted as approved content. Set-level approval must follow real inspection of the same adult, hair colour, fringe, crown, length, parting and nape across corresponding angles. The diagnostic probe remains excluded from homepage/gallerycounts by the root’s decision.

Canonical collections:

```text
classic, short, long, layered, choppy, shaggy, feathered, straight,
wavy, curly, fine-hair, thin-hair, thick-hair, bangs, over-40,
over-50, over-60, natural-grey, 90s-inspired, round-face,
undercut, easy-styling
```

The synchronizer verifies source existence, image decodability, hash, true dimensions, explicit approval, no upscale and native minimum. It requires a declared approved look plus three different approved source hashes for front/side/back; cross-look source reuse cannot inflate counts. Partial, failed or inconsistent sets stay out of `catalog.looks` and remain diagnostic. Homepage-role records are counted separately; real film verification is not inferred from image plans.

## Guide and publication gates

Guide `photo_set_requirements` allocate: definition`classic-01`; consultation`classic-02`; styling`easy-styling-03`; fine-vs-thin`fine-hair-01` plus`thin-hair-01`; angle reading`layered-02`; grow-out`long-03`; shixie comparison`shaggy-03`. These24view references reuse real canonical media records without counting additional original sources.

The plugin importer resolves approved look IDs and inserts **real native core Gallery/Image blocks** after the intro. No phantom picture blocks, fake bob/wolf-cut labels, or fabricated before-and-after sequence. All guides remain drafts while their real required sets are absent. Collection pages remain draft below20unique approved views/seven complete looks. Home stays gated by its dedicated roles, film and actual unique photo requirements. Contact/privacy remain owner-dependent where genuine contact/hosting policy facts are missing.

The catalog keeps `requirements.required_home_media` (25rolekeys), `required_home_video`, `minimum_home_unique_photos`, `site.home_pattern` and guide allocations intact. Avoid replacing the integrated catalog with an older generated copy.

## Plugin handoff and packaging

After actual synchronization, notify the `interaction` agent/root to refresh the embedded copy at:

```text
/workspace/check.txt/wordpress-package/plugin/bixie-library/content/catalog.json
```

The plugin’s media bundle layout expects `content/media/manifest.json` and native sources under`content/source-media/`, preserving relative source paths. The importer is owner-initiated, idempotent and preserves owner edits. Do not replace existing public data or media from this content-side script.

Do not label the package launch-complete while any required actual look/view, collection, guide-photo dependency, home role/film or verification remains missing. The persistent source/code checkpoint is safe to resume; publication counts must come from actual approved records and successful runtime import.
