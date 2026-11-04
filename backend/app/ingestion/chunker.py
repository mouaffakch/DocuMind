import uuid
from typing import List, Optional
from app.ingestion.file_scanner import ScannedFile
from app.ingestion.ast_parser import ParsedSymbol, ASTParser


class CodeChunk:
    """Represents an intelligent, context-enriched segment of source code for vector indexing."""
    def __init__(
        self,
        chunk_id: str,
        file_path: str,
        language: str,
        start_line: int,
        end_line: int,
        content: str,
        symbol_name: Optional[str] = None,
        symbol_type: Optional[str] = None,
    ):
        self.chunk_id = chunk_id
        self.file_path = file_path
        self.language = language
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.symbol_name = symbol_name
        self.symbol_type = symbol_type


class ASTAwareChunker:
    """Chunker that preserves syntactic code boundaries (functions, methods, classes) with context."""

    DEFAULT_WINDOW_LINES = 60
    DEFAULT_OVERLAP_LINES = 15

    @classmethod
    def chunk_file(
        cls,
        scanned_file: ScannedFile,
        symbols: Optional[List[ParsedSymbol]] = None,
    ) -> List[CodeChunk]:
        """Convert a scanned file into an array of context-enriched CodeChunks."""
        chunks: List[CodeChunk] = []
        lines = scanned_file.content.splitlines()
        total_lines = len(lines)

        if total_lines == 0:
            return chunks

        # 1. If AST symbols are available, chunk by symbol
        if symbols and len(symbols) > 0:
            covered_ranges = set()

            for symbol in symbols:
                # 1-indexed to 0-indexed slicing
                s_idx = max(0, symbol.start_line - 1)
                e_idx = min(total_lines, symbol.end_line)
                
                snippet_lines = lines[s_idx:e_idx]
                if not snippet_lines:
                    continue

                # Add contextual breadcrumb header
                comment_prefix = "//" if scanned_file.language in ("javascript", "typescript", "go", "java") else "#"
                breadcrumb = (
                    f"{comment_prefix} File: {scanned_file.relative_path} | "
                    f"Symbol: {symbol.name} ({symbol.symbol_type.value}) | "
                    f"Lines: {symbol.start_line}-{symbol.end_line}\n"
                )
                chunk_text = breadcrumb + "\n".join(snippet_lines)

                chunks.append(
                    CodeChunk(
                        chunk_id=str(uuid.uuid4()),
                        file_path=scanned_file.relative_path,
                        language=scanned_file.language,
                        start_line=symbol.start_line,
                        end_line=symbol.end_line,
                        content=chunk_text,
                        symbol_name=symbol.name,
                        symbol_type=symbol.symbol_type.value,
                    )
                )

                for l in range(symbol.start_line, symbol.end_line + 1):
                    covered_ranges.add(l)

            # If there is substantial remaining code (e.g. file header, imports, top-level code)
            uncovered_lines = [i for i in range(1, total_lines + 1) if i not in covered_ranges]
            if len(uncovered_lines) > 20:
                # Add header/imports chunk
                header_end = min(35, total_lines)
                header_text = "\n".join(lines[:header_end])
                comment_prefix = "//" if scanned_file.language in ("javascript", "typescript", "go", "java") else "#"
                breadcrumb = f"{comment_prefix} File: {scanned_file.relative_path} | Top-level imports & module init | Lines: 1-{header_end}\n"
                chunks.append(
                    CodeChunk(
                        chunk_id=str(uuid.uuid4()),
                        file_path=scanned_file.relative_path,
                        language=scanned_file.language,
                        start_line=1,
                        end_line=header_end,
                        content=breadcrumb + header_text,
                        symbol_name="module_header",
                        symbol_type="module",
                    )
                )

            return chunks

        # 2. Fallback: Sliding window chunker for Markdown or non-AST files
        start = 0
        while start < total_lines:
            end = min(start + cls.DEFAULT_WINDOW_LINES, total_lines)
            snippet = "\n".join(lines[start:end])
            
            comment_prefix = "//" if scanned_file.language in ("javascript", "typescript", "go", "java") else "#"
            breadcrumb = f"{comment_prefix} File: {scanned_file.relative_path} | Lines: {start + 1}-{end}\n"

            chunks.append(
                CodeChunk(
                    chunk_id=str(uuid.uuid4()),
                    file_path=scanned_file.relative_path,
                    language=scanned_file.language,
                    start_line=start + 1,
                    end_line=end,
                    content=breadcrumb + snippet,
                    symbol_name=None,
                    symbol_type="text_block",
                )
            )

            if end >= total_lines:
                break
            start += (cls.DEFAULT_WINDOW_LINES - cls.DEFAULT_OVERLAP_LINES)

        return chunks
