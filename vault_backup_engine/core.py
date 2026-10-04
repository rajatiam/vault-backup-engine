"""Integrity-checked content-addressed snapshots with conservative restores."""

from pathlib import Path, PurePosixPath
import gzip, hashlib, json, os, re, tempfile, zlib

MAX_FILE_BYTES = 32 * 1024 * 1024


def snapshot(source, vault, name):
    source, vault = Path(source).resolve(), Path(vault).resolve()
    if not source.is_dir():
        raise ValueError("Source must be a directory")
    if vault == source or source in vault.parents:
        raise ValueError("Vault must be outside the source tree")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name):
        raise ValueError("Unsafe snapshot name")
    manifest = vault / "snapshots" / (name + ".json")
    if manifest.exists():
        raise ValueError("Snapshot already exists")
    entries = []
    for file in sorted(source.rglob("*")):
        if file.is_symlink():
            raise ValueError("Symlinks are not supported")
        if not file.is_file():
            continue
        if file.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("File exceeds 32 MiB limit")
        data = file.read_bytes()
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("File exceeds 32 MiB limit")
        digest = hashlib.sha256(data).hexdigest()
        blob = vault / "blobs" / (digest + ".gz")
        blob.parent.mkdir(parents=True, exist_ok=True)
        if blob.exists():
            if read_blob(vault, digest) != data:
                raise ValueError("Existing blob failed integrity verification")
        else:
            with tempfile.NamedTemporaryFile(dir=blob.parent, delete=False) as tmp:
                temporary = Path(tmp.name)
                tmp.write(gzip.compress(data, mtime=0))
            try:
                os.replace(temporary, blob)
            finally:
                temporary.unlink(missing_ok=True)
        entries.append(
            {
                "path": file.relative_to(source).as_posix(),
                "sha256": digest,
                "bytes": len(data),
            }
        )
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("x", encoding="utf-8") as out:
        json.dump({"format": 1, "name": name, "files": entries}, out, indent=2)
    return {
        "snapshot": name,
        "files": len(entries),
        "bytes": sum(f["bytes"] for f in entries),
    }


def read_blob(vault, digest):
    if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
        raise ValueError("Invalid blob identifier")
    try:
        with gzip.open(Path(vault) / "blobs" / (digest + ".gz"), "rb") as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
    except (OSError, EOFError, zlib.error) as exc:
        raise ValueError("Corrupt or missing blob") from exc
    if len(data) > MAX_FILE_BYTES or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("Blob integrity mismatch")
    return data


def load_manifest(vault, name):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name):
        raise ValueError("Unsafe snapshot name")
    manifest = json.loads(
        (Path(vault) / "snapshots" / (name + ".json")).read_text(encoding="utf-8")
    )
    if manifest.get("format") != 1 or not isinstance(manifest.get("files"), list):
        raise ValueError("Unsupported manifest")
    seen = set()
    for item in manifest["files"]:
        path = PurePosixPath(item["path"])
        if (
            path.is_absolute()
            or ".." in path.parts
            or not path.parts
            or "\\" in item["path"]
            or ":" in item["path"]
        ):
            raise ValueError("Unsafe restore path")
        if item["path"] in seen:
            raise ValueError("Duplicate manifest path")
        seen.add(item["path"])
    return manifest


def verify(vault, name):
    manifest = load_manifest(vault, name)
    for item in manifest["files"]:
        if len(read_blob(vault, item["sha256"])) != item["bytes"]:
            raise ValueError("Manifest size mismatch")
    return {"snapshot": name, "verified": True, "files": len(manifest["files"])}


def restore(vault, name, target):
    verify(vault, name)
    manifest = load_manifest(vault, name)
    target = Path(target).absolute()
    if target.exists() or target.is_symlink():
        raise ValueError("Restore target must not exist")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as staging:
        for item in manifest["files"]:
            file = Path(staging) / item["path"]
            file.parent.mkdir(parents=True, exist_ok=True)
            with file.open("xb") as out:
                out.write(read_blob(vault, item["sha256"]))
        os.rename(staging, target)
    return {"restored": str(target), "files": len(manifest["files"])}


def compare(vault, before, after):
    old = {
        item["path"]: item["sha256"] for item in load_manifest(vault, before)["files"]
    }
    new = {
        item["path"]: item["sha256"] for item in load_manifest(vault, after)["files"]
    }
    return {
        "before": before,
        "after": after,
        "added": sorted(new.keys() - old.keys()),
        "removed": sorted(old.keys() - new.keys()),
        "changed": sorted(
            key for key in old.keys() & new.keys() if old[key] != new[key]
        ),
    }
