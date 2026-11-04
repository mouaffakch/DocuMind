import os
import hashlib
import re
from typing import List, Dict, Optional, Generator, Tuple

# Directories to ignore
IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".idea",
    ".vscode",
    "target",
    "vendor",
    "bin",
    "obj",
    ".gradle",
}

# Binary and non-code file extensions to ignore
IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".pyc", ".pyo", ".class", ".jar",
    ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".wav", ".avi",
    ".sqlite", ".sqlite3", ".db",
    ".min.js", ".min.css", ".map",
}

# Secret / sensitive filename patterns
SECRET_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),
    re.compile(r"^.*id_rsa.*$", re.IGNORECASE),
    re.compile(r"^.*\.(pem|key|pkcs12|pfx|crt|cer)$", re.IGNORECASE),
    re.compile(r"^.*credentials.*\.json$", re.IGNORECASE),
]

# Language mapping by file extension
LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".java": "java",
    ".go": "go",
    ".md": "markdown",
    ".rst": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
}

MAX_FILE_SIZE_BYTES = 500 * 1024  # 500 KB limit per file to avoid OOM on bundles


class ScannedFile:
    """Represents a discovered and validated code or documentation file."""
    def __init__(self, relative_path: str, full_path: str, language: str, content: str, size_bytes: int, sha256_hash: str):
        self.relative_path = relative_path
        self.full_path = full_path
        self.language = language
        self.content = content
        self.size_bytes = size_bytes
        self.sha256_hash = sha256_hash


class FileScanner:
    """Scans and filters repository files, detecting languages and excluding secrets/binaries."""

    @staticmethod
    def is_secret_file(filename: str) -> bool:
        """Check if filename matches known secret file patterns."""
        for pattern in SECRET_PATTERNS:
            if pattern.match(filename):
                return True
        return False

    @staticmethod
    def is_binary_file(filepath: str) -> bool:
        """Check if file contains binary / null bytes in its initial chunk."""
        try:
            with open(filepath, "tr", encoding="utf-8") as check_file:
                check_file.read(1024)
                return False
        except (UnicodeDecodeError, PermissionError):
            return True

    @classmethod
    def scan_directory(cls, repo_root_dir: str) -> List[ScannedFile]:
        """Walks the repository directory and yields clean, validated source files."""
        scanned_files: List[ScannedFile] = []

        if not os.path.exists(repo_root_dir):
            return scanned_files

        for root, dirs, files in os.walk(repo_root_dir):
            # Prune ignored directories in-place so os.walk does not recurse into them
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES and not d.startswith(".git")]

            for file_name in files:
                full_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(full_path, repo_root_dir).replace("\\", "/")

                # 1. Skip secret patterns
                if cls.is_secret_file(file_name):
                    continue

                # 2. Skip ignored extensions
                _, ext = os.path.splitext(file_name.lower())
                if ext in IGNORED_EXTENSIONS:
                    continue

                # 3. Check language support
                language = LANGUAGE_EXTENSIONS.get(ext)
                if not language:
                    # Not a tracked language extension
                    continue

                # 4. Check file size
                try:
                    file_size = os.path.getsize(full_path)
                    if file_size > MAX_FILE_SIZE_BYTES or file_size == 0:
                        continue
                except OSError:
                    continue

                # 5. Check if binary
                if cls.is_binary_file(full_path):
                    continue

                # 6. Read text content and compute SHA256
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()

                    scanned_files.append(
                        ScannedFile(
                            relative_path=relative_path,
                            full_path=full_path,
                            language=language,
                            content=content,
                            size_bytes=file_size,
                            sha256_hash=sha256,
                        )
                    )
                except Exception:
                    continue

        return scanned_files
