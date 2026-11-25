"""Publish an independent copy of the public files listed in the release manifest."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from urllib.request import Request, urlopen

ORIGINS = (
    "https://weizhenkong.vercel.app/",
    "https://resilient-cucurucho-a1abe2.netlify.app/",
)


def download(item):
    name, expected = item
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"Invalid path: {name}")
    last_error = None
    for origin in ORIGINS * 2:
        try:
            request = Request(origin + quote(name), headers={"User-Agent": "WeizhenKong-Portfolio-Publisher/1.0"})
            with urlopen(request, timeout=25) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError("release checksum mismatch")
        except (OSError, ValueError) as error:
            last_error = error
            continue
        destination = Path("site") / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return
    raise RuntimeError(f"Could not verify {name}: {last_error}")


if __name__ == "__main__":
    manifest = json.loads(Path("release.json").read_text())
    with ThreadPoolExecutor(max_workers=8) as pool:
        for _ in pool.map(download, manifest.items()):
            pass
    print(f"Verified {len(manifest)} published files.")
