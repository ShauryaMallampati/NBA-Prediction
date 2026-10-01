# Data sources and provenance

Earlier project experiments used the [Wyatt O'Walsh basketball dataset](https://www.kaggle.com/datasets/wyattowalsh/basketball) and [NBA Stats](https://stats.nba.com/).

Those references do not establish which exact dataset version produced older results. No pinned training snapshot, associated download manifest, or frozen trained ensemble is distributed in this release, and provider-specific ingestion prototypes are intentionally excluded from the verified release tree.

For a reproducible run, retain the provider's exact version/download date, original file hash, applicable permissions/license, and the transformations used to produce the [completed-game input schema](REPRODUCIBILITY.md). Do not redistribute data simply because this repository's code is MIT-licensed: code licensing and data permissions are separate.

The test suite uses explicitly synthetic fixtures and small synthetic training runs. Those fixtures contain no NBA performance evidence.
