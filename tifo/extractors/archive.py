from pathlib import Path
import tarfile
import zipfile

try:
    import py7zr
except ImportError:  # optional dependency — .7z just falls back to filename-only
    py7zr = None

from tifo.extractors.models import ExtractedFile

MAX_MEMBERS_LISTED = 20

# tarfile transparently handles gzip/bzip2/xz compression, so one opener covers
# .tar, .tar.gz/.tgz, .tar.bz2, .tar.xz. Single-file .gz (not a tar) is caught
# by tarfile.ReadError and falls back to content=None.
_TAR_SUFFIXES = {".tar", ".gz", ".tgz", ".bz2", ".xz"}


def _clean_members(names: list[str]) -> list[str]:
    """Drop directory-only entries and macOS/zip metadata noise."""
    cleaned = []
    for name in names:
        norm = name.rstrip("/")
        if not norm:
            continue
        base = norm.rsplit("/", 1)[-1]
        if not base:  # pure directory entry
            continue
        if base == ".DS_Store" or norm.startswith("__MACOSX"):
            continue
        cleaned.append(norm)
    return cleaned


def _list_zip(file_path: Path) -> list[str] | None:
    try:
        with zipfile.ZipFile(file_path) as zf:
            # file-only entries (dirs end with "/")
            return [i.filename for i in zf.infolist() if not i.is_dir()]
    except (zipfile.BadZipFile, OSError):
        return None


def _list_tar(file_path: Path) -> list[str] | None:
    try:
        with tarfile.open(file_path) as tf:
            return [m.name for m in tf.getmembers() if m.isfile()]
    except (tarfile.ReadError, tarfile.CompressionError, OSError, EOFError):
        return None


def _list_7z(file_path: Path) -> list[str] | None:
    # py7zr is optional; if it isn't installed, .7z falls back to filename-only.
    if py7zr is None:
        return None
    try:
        with py7zr.SevenZipFile(file_path, mode="r") as zf:
            # Header-encrypted archives can't be listed without the password.
            if zf.needs_password():
                return None
            # list() returns FileInfo objects; keep only files, not directories.
            return [info.filename for info in zf.list() if not info.is_directory]
    except (py7zr.exceptions.Bad7zFile, py7zr.exceptions.PasswordRequired, OSError, EOFError, ValueError):
        return None


def _synthesize_content(members: list[str]) -> str:
    """Build a short natural-language description from member file names."""
    total = len(members)
    shown = _clean_members(members)[:MAX_MEMBERS_LISTED]
    listing = ", ".join(shown)
    return f"Archive containing {total} files: {listing}"


def extract_archive(file_path: Path) -> ExtractedFile:
    """Describe an archive by listing its member files.

    Returns content=None (not an exception) for encrypted, corrupt, or
    unsupported archive formats so a single bad archive never breaks a run.
    .7z is supported when the optional ``py7zr`` package is installed (falls
    back to filename-only otherwise). .rar needs an external system binary and
    is intentionally unsupported — those fall back to filename-based naming.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".zip":
        members = _list_zip(file_path)
    elif suffix in _TAR_SUFFIXES:
        members = _list_tar(file_path)
    elif suffix == ".7z":
        members = _list_7z(file_path)
    else:
        members = None

    if not members:
        # Unsupported format, empty archive, or read failure.
        return ExtractedFile(content=None, summary=None, metadata={})

    cleaned = _clean_members(members)
    if not cleaned:
        return ExtractedFile(content=None, summary=None, metadata={})

    return ExtractedFile(
        content=_synthesize_content(cleaned),
        summary=None,
        metadata={
            "member_count": len(cleaned),
            "members": cleaned[:MAX_MEMBERS_LISTED],
        },
    )
