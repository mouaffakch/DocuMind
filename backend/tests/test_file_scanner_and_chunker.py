import os
import tempfile
import pytest
from app.ingestion.file_scanner import FileScanner
from app.ingestion.ast_parser import ASTParser
from app.ingestion.chunker import ASTAwareChunker


def test_file_scanner_filters_secrets_and_vendor_dirs():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create valid source file
        src_dir = os.path.join(tmp_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        main_py = os.path.join(src_dir, "main.py")
        with open(main_py, "w", encoding="utf-8") as f:
            f.write("def run():\n    print('Hello World')\n")

        # Create ignored directory (node_modules)
        nm_dir = os.path.join(tmp_dir, "node_modules", "package")
        os.makedirs(nm_dir, exist_ok=True)
        with open(os.path.join(nm_dir, "index.js"), "w", encoding="utf-8") as f:
            f.write("console.log('vendor');")

        # Create secret file (.env)
        with open(os.path.join(tmp_dir, ".env"), "w", encoding="utf-8") as f:
            f.write("DATABASE_PASSWORD=supersecret")

        # Create binary file
        with open(os.path.join(tmp_dir, "image.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

        scanned = FileScanner.scan_directory(tmp_dir)

        paths = [s.relative_path for s in scanned]
        assert "src/main.py" in paths
        assert not any("node_modules" in p for p in paths)
        assert not any(".env" in p for p in paths)
        assert not any("image.png" in p for p in paths)


def test_ast_aware_chunking_with_context():
    code = """def login_user(username: str) -> bool:
    print(f"Logging in {username}")
    return True

def logout_user() -> None:
    print("Logged out")
"""
    symbols = ASTParser.parse_code(code, "python")
    from app.ingestion.file_scanner import ScannedFile
    scanned_file = ScannedFile(
        relative_path="auth/login.py",
        full_path="/tmp/auth/login.py",
        language="python",
        content=code,
        size_bytes=len(code),
        sha256_hash="dummyhash",
    )

    chunks = ASTAwareChunker.chunk_file(scanned_file, symbols)
    assert len(chunks) >= 2
    assert any("login_user" in c.content for c in chunks)
    assert any("logout_user" in c.content for c in chunks)
    assert all(c.file_path == "auth/login.py" for c in chunks)
    assert all("# File: auth/login.py" in c.content for c in chunks)
