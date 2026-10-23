"""Fetch the observed-declaration corpus and verify it against the deposit.

The data is not vendored. It is downloaded from the deposit that published it
and checked against the digest that deposit records, so a run here is pinned to
bytes the depositor published rather than to a copy we made.
"""
import hashlib, sys, urllib.request
from pathlib import Path

RECORD = "21778282"
BASE = f"https://zenodo.org/api/records/{RECORD}/files"
DATA = Path(__file__).resolve().parent / "data"

# From the deposit's own SHA256SUMS.
WANT = {
    "declared_vectors_v1.csv":
        "36266d02957dca37adea910c7ac0922ee90dda554cd638802833df1040b0d2fd",
    "flips_v1.csv":
        "7bcc2475e27d9c0eb4982d058dd6a342c5ad96257ff8e80ad89df3677e49eddd",
}


def ensure(name: str) -> Path:
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / name
    if not path.exists():
        urllib.request.urlretrieve(f"{BASE}/{name}/content", path)
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != WANT[name]:
        raise SystemExit(f"{name}: digest mismatch\n  want {WANT[name]}\n  got  {got}")
    return path


if __name__ == "__main__":
    for n in WANT:
        print("ok", ensure(n))
