"""
Document Parsing Services
=========================

文档解析服务，支持多种格式并智能分块。

Provides document parsing for multiple file formats with intelligent text
chunking that preserves paragraph and sentence boundaries. The ParserFactory
creates the appropriate parser based on document kind.

Supported formats / 支持的文件格式::

    Format      Parser Class    Dependencies
    ───────     ─────────────   ────────────
    PDF         PDFParser       PyMuPDF (fitz)
    Markdown    MarkdownParser  (built-in, re-based)
    TXT         TxtParser       (built-in)
    DOC/DOCX    WordParser      python-docx

Chunking strategy / 分块策略::

    1. Try to split by paragraph boundaries (\\n\\n)
    2. If no paragraphs, split by sentence boundaries (.!?)
    3. For oversized paragraphs, split by sentences, then words
    4. Each chunk respects the configured chunk_size limit

Usage / 用法示例::

    parser = ParserFactory.create_parser("pdf", chunk_size=2000)
    full_text, chunks = parser.parse("/path/to/document.pdf")
"""
import re
from typing import List, Dict, Any
from pathlib import Path
import fitz  # PyMuPDF
from models.document import Chunk


class Parser:
    """
    Abstract base parser with smart chunking logic.
    抽象基础解析器，包含智能分块逻辑。

    Subclasses must implement parse() which returns (full_text, chunks).
    The _smart_chunk() method provides intelligent text segmentation that
    respects natural text boundaries.

    Attributes:
        chunk_size:  Maximum characters per chunk / 每个文本块的最大字符数

    Args:
        chunk_size: Maximum chars per chunk (default: 2000) / 每块最大字符数
    """

    def __init__(self, chunk_size: int = 2000):
        self.chunk_size = chunk_size

    def parse(self, file_path: str) -> tuple[str, List[Chunk]]:
        """
        Parse document and return full text plus chunked segments.
        解析文档，返回全文和分块后的文本段。

        Args:
            file_path:  Path to the document file / 文档文件路径

        Returns:
            Tuple of (full_text, list_of_chunks)
            元组：(完整文本, 文本块列表)

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    def _smart_chunk(
        self,
        text: str,
        doc_id: str,
        base_chunk_id: str,
        meta: Dict[str, Any],
    ) -> List[Chunk]:
        """
        Intelligently chunk text by size while preserving natural boundaries.
        智能分块，在限制大小的同时保留自然边界。

        Chunking algorithm / 分块算法::

            1. If text fits in one chunk → return as single chunk
            2. Split by paragraphs → accumulate paragraphs into chunks
            3. If a paragraph is too large → split by sentences
            4. If a sentence is too large → split by words
            5. Each chunk stays under chunk_size

        Args:
            text:           Text to chunk / 待分块的文本
            doc_id:         Document ID for chunk metadata / 文档 ID
            base_chunk_id:  Base ID prefix for chunks / 块 ID 前缀
            meta:           Base metadata applied to all chunks / 基础元数据

        Returns:
            List of Chunk objects / 文本块对象列表
        """
        if not text.strip():
            return []

        # If text fits in one chunk, return as-is / 如果文本足够小，直接返回
        if len(text) <= self.chunk_size:
            return [
                Chunk(
                    doc_id=doc_id,
                    chunk_id=base_chunk_id,
                    text=text.strip(),
                    meta=meta.copy(),
                )
            ]

        # Split by paragraphs first / 首先按段落分割
        paragraphs = [
            p.strip()
            for p in text.split('\n\n')
            if p.strip() and len(p.strip()) >= 10
        ]

        if not paragraphs:
            # Fallback: split by sentences / 后备方案：按句子分割
            sentences = re.split(r'[.!?。！？]\s+', text)
            paragraphs = [
                s.strip()
                for s in sentences
                if s.strip() and len(s.strip()) >= 10
            ]

        current_chunk = []
        current_size = 0
        chunk_idx = 0

        for para in paragraphs:
            para_size = len(para)

            # Handle paragraphs that exceed chunk_size / 处理超长段落
            if para_size > self.chunk_size:
                # Save current accumulated chunk first / 先保存当前累积的块
                if current_chunk:
                    chunks.append(
                        Chunk(
                            doc_id=doc_id,
                            chunk_id=f"{base_chunk_id}_{chunk_idx}",
                            text="\n\n".join(current_chunk),
                            meta=meta.copy(),
                        )
                    )
                    chunk_idx += 1
                    current_chunk = []
                    current_size = 0

                # Split large paragraph by sentences / 按句子分割超长段落
                sentences = re.split(r'[.!?。！？]\s+', para)
                for sent in sentences:
                    sent = sent.strip()
                    if not sent or len(sent) < 10:
                        continue

                    if len(sent) > self.chunk_size:
                        # Even sentence too long — split by words
                        # 句子还是太长 — 按单词分割
                        words = sent.split()
                        current_sent = []
                        current_sent_size = 0

                        for word in words:
                            word_size = len(word) + 1  # +1 for space
                            if (
                                current_sent_size + word_size
                                > self.chunk_size
                                and current_sent
                            ):
                                chunks.append(
                                    Chunk(
                                        doc_id=doc_id,
                                        chunk_id=(
                                            f"{base_chunk_id}_{chunk_idx}"
                                        ),
                                        text=" ".join(current_sent),
                                        meta=meta.copy(),
                                    )
                                )
                                chunk_idx += 1
                                current_sent = []
                                current_sent_size = 0

                            current_sent.append(word)
                            current_sent_size += word_size

                        if current_sent:
                            current_chunk.append(" ".join(current_sent))
                            current_size += current_sent_size
                    else:
                        # Sentence fits — add to current chunk
                        # 句子可以放入当前块
                        if (
                            current_size + len(sent) + 2
                            > self.chunk_size
                            and current_chunk
                        ):
                            chunks.append(
                                Chunk(
                                    doc_id=doc_id,
                                    chunk_id=(
                                        f"{base_chunk_id}_{chunk_idx}"
                                    ),
                                    text="\n\n".join(current_chunk),
                                    meta=meta.copy(),
                                )
                            )
                            chunk_idx += 1
                            current_chunk = [sent]
                            current_size = len(sent)
                        else:
                            current_chunk.append(sent)
                            current_size += len(sent) + 2
            else:
                # Normal paragraph — add to current chunk if it fits
                # 普通段落 — 如果能放得下则加入当前块
                if (
                    current_size + para_size + 2 > self.chunk_size
                    and current_chunk
                ):
                    chunks.append(
                        Chunk(
                            doc_id=doc_id,
                            chunk_id=f"{base_chunk_id}_{chunk_idx}",
                            text="\n\n".join(current_chunk),
                            meta=meta.copy(),
                        )
                    )
                    chunk_idx += 1
                    current_chunk = [para]
                    current_size = para_size
                else:
                    current_chunk.append(para)
                    current_size += para_size + 2

        # Don't forget the last chunk / 别忘了最后一个块
        if current_chunk:
            chunks.append(
                Chunk(
                    doc_id=doc_id,
                    chunk_id=f"{base_chunk_id}_{chunk_idx}",
                    text="\n\n".join(current_chunk),
                    meta=meta.copy(),
                )
            )

        return chunks


class PDFParser(Parser):
    """
    PDF parser using PyMuPDF (fitz).
    基于 PyMuPDF 的 PDF 解析器。

    Extracts text page by page, then applies smart chunking within each page.
    Page numbers are preserved in chunk metadata for provenance tracking.
    """

    def parse(self, file_path: str) -> tuple[str, List[Chunk]]:
        """
        Parse a PDF file by extracting text from each page.
        逐页提取 PDF 文件文本。

        Args:
            file_path:  Path to PDF file / PDF 文件路径

        Returns:
            Tuple of (full_text, chunks_with_page_metadata)
            元组：(完整文本, 带页码元数据的文本块)
        """
        doc = fitz.open(file_path)
        chunks = []
        full_text_parts = []
        doc_id = Path(file_path).stem

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            if not text.strip():
                continue

            full_text_parts.append(text)

            # Smart chunk within each page / 每页内智能分块
            page_chunks = self._smart_chunk(
                text=text,
                doc_id=doc_id,
                base_chunk_id=f"c_{page_num}",
                meta={
                    "page": page_num + 1,
                    "section": None,
                    "offset": [0, len(text)],
                },
            )
            chunks.extend(page_chunks)

        doc.close()
        full_text = "\n\n".join(full_text_parts)
        return full_text, chunks


class MarkdownParser(Parser):
    """
    Markdown parser with section-aware chunking.
    基于 Markdown 的解析器，支持按章节分块。

    Splits content by markdown headers (# ## ### etc.) and preserves
    section information in chunk metadata.
    """

    def parse(self, file_path: str) -> tuple[str, List[Chunk]]:
        """
        Parse a Markdown file, splitting by headers.
        解析 Markdown 文件，按标题分割。

        Args:
            file_path:  Path to Markdown file / Markdown 文件路径

        Returns:
            Tuple of (full_content, chunks_with_section_metadata)
            元组：(完整内容, 带章节元数据的文本块)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        chunks = []
        doc_id = Path(file_path).stem

        # Split by headers / 按标题分割
        sections = re.split(r'\n(#{1,6}\s+.+?)\n', content)

        current_section = None
        chunk_idx = 0

        for i, section in enumerate(sections):
            if i == 0:
                # Content before first header / 第一个标题前的内容
                if section.strip():
                    section_chunks = self._smart_chunk(
                        text=section.strip(),
                        doc_id=doc_id,
                        base_chunk_id=f"c_{chunk_idx}",
                        meta={
                            "page": 1,
                            "section": None,
                            "offset": [0, len(section)],
                        },
                    )
                    chunks.extend(section_chunks)
                    chunk_idx += len(section_chunks)
                continue

            if section.startswith('#'):
                # This is a header line / 这是标题行
                current_section = section.strip()
            else:
                # This is content under a header / 这是标题下的内容
                if section.strip():
                    section_chunks = self._smart_chunk(
                        text=section.strip(),
                        doc_id=doc_id,
                        base_chunk_id=f"c_{chunk_idx}",
                        meta={
                            "page": 1,
                            "section": current_section,
                            "offset": [0, len(section)],
                        },
                    )
                    chunks.extend(section_chunks)
                    chunk_idx += len(section_chunks)

        return content, chunks


class TxtParser(Parser):
    """
    Plain text file parser.
    纯文本文件解析器。

    Applies smart chunking directly to the entire text content.
    """

    def parse(self, file_path: str) -> tuple[str, List[Chunk]]:
        """
        Parse a plain text file.
        解析纯文本文件。

        Args:
            file_path:  Path to TXT file / 文本文件路径

        Returns:
            Tuple of (full_content, chunks) / 元组：(完整内容, 文本块列表)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        doc_id = Path(file_path).stem

        chunks = self._smart_chunk(
            text=content,
            doc_id=doc_id,
            base_chunk_id="c",
            meta={
                "page": 1,
                "section": None,
                "offset": [0, len(content)],
            },
        )

        return content, chunks


class WordParser(Parser):
    """
    Word document parser (DOC/DOCX) using python-docx.
    基于 python-docx 的 Word 文档解析器。

    Processes paragraphs sequentially, tracking section changes via
    paragraph style names.
    """

    def parse(self, file_path: str) -> tuple[str, List[Chunk]]:
        """
        Parse a Word document.
        解析 Word 文档。

        Requires python-docx library. Raises ImportError if not installed.

        Args:
            file_path:  Path to DOC/DOCX file / Word 文件路径

        Returns:
            Tuple of (full_text, chunks_with_section_metadata)
            元组：(完整文本, 带章节元数据的文本块)

        Raises:
            ImportError: If python-docx is not installed
        """
        try:
            import docx
        except ImportError:
            raise ImportError(
                "python-docx is required for Word document parsing. "
                "Install with: pip install python-docx"
            )

        doc = docx.Document(file_path)
        chunks = []
        full_text_parts = []
        doc_id = Path(file_path).stem

        all_text = []
        current_section = None

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text or len(text) < 10:
                continue

            section = para.style.name if para.style else None
            if section != current_section:
                # Section boundary detected / 检测到章节边界
                if all_text:
                    section_text = "\n\n".join(all_text)
                    full_text_parts.append(section_text)
                    section_chunks = self._smart_chunk(
                        text=section_text,
                        doc_id=doc_id,
                        base_chunk_id=f"c_{len(chunks)}",
                        meta={
                            "page": 1,
                            "section": current_section,
                            "offset": [0, len(section_text)],
                        },
                    )
                    chunks.extend(section_chunks)
                    all_text = []
                current_section = section

            all_text.append(text)

        # Process remaining text / 处理剩余文本
        if all_text:
            section_text = "\n\n".join(all_text)
            full_text_parts.append(section_text)
            section_chunks = self._smart_chunk(
                text=section_text,
                doc_id=doc_id,
                base_chunk_id=f"c_{len(chunks)}",
                meta={
                    "page": 1,
                    "section": current_section,
                    "offset": [0, len(section_text)],
                },
            )
            chunks.extend(section_chunks)

        full_text = "\n\n".join(full_text_parts)
        return full_text, chunks


class ParserFactory:
    """
    Factory for creating parsers based on document type.
    根据文档类型创建解析器的工厂类。

    Maps document kind strings to parser classes and creates instances
    with the configured chunk size.

    Usage / 用法示例::

        parser = ParserFactory.create_parser("pdf", chunk_size=2000)
        parser = ParserFactory.create_parser("md", chunk_size=1000)
    """

    @staticmethod
    def create_parser(kind: str, chunk_size: int = 2000) -> Parser:
        """
        Create a parser for the given document type.
        为指定文档类型创建解析器。

        Args:
            kind:       Document type identifier / 文档类型标识符
                       (pdf, md, markdown, txt, word)
            chunk_size: Maximum characters per chunk / 每块最大字符数

        Returns:
            Parser instance configured for the document type
            配置好的解析器实例

        Raises:
            ValueError: If the document kind is not supported
                        如果文档类型不受支持
        """
        parsers = {
            "pdf": PDFParser,
            "md": MarkdownParser,
            "markdown": MarkdownParser,
            "txt": TxtParser,
            "word": WordParser,
        }

        parser_class = parsers.get(kind.lower())
        if not parser_class:
            raise ValueError(f"Unsupported document kind: {kind}")

        return parser_class(chunk_size=chunk_size)
