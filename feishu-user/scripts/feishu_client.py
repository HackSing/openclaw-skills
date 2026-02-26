"""
飞书文档操作客户端 (Python)

使用用户访问令牌认证的飞书文档操作库。

依赖:
    pip install requests

用法:
    from feishu_client import FeishuClient
    
    client = FeishuClient(user_access_token="u-xxx")
    
    # 读取文档
    content = client.read_doc("doc_token")
    
    # 创建文档
    doc_token = client.create_doc("标题", folder_token="xxx")
    
    # 写入文档
    client.write_doc("doc_token", "# Hello\\n\\nWorld")
    
    # 追加内容
    client.append_doc("doc_token", "## New Section")
"""

import requests
from typing import Optional, Any, Dict, List, Union


class FeishuClient:
    """飞书文档操作客户端"""
    
    BASE_URL = "https://open.feishu.cn/open-apis"
    
    def __init__(self, user_access_token: str, domain: str = "feishu"):
        """
        初始化客户端
        
        Args:
            user_access_token: 飞书用户访问令牌
            domain: 飞书域名 (feishu/lark)
        """
        self.token = user_access_token
        self.domain = domain
        self.headers = {
            "Authorization": f"Bearer {user_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
    
    # ========== 文档操作 ==========
    
    def read_doc(self, doc_token: str) -> Dict[str, Any]:
        """
        读取文档内容
        
        Args:
            doc_token: 文档令牌 (从 URL /docx/XXX 获取)
        
        Returns:
            文档内容
        """
        url = f"{self.BASE_URL}/docx/v1/documents/{doc_token}"
        resp = requests.get(url, headers=self.headers)
        data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"读取文档失败: {data.get('msg')}")
        
        return data.get("data", {})
    
    def create_doc(self, title: str, folder_token: Optional[str] = None) -> str:
        """
        创建新文档
        
        Args:
            title: 文档标题
            folder_token: 文件夹令牌 (可选)
        
        Returns:
            创建的文档 token
        """
        url = f"{self.BASE_URL}/docx/v1/documents"
        payload = {"title": title}
        if folder_token:
            payload["folder_token"] = folder_token
        
        resp = requests.post(url, json=payload, headers=self.headers)
        data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"创建文档失败: {data.get('msg')}")
        
        return data.get("data", {}).get("document", {}).get("document_id")
    
    def write_doc(self, doc_token: str, content: str) -> Dict[str, Any]:
        """
        写入文档 (覆盖)
        
        Args:
            doc_token: 文档令牌
            content: Markdown 内容
        
        Returns:
            操作结果
        """
        # 追加到文档末尾
        return self.append_doc(doc_token, content)
    
    def append_doc(self, doc_token: str, content: str) -> Dict[str, Any]:
        """
        追加内容到文档末尾
        
        Args:
            doc_token: 文档令牌
            content: Markdown 内容
        
        Returns:
            操作结果
        """
        # 先获取文档的所有块，找到第一个块
        blocks = self.list_blocks(doc_token)
        
        # 正确的 API 路径：/documents/{doc_id}/blocks/{block_id}/children
        first_block = blocks[0] if blocks else None
        
        if first_block:
            url = f"{self.BASE_URL}/docx/v1/documents/{doc_token}/blocks/{first_block.get('block_id')}/children?document_revision_id=-1"
        else:
            raise Exception("文档为空，无法追加内容")
        
        # 正确的 payload 格式
        payload = {
            "children": [
                {
                    "block_type": 2,  # 文本块
                    "text": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": content
                                }
                            }
                        ]
                    }
                }
            ],
            "index": 0
        }
        
        resp = requests.post(url, json=payload, headers=self.headers)
        data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"追加内容失败: {data.get('msg')}")
        
        return data
    
    def list_blocks(self, doc_token: str) -> List[Dict[str, Any]]:
        """
        列出文档所有块
        
        Args:
            doc_token: 文档令牌
        
        Returns:
            块列表
        """
        url = f"{self.BASE_URL}/docx/v1/documents/{doc_token}/blocks"
        resp = requests.get(url, headers=self.headers)
        data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"获取块列表失败: {data.get('msg')}")
        
        return data.get("data", {}).get("items", [])
    
    def get_block(self, doc_token: str, block_id: str) -> Dict[str, Any]:
        """
        获取指定块
        
        Args:
            doc_token: 文档令牌
            block_id: 块 ID
        
        Returns:
            块内容
        """
        url = f"{self.BASE_URL}/docx/v1/documents/{doc_token}/blocks/{block_id}"
        resp = requests.get(url, headers=self.headers)
        data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"获取块失败: {data.get('msg')}")
        
        return data.get("data", {})
    
    def update_block(self, doc_token: str, block_id: str, content: str) -> Dict[str, Any]:
        """
        更新块内容
        
        Args:
            doc_token: 文档令牌
            block_id: 块 ID
            content: 新内容
        
        Returns:
            操作结果
        """
        url = f"{self.BASE_URL}/docx/v1/documents/{doc_token}/blocks/{block_id}"
        payload = {
            "block": {
                "text": {"content": content}
            }
        }
        
        resp = requests.put(url, json=payload, headers=self.headers)
        data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"更新块失败: {data.get('msg')}")
        
        return data
    
    def delete_block(self, doc_token: str, block_id: str) -> Dict[str, Any]:
        """
        删除块
        
        注意：飞书文档 API 不支持删除单个块，请使用 delete_doc() 删除整个文档
        
        Args:
            doc_token: 文档令牌
            block_id: 块 ID
        
        Returns:
            操作结果
        """
        raise Exception("飞书文档 API 不支持删除块，请使用 delete_doc() 删除整个文档")
    
    def delete_doc(self, doc_token: str) -> Dict[str, Any]:
        """
        删除整个文档
        
        Args:
            doc_token: 文档令牌
        
        Returns:
            操作结果
        """
        url = f"{self.BASE_URL}/drive/v1/files/{doc_token}"
        params = {"type": "docx", "token": doc_token}
        resp = requests.delete(url, params=params, headers=self.headers)
        data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"删除文档失败: {data.get('msg')}")
        
        return data


# ========== 便捷函数 ==========

def read_document(doc_token: str, user_access_token: str = None) -> Dict[str, Any]:
    """读取文档便捷函数"""
    client = FeishuClient(user_access_token or "your-token")
    return client.read_doc(doc_token)


def create_document(title: str, folder_token: str = None, user_access_token: str = None) -> str:
    """创建文档便捷函数"""
    client = FeishuClient(user_access_token or "your-token")
    return client.create_doc(title, folder_token)


def write_document(doc_token: str, content: str, user_access_token: str = None) -> Dict[str, Any]:
    """写入文档便捷函数"""
    client = FeishuClient(user_access_token or "your-token")
    return client.write_doc(doc_token, content)


def append_document(doc_token: str, content: str, user_access_token: str = None) -> Dict[str, Any]:
    """追加文档便捷函数"""
    client = FeishuClient(user_access_token or "your-token")
    return client.append_doc(doc_token, content)
