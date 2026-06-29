"""
File Storage Utilities
======================

文件存储工具模块，提供文件保存、校验和计算和去重管理功能。

Provides low-level file I/O operations with SHA256 checksum-based
deduplication. Files are stored with a checksum prefix to avoid
collisions and enable content-addressable retrieval.

Usage / 用法示例::

    storage = Storage()
    file_path, checksum = await storage.save_file(content, "doc.pdf")
    existing_path = storage.file_exists(checksum)  # Dedup check / 去重检查
    deleted = storage.delete_file(file_path)
"""
import os
import hashlib
import aiofiles
from pathlib import Path
from typing import Optional
from server.infra.config import settings


class Storage:
    """
    File storage manager with checksum-based deduplication.
    基于校验和的去重文件存储管理器。

    All files are saved under a configurable base directory (default: ./uploads).
    The filename is prefixed with a SHA256 checksum to:
    1. Enable content-addressable deduplication / 支持内容寻址去重
    2. Prevent filename collisions / 防止文件名冲突
    3. Allow quick lookup by content hash / 支持通过内容哈希快速查找

    Attributes:
        base_dir:  Root directory for file storage / 文件存储根目录

    Args:
        base_dir: Custom base directory (default from settings) / 自定义基础目录
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.upload_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_content: bytes, filename: str) -> tuple[str, str]:
        """
        Save file with checksum-based naming to prevent collisions.
        使用基于校验和的文件名保存文件，防止冲突。

        The saved filename follows the pattern: {checksum_prefix}_{original_stem}{suffix}
        Example: "a1b2c3d4e5f6g7h8_my_document.pdf"

        Args:
            file_content:  File content as raw bytes / 文件内容的原始字节
            filename:      Original filename (used for extension detection)
                          / 原始文件名（用于识别扩展名）

        Returns:
            Tuple of (relative_path_relative_to_cwd, sha256_checksum)
            返回一个元组：(相对于工作目录的文件路径, SHA256校验和)

        Raises:
            OSError: If file cannot be written / 文件写入失败时抛出
        """
        # Calculate checksum / 计算校验和
        checksum = hashlib.sha256(file_content).hexdigest()

        # Create filename with checksum prefix to avoid collisions
        # 使用校验和前 16 位作为前缀，防止文件名冲突
        file_ext = Path(filename).suffix
        safe_filename = f"{checksum[:16]}_{Path(filename).stem}{file_ext}"
        file_path = self.base_dir / safe_filename

        # Save file asynchronously / 异步写入文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)

        return str(file_path.resolve().relative_to(Path.cwd())), checksum

    def calculate_checksum(self, file_path: str) -> str:
        """
        Calculate SHA256 checksum of an existing file.
        计算已有文件的 SHA256 校验和。

        Args:
            file_path:  Path to the file / 文件路径

        Returns:
            SHA256 hex digest string / SHA256 十六进制字符串
        """
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def get_file_path(self, filename: str) -> Path:
        """
        Get the full path for a given filename in the storage directory.
        获取存储目录中指定文件的完整路径。

        Args:
            filename:  Filename (with or without checksum prefix) / 文件名

        Returns:
            Absolute Path object / 绝对路径对象
        """
        return self.base_dir / filename

    def file_exists(self, checksum: str) -> Optional[str]:
        """
        Check if a file with the given checksum already exists.
        检查具有指定校验和的文件是否已存在。

        Searches for files whose names start with the first 16 hex chars
        of the SHA256 checksum.

        Args:
            checksum:  Full SHA256 checksum to look up / 要查找的完整 SHA256 校验和

        Returns:
            File path string if found, None otherwise / 找到则返回路径，否则返回 None
        """
        for file_path in self.base_dir.glob(f"{checksum[:16]}*"):
            return str(file_path)
        return None

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from the storage directory.
        从存储目录中删除文件。

        Supports both absolute and relative paths. Relative paths are resolved
        relative to the base storage directory.

        Args:
            file_path:  Relative or absolute path to delete / 相对或绝对文件路径

        Returns:
            True if the file was deleted, False if it was not found.
            如果文件被删除则返回 True，未找到则返回 False。
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_dir / file_path

        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
