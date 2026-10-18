from pathlib import Path

from PIL import Image, ExifTags, UnidentifiedImageError

from tifo.extractors.models import ExtractedFile

# Reverse lookups from human-readable tag name -> numeric EXIF id.
_TAG_IDS = {name: num for num, name in ExifTags.TAGS.items()}
_GPS_IDS = {name: num for num, name in ExifTags.GPSTAGS.items()}

_DATETIME_TAGS = ("DateTimeOriginal", "DateTimeDigitized", "DateTime")


def _normalize_datetime(raw: str) -> str | None:
    """EXIF stores dates as 'YYYY:MM:DD HH:MM:SS'. Return 'YYYY-MM-DD' or None."""
    if not raw:
        return None
    date_part = raw.strip().split(" ", 1)[0]  # drop the time
    pieces = date_part.split(":")
    if len(pieces) != 3 or not all(pieces):
        return None
    year, month, day = pieces
    return f"{year}-{month}-{day}"


def _to_degrees(dms, ref: str | None) -> float | None:
    """Convert EXIF GPS (degrees, minutes, seconds) rationals to decimal degrees."""
    try:
        d, m, s = (float(x) for x in dms)
    except (TypeError, ValueError):
        return None
    decimal = d + m / 60.0 + s / 3600.0
    if ref in ("S", "W"):
        decimal = -decimal
    return round(decimal, 6)


def _extract_gps(exif) -> tuple[float, float] | None:
    """Pull (lat, lon) decimal degrees from the GPS IFD, or None."""
    gps_ifd_id = _TAG_IDS.get("GPSInfo")
    if gps_ifd_id is None:
        return None
    try:
        gps = exif.get_ifd(gps_ifd_id)
    except (KeyError, AttributeError):
        gps = None
    if not gps:
        return None

    lat = _to_degrees(gps.get(_GPS_IDS["GPSLatitude"]), gps.get(_GPS_IDS["GPSLatitudeRef"]))
    lon = _to_degrees(gps.get(_GPS_IDS["GPSLongitude"]), gps.get(_GPS_IDS["GPSLongitudeRef"]))
    if lat is None or lon is None:
        return None
    return lat, lon


def extract_image(file_path: Path) -> ExtractedFile:
    """Describe an image from its EXIF metadata (date / device / location).

    EXIF carries *when / where / what-device*, never the image subject — that
    needs a vision model. This always returns whatever structured fields are
    available (dimensions, and when present: date_taken, device, gps) in
    `metadata` so the image-aware namer never has to work from nothing. The
    human-readable `content` string is only built from descriptive signals
    (date/location); device alone stays out of `content` but is kept in
    `metadata`. Never raises — unreadable/truncated images return empty.
    """
    try:
        with Image.open(file_path) as img:
            exif = img.getexif()
            dimensions = img.size  # (width, height) — available without EXIF
    except (UnidentifiedImageError, OSError, ValueError):
        return ExtractedFile(content=None, summary=None, metadata={})

    meta: dict = {}
    if dimensions:
        meta["dimensions"] = {"width": dimensions[0], "height": dimensions[1]}

    # EXIF may be entirely absent (common for PNGs/screenshots). We still return
    # dimensions so the namer has *something* real to work with.
    date_str = None
    device = None
    gps = None

    if exif:
        # Capture date — most useful field for organizing photos.
        for tag in _DATETIME_TAGS:
            tag_id = _TAG_IDS.get(tag)
            if tag_id is not None and exif.get(tag_id):
                date_str = _normalize_datetime(str(exif.get(tag_id)))
                if date_str:
                    break

        # Capturing device (camera make/model).
        make = str(exif.get(_TAG_IDS.get("Make", -1), "")).strip().strip("\x00")
        model = str(exif.get(_TAG_IDS.get("Model", -1), "")).strip().strip("\x00")
        device = " ".join(p for p in (make, model) if p) or None

        gps = _extract_gps(exif)

    # Always record whatever structured fields are present — the namer decides
    # how to use them. This is the key fix: we never discard device-only EXIF.
    if date_str:
        meta["date_taken"] = date_str
    if device:
        meta["device"] = device
    if gps:
        meta["gps"] = {"lat": gps[0], "lon": gps[1]}

    # Build a human-readable `content` string only from the *descriptive* signals
    # (date/location) — this feeds semantic classification and acts as a readable
    # summary. Device alone is NOT enough to form content (it would mislead a
    # "what is this about?" reader), but it IS preserved in metadata above so the
    # image-aware namer can still use it. When there's no date/location, content
    # stays None and naming falls back to the labeled-metadata prompt + filename.
    parts: list[str] = []
    if date_str:
        parts.append(f"taken on {date_str}")
    if gps:
        parts.append(f"location {gps[0]}, {gps[1]}")
    if device and parts:  # only append device as a qualifier alongside date/gps
        parts.append(f"camera {device}")

    content = ("Photo " + ", ".join(parts)) if parts else None
    return ExtractedFile(content=content, summary=None, metadata=meta)
