# Contributing Evidence

Basemode generates the bundle, provides the content-free preview, and optionally orchestrates the
pull request. This repository only validates and compiles what arrives.

For a generated bundle:

1. inspect the content-free preview locally;
2. place it at `contributions/v1/YYYY/MM/<bundle-id>.json`, using `window_end` for the directory;
3. run `basemode-evidence validate PATH`;
4. open a pull request containing that file and no other changes;
5. wait for automated validation and maintainer review.

Do not edit an index or another contributor's file. Do not combine a contribution with code,
documentation, schema, workflow, or revocation changes. The dedicated workflow builds its validator
from the trusted base revision before checking out contributor-controlled data.

See [[Privacy Model]] before exporting and [[Contribution Format]] for field semantics.
