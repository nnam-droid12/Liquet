"""
Alibaba Cloud Integration — Proof File for QwenCloud Hackathon

This module demonstrates concrete use of Alibaba Cloud services:
1. OSS (Object Storage Service) — evidence image upload/fetch for disputes
2. RDS (Relational Database Service) — PostgreSQL production database path
3. Region/config management

Referenced in README.md under "## Proof of Alibaba Cloud Deployment".

Requires:
  pip install oss2 aliyun-python-sdk-core
  env vars: ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET,
            OSS_BUCKET_NAME, OSS_ENDPOINT
"""

from __future__ import annotations

import io
import os
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


# ── OSS Evidence Storage ───────────────────────────────────────────────────────

class OSSEvidenceStore:
    """
    Stores and retrieves dispute evidence images on Alibaba Cloud OSS.

    This is the production backend for the EvidenceStorage interface.
    A local-filesystem fallback (LocalEvidenceStore) is used for offline dev.
    """

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        bucket_name: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        self.access_key_id = access_key_id or os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
        self.access_key_secret = access_key_secret or os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
        self.bucket_name = bucket_name or os.environ.get("OSS_BUCKET_NAME", "liquet-evidence")
        self.endpoint = endpoint or os.environ.get("OSS_ENDPOINT", "oss-us-east-1.aliyuncs.com")
        self._bucket = None

    def _get_bucket(self):
        """Lazy-init OSS bucket connection."""
        if self._bucket is None:
            import oss2
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self._bucket = oss2.Bucket(auth, f"https://{self.endpoint}", self.bucket_name)
        return self._bucket

    def upload_evidence(self, dispute_id: str, filename: str, data: bytes, content_type: str = "image/jpeg") -> str:
        """
        Upload dispute evidence to OSS.
        Returns the public URL of the uploaded object.

        Object key: evidence/{dispute_id}/{filename}
        """
        bucket = self._get_bucket()
        object_key = f"evidence/{dispute_id}/{filename}"
        headers = {"Content-Type": content_type}
        result = bucket.put_object(object_key, data, headers=headers)
        if result.status != 200:
            raise RuntimeError(f"OSS upload failed: status={result.status}")
        url = f"https://{self.bucket_name}.{self.endpoint}/{object_key}"
        logger.info("OSS upload successful", extra={"object_key": object_key, "url": url})
        return url

    def download_evidence(self, dispute_id: str, filename: str) -> bytes:
        """Download evidence bytes from OSS."""
        bucket = self._get_bucket()
        object_key = f"evidence/{dispute_id}/{filename}"
        result = bucket.get_object(object_key)
        return result.read()

    def list_evidence(self, dispute_id: str) -> list[str]:
        """List all evidence file URLs for a dispute."""
        import oss2
        bucket = self._get_bucket()
        prefix = f"evidence/{dispute_id}/"
        urls = []
        for obj in oss2.ObjectIterator(bucket, prefix=prefix):
            urls.append(f"https://{self.bucket_name}.{self.endpoint}/{obj.key}")
        return urls

    def delete_evidence(self, dispute_id: str, filename: str) -> None:
        """Delete a specific evidence file (reversible — OSS versioning enabled in prod)."""
        bucket = self._get_bucket()
        object_key = f"evidence/{dispute_id}/{filename}"
        bucket.delete_object(object_key)

    def get_signed_url(self, dispute_id: str, filename: str, expiry_seconds: int = 3600) -> str:
        """Generate a time-limited signed URL for secure evidence sharing."""
        bucket = self._get_bucket()
        object_key = f"evidence/{dispute_id}/{filename}"
        return bucket.sign_url("GET", object_key, expiry_seconds)


# ── Local Fallback ─────────────────────────────────────────────────────────────

class LocalEvidenceStore:
    """
    Filesystem-backed evidence store for offline development.
    Implements the same interface as OSSEvidenceStore.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path("./data/evidence")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def upload_evidence(self, dispute_id: str, filename: str, data: bytes, content_type: str = "image/jpeg") -> str:
        dispute_dir = self.base_dir / dispute_id
        dispute_dir.mkdir(exist_ok=True)
        (dispute_dir / filename).write_bytes(data)
        return f"file://{(dispute_dir / filename).resolve()}"

    def download_evidence(self, dispute_id: str, filename: str) -> bytes:
        return (self.base_dir / dispute_id / filename).read_bytes()

    def list_evidence(self, dispute_id: str) -> list[str]:
        dispute_dir = self.base_dir / dispute_id
        if not dispute_dir.exists():
            return []
        return [f"file://{p.resolve()}" for p in dispute_dir.iterdir()]

    def delete_evidence(self, dispute_id: str, filename: str) -> None:
        (self.base_dir / dispute_id / filename).unlink(missing_ok=True)

    def get_signed_url(self, dispute_id: str, filename: str, expiry_seconds: int = 3600) -> str:
        return self.upload_evidence.__doc__ and self.list_evidence(dispute_id)[0] or ""


# ── Factory ────────────────────────────────────────────────────────────────────

def get_evidence_store():
    """
    Returns OSSEvidenceStore if Alibaba Cloud credentials are configured,
    otherwise falls back to LocalEvidenceStore for offline development.
    """
    if os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"):
        try:
            import oss2  # noqa: F401
            logger.info("Using Alibaba Cloud OSS for evidence storage")
            return OSSEvidenceStore()
        except ImportError:
            logger.warning("oss2 not installed — falling back to local storage")
    logger.info("Using local filesystem for evidence storage (dev mode)")
    return LocalEvidenceStore()


# ── RDS (PostgreSQL) connection path ──────────────────────────────────────────

def get_rds_database_url() -> str:
    """
    Build an async SQLAlchemy URL for Alibaba Cloud RDS (PostgreSQL).
    Used when DATABASE_URL env var points to RDS in production.

    Example RDS URL:
    postgresql+asyncpg://liquet_user:password@rm-xxxx.pg.rds.aliyuncs.com:5432/liquet_prod
    """
    host = os.environ.get("RDS_HOST", "rm-xxxx.pg.rds.aliyuncs.com")
    port = os.environ.get("RDS_PORT", "5432")
    user = os.environ.get("RDS_USER", "liquet_user")
    password = os.environ.get("RDS_PASSWORD", "")
    dbname = os.environ.get("RDS_DBNAME", "liquet_prod")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"


# ── Demo / smoke test ─────────────────────────────────────────────────────────

def demo_oss_integration() -> None:
    """
    Demonstrates OSS upload/download cycle.
    Requires valid ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET.
    """
    print("\n── Alibaba Cloud OSS Integration Demo ──")
    store = get_evidence_store()

    # Upload a synthetic evidence file
    dispute_id = "DEMO-DISPUTE-001"
    filename = "test_evidence.txt"
    data = b"Sample dispute evidence: item color is grey, listing says brown."

    print(f"Uploading evidence for {dispute_id}...")
    url = store.upload_evidence(dispute_id, filename, data, content_type="text/plain")
    print(f"Uploaded to: {url}")

    # Download it back
    print("Downloading evidence...")
    downloaded = store.download_evidence(dispute_id, filename)
    assert downloaded == data, "Download mismatch!"
    print(f"Downloaded {len(downloaded)} bytes — content verified ✓")

    # List evidence
    urls = store.list_evidence(dispute_id)
    print(f"Evidence files for {dispute_id}: {urls}")
    print("── OSS demo complete ──\n")


if __name__ == "__main__":
    demo_oss_integration()
