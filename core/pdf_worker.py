"""Isolated text extraction. No credentials, disk writes, or document logging."""
import io
import json
import logging
import sys


def extract(data: bytes) -> dict:
    from pypdf import PdfReader
    try:
        # Tolerate recoverable PDF formatting issues, while keeping extraction
        # isolated and bounded. This does not bypass encryption or size limits.
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted:
            return {"error": "encrypted"}
        if len(reader.pages) > 50:
            return {"error": "page_limit"}
        pages, count = [], 0
        for page in reader.pages:
            text = page.extract_text() or ""
            count += len(text)
            if count > 100_000:
                return {"error": "text_limit"}
            pages.append(text)
        if not any(any(c.isalnum() for c in text) for text in pages):
            return {"error": "no_text"}
        return {"pages": pages}
    except Exception:
        # Fixed codes explain the failure without exposing document contents,
        # parser exception details or local paths to the interface.
        return {"error": "parse_error"}


def main():
    logging.disable(logging.CRITICAL)
    if sys.platform == "linux":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    data = sys.stdin.buffer.read(10 * 1024 * 1024 + 1)
    payload = {"error": "upload_limit"} if len(data) > 10 * 1024 * 1024 else extract(data)
    sys.stdout.write(json.dumps(payload))


if __name__ == "__main__":
    main()
