# -*- coding: utf-8 -*-
"""压缩文件解压工具

提供多种压缩格式的解压功能。
"""
import zipfile
import tarfile
import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("ArchiveUtils")


class ArchiveExtractor:
    """压缩文件解压工具类"""

    # 支持的压缩格式映射
    SUPPORTED_FORMATS = {
        '.zip': {'name': 'ZIP', 'extractor': '_extract_zip'},
        '.rar': {'name': 'RAR', 'extractor': '_extract_rar'},
        '.7z': {'name': '7Z', 'extractor': '_extract_7z'},
        '.tar.gz': {'name': 'TAR.GZ', 'extractor': '_extract_tar', 'tar_mode': 'gz'},
        '.tgz': {'name': 'TGZ', 'extractor': '_extract_tar', 'tar_mode': 'gz'},
        '.tar.bz2': {'name': 'TAR.BZ2', 'extractor': '_extract_tar', 'tar_mode': 'bz2'},
        '.tbz2': {'name': 'TBZ2', 'extractor': '_extract_tar', 'tar_mode': 'bz2'},
        '.tar': {'name': 'TAR', 'extractor': '_extract_tar', 'tar_mode': ''},
    }

    @classmethod
    def is_archive_file(cls, filename: str, allowed_types: Optional[List[str]] = None) -> bool:
        """
        检查文件是否为支持的压缩格式

        Args:
            filename: 文件名（可以是 str 或 Path 对象）
            allowed_types: 允许的压缩格式列表（如 ['.zip', '.rar']）

        Returns:
            bool: 是否为压缩文件
        """
        # 处理 Path 对象
        if isinstance(filename, Path):
            filename_str = filename.name
        else:
            filename_str = str(filename)

        filename_lower = filename_str.lower()

        # 如果指定了允许的格式，只检查这些格式
        if allowed_types:
            allowed_types_lower = [t.lower() for t in allowed_types]
            for ext in allowed_types_lower:
                if filename_lower.endswith(ext):
                    return True
            return False

        # 否则检查所有支持的格式
        for ext in cls.SUPPORTED_FORMATS.keys():
            if filename_lower.endswith(ext):
                return True
        return False

    @classmethod
    def get_archive_type(cls, filename: str) -> Optional[str]:
        """
        获取压缩文件类型

        Args:
            filename: 文件名（可以是 str 或 Path 对象）

        Returns:
            str|None: 压缩格式扩展名（如 .zip）或 None
        """
        # 处理 Path 对象
        if isinstance(filename, Path):
            filename_str = filename.name
        else:
            filename_str = str(filename)

        filename_lower = filename_str.lower()
        for ext in cls.SUPPORTED_FORMATS.keys():
            if filename_lower.endswith(ext):
                return ext
        return None

    @classmethod
    def get_supported_formats(cls) -> dict:
        """
        获取支持的压缩格式列表

        Returns:
            dict: 支持的压缩格式映射
        """
        return cls.SUPPORTED_FORMATS.copy()

    def extract_archive(
        self,
        archive_path: str,
        extract_dir: Path,
        password: Optional[str] = None,
        allowed_types: Optional[List[str]] = None
    ) -> dict:
        """
        解压压缩文件

        Args:
            archive_path: 压缩文件路径
            extract_dir: 解压目标目录
            password: 压缩包密码（可选）
            allowed_types: 允许的压缩格式列表（可选）

        Returns:
            dict: {
                'success': bool,              # 是否成功
                'extracted_count': int,      # 解压的文件数量
                'extracted_paths': List[str], # 解压后的文件路径列表
                'error': str                 # 错误信息（如果失败）
            }
        """
        archive_path = Path(archive_path)
        if not archive_path.exists():
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': f'压缩包不存在：{archive_path}'
            }

        # 检查文件类型
        archive_type = self.get_archive_type(archive_path.name)
        if not archive_type:
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': f'不支持的压缩格式：{archive_path.name}'
            }

        # 检查是否在允许的类型列表中
        if allowed_types and archive_type not in allowed_types:
            logger.info(f"【解压器】跳过不允许的压缩格式：{archive_type}")
            return {
                'success': True,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': ''
            }

        # 创建解压目录（避免 Windows 同名文件/目录冲突）
        # 使用原始文件名加上 _extracted 后缀
        archive_name = archive_path.stem  # 去掉扩展名
        archive_ext = archive_path.suffix  # 扩展名（如 .zip）
        extract_subdir = extract_dir / f"{archive_name}_extracted{archive_ext}/"
        extract_subdir.mkdir(parents=True, exist_ok=True)

        logger.info(f"【解压器】开始解压：{archive_path.name} -> {extract_subdir}")

        # 获取解压方法
        format_info = self.SUPPORTED_FORMATS[archive_type]
        extractor_method = getattr(self, format_info['extractor'])

        try:
            # 调用对应的解压方法（根据格式类型传递不同参数）
            if archive_type in ['.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar']:
                # TAR 格式需要 tar_mode 参数
                result = extractor_method(
                    archive_path,
                    extract_subdir,
                    password,
                    tar_mode=format_info.get('tar_mode')
                )
            else:
                # ZIP, RAR, 7Z 格式只需要基本参数
                result = extractor_method(
                    archive_path,
                    extract_subdir,
                    password
                )

            if result['success']:
                logger.info(f"【解压器】解压成功：{result['extracted_count']} 个文件")
                for path in result['extracted_paths']:
                    logger.debug(f"  - {Path(path).relative_to(extract_dir)}")
            else:
                logger.warning(f"【解压器】解压失败：{result['error']}")

            # 添加解压目录信息到返回值
            result['extract_dir'] = str(extract_subdir)
            return result

        except Exception as e:
            logger.error(f"【解压器】解压异常：{archive_path.name}，错误：{e}")
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': str(e),
                'extract_dir': str(extract_subdir)
            }

    def _extract_zip(
        self,
        archive_path: Path,
        extract_dir: Path,
        password: Optional[str] = None,
        **kwargs
    ) -> dict:
        """解压 ZIP 文件"""
        extracted_paths = []
        extracted_count = 0

        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # 检查 ZIP 文件是否需要密码（尝试读取第一个文件）
                needs_password = False
                try:
                    # 尝试获取文件列表（不需要密码）
                    file_list = zip_ref.namelist()
                    if file_list:
                        # 尝试测试第一个文件是否需要密码
                        first_file = file_list[0]
                        if not first_file.endswith('/'):
                            try:
                                # 尝试读取文件信息（不需要解压）
                                zip_ref.getinfo(first_file)
                            except RuntimeError as e:
                                if 'password' in str(e).lower():
                                    needs_password = True
                except Exception:
                    pass

                if needs_password and not password:
                    logger.warning("【解压器】ZIP 文件需要密码，但未提供密码")

                # 尝试解压所有文件
                for member in zip_ref.namelist():
                    try:
                        # 跳过目录（目录会在创建文件时自动创建）
                        if member.endswith('/'):
                            continue

                        # 解压文件
                        zip_ref.extract(member, extract_dir, pwd=password if password else None)
                        extracted_path = extract_dir / member
                        extracted_paths.append(str(extracted_path))
                        extracted_count += 1
                    except RuntimeError as e:
                        if 'password' in str(e).lower():
                            logger.error(f"【解压器】ZIP 密码错误：{member}")
                            return {
                                'success': False,
                                'extracted_count': 0,
                                'extracted_paths': [],
                                'error': '密码错误或文件受保护'
                            }
                        else:
                            logger.warning(f"【解压器】跳过文件：{member}，错误：{e}")
                            continue

            return {
                'success': True,
                'extracted_count': extracted_count,
                'extracted_paths': extracted_paths,
                'error': ''
            }

        except zipfile.BadZipFile as e:
            logger.error(f"【解压器】ZIP 文件损坏：{e}")
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': 'ZIP 文件损坏'
            }
        except Exception as e:
            logger.error(f"【解压器】ZIP 解压失败：{e}")
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': str(e)
            }

    def _extract_tar(
        self,
        archive_path: Path,
        extract_dir: Path,
        password: Optional[str] = None,
        tar_mode: str = ''
    ) -> dict:
        """解压 TAR 文件"""
        extracted_paths = []
        extracted_count = 0

        try:
            # 根据压缩模式选择打开模式
            if tar_mode == 'gz':
                mode = 'r:gz'
            elif tar_mode == 'bz2':
                mode = 'r:bz2'
            else:
                mode = 'r'

            with tarfile.open(archive_path, mode) as tar_ref:
                members = tar_ref.getmembers()

                for member in members:
                    try:
                        # 跳过目录
                        if member.isdir():
                            continue

                        # 解压文件
                        tar_ref.extract(member, extract_dir)
                        extracted_path = extract_dir / member.name
                        extracted_paths.append(str(extracted_path))
                        extracted_count += 1
                    except Exception as e:
                        logger.warning(f"【解压器】跳过文件：{member.name}，错误：{e}")
                        continue

            return {
                'success': True,
                'extracted_count': extracted_count,
                'extracted_paths': extracted_paths,
                'error': ''
            }

        except tarfile.TarError as e:
            logger.error(f"【解压器】TAR 文件损坏：{e}")
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': 'TAR 文件损坏'
            }
        except Exception as e:
            logger.error(f"【解压器】TAR 解压失败：{e}")
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': str(e)
            }

    def _extract_rar(
        self,
        archive_path: Path,
        extract_dir: Path,
        password: Optional[str] = None,
        **kwargs
    ) -> dict:
        """解压 RAR 文件（使用 rarfile 库）"""
        try:
            import rarfile
        except ImportError:
            logger.error("【解压器】rarfile 库未安装，无法解压 RAR 文件")
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': 'rarfile 库未安装'
            }

        extracted_paths = []
        extracted_count = 0

        try:
            with rarfile.RarFile(archive_path) as rf:
                # 检查是否需要密码
                if rf.needs_password():
                    if not password:
                        logger.error(f"【解压器】RAR 文件需要密码，但未提供密码")
                        return {
                            'success': False,
                            'extracted_count': 0,
                            'extracted_paths': [],
                            'error': '需要密码'
                        }

                # 使用 extractall 解压所有文件
                rf.extract(path=extract_dir, pwd=password)

                # 扫描解压后的文件
                for item in extract_dir.rglob('*'):
                    if item.is_file():
                        extracted_paths.append(str(item))
                        extracted_count += 1

            return {
                'success': True,
                'extracted_count': extracted_count,
                'extracted_paths': extracted_paths,
                'error': ''
            }

        except Exception as e:
            logger.error(f"【解压器】RAR 解压失败：{e}")
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': str(e)
            }

    def _extract_7z(
        self,
        archive_path: Path,
        extract_dir: Path,
        password: Optional[str] = None,
        **kwargs
    ) -> dict:
        """解压 7Z 文件（使用 py7zr 库）"""
        try:
            import py7zr
        except ImportError:
            logger.error("【解压器】py7zr 库未安装，无法解压 7Z 文件")
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': 'py7zr 库未安装'
            }

        extracted_paths = []
        extracted_count = 0

        try:
            # py7zr 的正确 API：使用 unpack_7zarchive 或 SevenZipFile.extractall
            if password:
                # 如果有密码，使用 SevenZipFile
                with py7zr.SevenZipFile(archive_path, password=password) as szf:
                    szf.extractall(path=extract_dir)
            else:
                # 如果没有密码，使用 unpack_7zarchive
                py7zr.unpack_7zarchive(
                    archive_path,
                    extract_dir
                )

            # 扫描解压后的文件
            for item in extract_dir.rglob('*'):
                if item.is_file():
                    extracted_paths.append(str(item))
                    extracted_count += 1

            return {
                'success': True,
                'extracted_count': extracted_count,
                'extracted_paths': extracted_paths,
                'error': ''
            }

        except Exception as e:
            logger.error(f"【解压器】7Z 解压失败：{e}")
            return {
                'success': False,
                'extracted_count': 0,
                'extracted_paths': [],
                'error': str(e)
            }
