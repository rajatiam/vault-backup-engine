# Vault Backup Engine: architecture

## Content addressing and verified restore

Each file is hashed with SHA-256. Blobs are deterministically gzip-compressed and reused by digest; snapshot manifests identify relative paths, digests and sizes. Restore validates the complete manifest and checksums before staging output in a temporary sibling directory.

## Module boundaries

`vault_backup_engine/core.py` contains the algorithm and persistence operations. `cli.py` validates arguments and prints JSON. The package entrypoint translates input and storage errors into structured stderr with exit status 2. Domain-specific unsuccessful results can use exit status 1. There is no shared runtime dependency on the portfolio folder.

## Failure and operational boundaries

Reject source-tree vaults, symlinks, unsafe paths and existing destinations. A corrupt blob cannot silently become restored data. File permissions, empty directories and point-in-time consistency of a changing source are outside this format. Interrupted snapshot publication can leave unreferenced blobs; concurrent snapshot writers are not supported.

## Verification

Core tests cover valid results and failure boundaries. Process-level CLI tests run the committed examples in temporary copies, inspect JSON output and verify domain outcomes. CI runs on Python 3.11 and 3.13, Linux and Windows, checks package installation, and builds and executes the non-root Docker image.

## Extension choices

The standard-library implementation keeps local execution inspectable and offline. A hosted or distributed version would require workload-specific authorization, resource limits, durable coordination and observability. Extend the core through tested functions rather than adding infrastructure without a scaling requirement.
