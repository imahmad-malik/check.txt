# Original media production

These helpers preserve genuine generated originals and record their actual resolution and hashes. They never generate images, add angles from crops, upscale, or inflate counts. Generation itself uses the available `image_gen` tool with `media/generation-plan.json` and real inspected original reference files.

The accepted native quality is at least 1024 pixels on the long edge. No 8K claim is made. Every hairstyle portrait needs loose opaque high-neck clothing, a complete hair outline with margin, sharp detail and its full source aspect. A gallery look becomes complete only after three separately generated front, side and back photographs pass individual and coherent-set review.

Run from any directory; `BIXIE_PACKAGE_ROOT` optionally selects another extracted package root:

```sh
python media-production/ingest_generated.py IMAGE_ID /absolute/tool-output.png
python media-production/native_source.py IMAGE_ID
python media-production/aggregate_media.py
```

The first command refuses to overwrite an existing original. The native source command encodes a lossless WebP without scaling and verifies its decoded RGB pixels equal the generator PNG. Generator PNG, native lossless WebP and optimized display WebP count as one photograph. Inspection JPEGs and photo-sequence films do not add photographic originals. The aggregator verifies files and hashes, then derives look images from current top-level records so paths and hashes remain consistent.

Individual approval lives in `media/records/*.json`. Disjoint worker coherent-set declarations live in `media/workers/*.json`. Failed attempts stay separately archived and excluded from approved launch totals. Only the master media owner runs the aggregator. `media/progress.json` lists missing IDs, unresolved records and genuine completed look keys for resume.

Use small full-aspect JPEG copies solely for visual inspection to avoid carrying large PNG payloads in tool conversations; do not use these JPEGs as native sources. Save each actual tool output and its exact prompt/reference metadata before starting another call. If an earlier call's exact prompt cannot be recovered, mark it unavailable instead of describing a reconstructed prompt as exact.
