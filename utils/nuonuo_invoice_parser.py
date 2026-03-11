# -*- coding: utf-8 -*-
"""诺诺网发票链接解析器

从诺诺网发票邮件HTML中提取发票链接，并自动下载PDF文件。
"""
import logging
import re
import time
import hashlib
from pathlib import Path
from typing import Optional

logger = logging.getLogger("NuonuoInvoiceParser")


class NuonuoInvoiceParser:
    """诺诺网发票链接解析器"""

    def extract_invoice_link(self, html_content: str, anchor_text: str = "点击链接查看发票：") -> Optional[str]:
        """
        从HTML中提取特定文字后面的链接

        Args:
            html_content: HTML内容
            anchor_text: 锚点文字（默认："点击链接查看发票："）

        Returns:
            Optional[str]: 发票查看链接，如果找不到返回None
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'lxml')

            # 查找包含锚点文字的span/div标签
            for element in soup.find_all(['span', 'div', 'p']):
                element_text = element.get_text()
                if anchor_text in element_text:
                    logger.debug(f"【诺诺网解析器】找到锚点文字：{element_text[:50]}...")

                    # 策略1: 在下一个兄弟元素中查找链接
                    next_sibling = element.find_next_sibling(['a', 'span'])
                    if next_sibling and next_sibling.name == 'a':
                        href = next_sibling.get('href')
                        if href and 'nnfp.jss.com.cn' in href:
                            logger.info(f"【诺诺网解析器】✅ 从兄弟元素提取发票链接：{href}")
                            return href

                    # 策略2: 在父元素中查找链接
                    parent = element.parent
                    if parent:
                        link = parent.find('a', href=True)
                        if link:
                            href = link.get('href', '')
                            if 'nnfp.jss.com.cn' in href:
                                logger.info(f"【诺诺网解析器】✅ 从父元素提取发票链接：{href}")
                                return href

                    # 策略3: 在整个文档中查找包含nnfp.jss.com.cn的链接
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        if 'nnfp.jss.com.cn' in href:
                            # 检查链接是否在锚点文字附近
                            link_parent = link.parent
                            if link_parent and anchor_text in link_parent.get_text():
                                logger.info(f"【诺诺网解析器】✅ 从文档中提取发票链接：{href}")
                                return href

            logger.warning(f"【诺诺网解析器】未找到发票链接（锚点文字：{anchor_text}）")
            return None

        except Exception as e:
            logger.error(f"【诺诺网解析器】HTML解析失败：{e}")
            return None

    def get_pdf_download_url(self, invoice_url: str, timeout: int = 30) -> Optional[str]:
        """
        访问发票查看页面，获取PDF下载链接

        Args:
            invoice_url: 发票查看URL
            timeout: 请求超时（秒）

        Returns:
            Optional[str]: PDF下载链接，如果获取失败返回None
        """
        import requests
        import urllib.parse

        try:
            logger.info(f"【诺诺网解析器】开始访问发票页面：{invoice_url}")

            # 1. 访问发票URL（会重定向到查看页面）
            response = requests.get(
                invoice_url,
                timeout=timeout,
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive'
                }
            )
            response.raise_for_status()

            # 2. 从重定向URL中提取paramList参数
            final_url = response.url
            logger.debug(f"【诺诺网解析器】重定向后的URL：{final_url}")

            # 尝试多种方式提取paramList参数
            param_match = None

            # 方式1: 从URL查询参数中提取
            param_match = re.search(r'paramList=([^&]+)', final_url)

            # 方式2: 从URL路径中提取
            if not param_match:
                param_match = re.search(r'/([^/]+)$', final_url)

            # 方式3: 从页面HTML中提取
            if not param_match:
                param_match = re.search(r'paramList["\']:\s*["\']([^"\']+)["\']', response.text)
                if param_match:
                    param_match = re.search(r'paramList=([^&]+)', urllib.parse.unquote(param_match.group(1)))

            if not param_match:
                logger.error(f"【诺诺网解析器】无法找到paramList参数")
                return None

            param_list = param_match.group(1)
            logger.debug(f"【诺诺网解析器】提取paramList参数：{param_list[:50]}...")

            # 3. 调用API获取发票详情
            api_url = "https://nnfp.jss.com.cn/sapi/scan2/getIvcDetailShow.do"

            # URL编码参数
            encoded_param = urllib.parse.quote(param_list, safe='')

            # 构造请求参数
            payload = {
                'paramList': param_list,  # 使用原始参数
                'code': param_list,
                'aliView': 'true',
                'invoiceDetailMiddleUri': f'printQrcode?paramList={encoded_param}&aliView=true&shortLinkSource=1&wxApplet=0',
                'shortLinkSource': '1',
                '_timestamp': str(int(time.time() * 1000))
            }

            logger.info(f"【诺诺网解析器】调用API获取发票详情...")

            api_response = requests.post(
                api_url,
                data=payload,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': final_url,
                    'Origin': 'https://nnfp.jss.com.cn'
                },
                timeout=timeout
            )
            api_response.raise_for_status()

            # 4. 解析JSON响应，提取PDF链接
            data = api_response.json()
            logger.debug(f"【诺诺网解析器】API响应状态：{data.get('status')}")

            if data.get('status') == '0000' and 'data' in data:
                pdf_url = data['data'].get('invoiceSimpleVo', {}).get('url', '')
                if pdf_url:
                    logger.info(f"【诺诺网解析器】✅ 成功获取PDF链接：{pdf_url}")
                    return pdf_url
                else:
                    logger.error(f"【诺诺网解析器】API响应中未找到PDF链接")
            else:
                logger.error(f"【诺诺网解析器】API响应异常：{data.get('msg', 'Unknown error')}")

            return None

        except requests.exceptions.Timeout:
            logger.error(f"【诺诺网解析器】❌ 请求超时")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"【诺诺网解析器】❌ HTTP错误：{e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"【诺诺网解析器】❌ 请求失败：{e}")
            return None
        except Exception as e:
            logger.error(f"【诺诺网解析器】❌ 解析失败：{e}")
            return None

    def download_invoice_pdf(
        self,
        invoice_url: str,
        save_path: Path,
        timeout: int = 30
    ) -> bool:
        """
        下载发票PDF文件

        Args:
            invoice_url: 发票查看URL
            save_path: 保存路径
            timeout: 请求超时（秒）

        Returns:
            bool: 是否下载成功
        """
        import requests

        try:
            # 获取PDF下载链接
            pdf_url = self.get_pdf_download_url(invoice_url, timeout)
            if not pdf_url:
                return False

            # 下载PDF文件
            logger.info(f"【诺诺网解析器】开始下载PDF：{pdf_url}")

            response = requests.get(
                pdf_url,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                stream=True
            )
            response.raise_for_status()

            # 检查Content-Type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' not in content_type:
                logger.warning(f"【诺诺网解析器】响应可能不是PDF文件：{content_type}")

            # 保存文件
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"【诺诺网解析器】✅ PDF下载成功：{save_path}")
            return True

        except Exception as e:
            logger.error(f"【诺诺网解析器】❌ PDF下载失败：{e}")
            return False
