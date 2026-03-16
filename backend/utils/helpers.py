"""
Utility helpers - file validation, sanitization, logging setup
"""
import os
import re
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE_MB = 16


def allowed_file(filename: str) -> bool:
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def file_size_ok(filepath: str) -> bool:
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    return size_mb <= MAX_FILE_SIZE_MB


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from filename."""
    name, ext = os.path.splitext(filename)
    name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
    name = name[:60]  # Limit length
    return f"{name}{ext.lower()}"


def unique_filename(original: str) -> str:
    """Generate a unique filename using timestamp hash."""
    ts = datetime.utcnow().isoformat()
    h = hashlib.md5(f"{original}{ts}".encode()).hexdigest()[:8]
    _, ext = os.path.splitext(original)
    return f"{h}_{sanitize_filename(original)}"


def setup_logging(log_dir: str = '../logs', level=logging.INFO):
    """Configure application-wide logging."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
