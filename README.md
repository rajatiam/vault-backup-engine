# Vault Backup Engine

Content-addressed snapshots, integrity verification and safe restore. An independent Python 3.11+ project using the standard library, with a real command-line interface and no runtime package dependencies.

## Run locally

From the cloned repository, run:

```sh
python -m vault_backup_engine snapshot examples/source examples/vault --name first
python -m vault_backup_engine verify examples/vault first
python -m vault_backup_engine restore examples/vault first examples/restored
```

Examples contain synthetic data. First use requires no cloud account, API key or package download. Optionally install the CLI using `python -m pip install .` and run `vault-backup-engine --help`.

## Verify

```sh
python -m unittest discover -v
```

GitHub Actions checks Python 3.11 and 3.13 on Linux and Windows, verifies package installation, and builds/runs the non-root Docker image.

```sh
docker build -t vault-backup-engine .
docker run --rm vault-backup-engine --help
```

Mount a working directory at `/workspace` to process your own files. The container runs as UID 10001; provide appropriate write permissions for outputs.

## Architecture and scope

Business algorithms live in `vault_backup_engine/core.py`; `vault_backup_engine/cli.py` owns argument parsing and JSON output. Tests exercise success cases and failure boundaries, with temporary storage for mutations. See [design decisions](docs/architecture.md).

Snapshots are gzip-compressed and SHA-256 addressed, not encrypted. Keep sensitive backups on encrypted storage. Symlinks are rejected; existing restore files are never overwritten.

This project demonstrates implemented engineering practices. It does not claim production deployment history or external certifications.

## Snapshot comparison

Compare two snapshot manifests without restoring data. The report identifies added, removed and content-changed paths.

```sh
python -m vault_backup_engine snapshot examples/source examples/vault --name second
python -m vault_backup_engine compare examples/vault first second
```

Create the named input snapshots, databases or plan files first using the existing commands above.
