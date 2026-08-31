# Validation

Validate one bundle or a pull-request revision range with:

```bash
basemode-evidence validate contributions/v1/2026/08/<bundle-id>.json
basemode-evidence validate-pr --base BASE_SHA --head HEAD_SHA
```

The PR gate requires exactly one newly added
`contributions/v1/YYYY/MM/<bundle-id>.json` and rejects every other change. It also rejects bundle IDs
already present in the base revision's history.

Bundle validation enforces:

1. filename ID and path year/month agree with the payload and `window_end`;
2. the payload matches the pinned schema with no unknown fields;
3. counts are non-negative integers and arithmetic relationships are consistent;
4. failure totals do not exceed attempts;
5. metric counts do not exceed successful operations and `p50 <= p95`;
6. UTC timestamps, an ordered window, and sensible construction time;
7. restricted identifier characters and lengths;
8. unique observation dimensions;
9. conservative resource limits and content/secret scanning.

Current policy limits are 1 MB per file, 1,000 rows, 31 days per window, 128 characters per endpoint
or strategy identifier, and 24 hours of future clock skew. Historical bundles are compiled without a
wall-clock check so a repository tree remains reproducible.

Successful validation prints a content-free summary containing the window, endpoints, operations,
attempts, failures, schema version, and confirmation that no content-bearing fields were accepted.
