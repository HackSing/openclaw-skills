"""
飞书文档操作客户端 (Python)

使用用户访问令牌认证的飞书文档操作库，支持自动刷新 token。

依赖:
    pip install requests

用法:
    from feishu_client import FeishuClient, load_token_manager
    
    # 方式1: 使用 TokenManager 自动刷新
    manager = load_token_manager("cli_xxx", "secret_xxx")
    client = FeishuClient(manager=manager)
    
    # 读取文档 (如果 token 过期会自动刷新)
    content = client.read_doc("doc_token")
    
    # 方式2: 手动传入 token
    client = FeishuClient(user_access_token="u-xxx")
    content = client.read_doc("doc_token")
"""

import os
import json
import requests
from typing import Optional, Any, Dict, List, Union


# 默认配置目录
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/claw-feishu-user")


class TokenManager:
    """飞书用户访问令牌管理器，支持自动刷新"""
    
    def __init__(self, app_id: str, app_secret: str, config_dir: str = DEFAULT_CONFIG_DIR):
        self.app_id = app_id
        self.app_secret = app_secret
        self.config_dir = config_dir
        self.config_path = os.path.join(config_dir, "config.json")
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        # 加载缓存的 token
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "access_token": None,
                "refresh_token": None,
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
        
        self.access_token = self.config.get("access_token")
        self.refresh_token = self.config.get("refresh_token")
    
    def _save_config(self):
        """保存配置到文件"""
        self.config["access_token"] = self.access_token
        self.config["refresh_token"] = self.refresh_token
        self.config["app_id"] = self.app_id
        self.config["app_secret"] = self.app_secret
        
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_token(self) -> str:
        """获取当前有效的 access_token"""
        if not self.access_token:
            raise Exception("未找到 access_token，请先通过授权获取")
        return self.access_token
    
    def refresh_access_token(self) -> str:
        """刷新 access_token"""
        url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        resp = requests.post(url, json=payload, headers=headers)
        data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"刷新 token 失败: {data.get('msg')}")
        
        result = data.get("data", {})
        self.access_token = result.get("access_token")
        self.refresh_token = result.get("refresh_token")
        self._save_config()
        
        print(f"Token 刷新成功: {self.access_token[:20]}...")
        return self.access_token
    
    def authorize_with_code(self, code: str) -> str:
        """使用授权码获取 token"""
        url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        resp = requests.post(url, json=payload, headers=headers)
        data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"获取 token 失败: {data.get('msg')}")
        
        result = data.get("data", {})
        self.access_token = result.get("access_token")
        self.refresh_token = result.get("refresh_token")
        self._save_config()
        
        print(f"授权成功! Token: {self.access_token[:20]}...")
        return self.access_token


def load_token_manager(app_id: str, app_secret: str = None, config_dir: str = DEFAULT_CONFIG_DIR) -> TokenManager:
    """
    加载或创建 TokenManager
    
    Args:
        app_id: 飞书应用 ID
        app_secret: 飞书应用密钥 (可选，从配置读取)
        config_dir: 配置目录
    
    Returns:
        TokenManager 实例
    """
    # 如果没提供 secret，尝试从配置读取
    if not app_secret:
        config_path = os.path.join(config_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                app_secret = config.get("app_secret")
    
    if not app_secret:
        raise Exception("未提供 app_secret，且配置文件中也没有")
    
    return TokenManager(app_id, app_secret, config_dir)


# Token 过期错误码
TOKEN_EXPIRED_CODE = 99991663


class FeishuClient:
    """飞书文档操作客户端"""
    
    BASE_URL = "https://open.feishu.cn/open-apis"
    
    def __init__(self, user_access_token: str = None, domain: str = "feishu", manager: TokenManager = None):
        """
        初始化客户端
        
        Args:
            user_access_token: 飞书用户访问令牌 (可选)
            domain: 飞书域名 (feishu/lark)
            manager: TokenManager 实例 (可选，有则自动刷新 token)
        """
        self.token_manager = manager
        self.domain = domain
        
        if manager:
            self.token = manager.get_token()
        else:
            self.token = user_access_token
        
        if not self.token:
            raise Exception("必须提供 user_access_token 或 manager")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8"
        }
    
    def _refresh_token(self):
        """刷新 token 并更新 headers"""
        if self.token_manager:
            self.token = self.token_manager.refresh_access_token()
            self.headers["Authorization"] = f"Bearer {self.token}"
        else:
            raise Exception("Token 已过期，且未配置 TokenManager，无法自动刷新")
    
    def _handle_response(self, resp: requests.Response) -> Dict[str, Any]:
        """处理 API 响应，自动处理 token 过期"""
        data = resp.json()
        
        # 如果 token 过期，尝试自动刷新
        if data.get("code") == TOKEN_EXPIRED_CODE:
            if self.token_manager:
                self._refresh_token()
                raise TokenExpiredError("Token 已刷新，请重试请求")
            else:
                raise Exception(f"Token 已过期: {data.get('msg')}")
        
        if data.get("code") != 0:
            raise Exception(f"API 调用失败: {data.get('msg')}")
        
        return data
    
    # ========== 文档操作 ==========
    
    def read_doc(self, doc_token: str) -> Dict[str, Any]:
        """读取文档内容"""
        url = f"{self.BASE_URL}/docx/v1/documents/{doc_token}"
        resp = requests.get(url, headers=self.headers)
        
        try:
            return self._handle_response(resp).get("data", {})
        except TokenExpiredError:
            resp = requests.get(url, headers=self.headers)
            return self._handle_response(resp).get("data", {})
    
    def create_doc(self, title: str, folder_token: Optional[str] = None) -> str:
        """创建新文档"""
        url = f"{self.BASE_URL}/docx/v1/documents"
        payload = {"title": title}
        if folder_token:
            payload["folder_token"] = folder_token
        
        resp = requests.post(url, json=payload, headers=self.headers)
        
        try:
            data = self._handle_response(resp)
        except TokenExpiredError:
            resp = requests.post(url, json=payload, headers=self.headers)
            data = self._handle_response(resp)
        
        return data.get("data", {}).get("document", {}).get("document_id")
    
    def write_doc(self, doc_token: str, content: str) -> Dict[str, Any]:
        """写入文档 (覆盖)"""
        return self.append_doc(doc_token, content)
    
    def append_doc(self, doc_token: str, content: str) -> Dict[str, Any]:
        """追加内容到文档末尾"""
        blocks = self.list_blocks(doc_token)
        first_block = blocks[0] if blocks else None
        
        if first_block:
            url = f"{self.BASE_URL}/docx/v1/documents/{doc_token}/blocks/{first_block.get('block_id')}/children?document_revision_id=-1"
        else:
            raise Exception("文档为空，无法追加内容")
        
        payload = {
            "children": [
                {
                    "block_type": 2,
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
        
        try:
            return self._handle_response(resp)
        except TokenExpiredError:
            resp = requests.post(url, json=payload, headers=self.headers)
            return self._handle_response(resp)
    
    def list_blocks(self, doc_token: str) -> List[Dict[str, Any]]:
        """列出文档所有块"""
        url = f"{self.BASE_URL}/docx/v1/documents/{doc_token}/blocks"
        resp = requests.get(url, headers=self.headers)
        
        try:
            data = self._handle_response(resp)
        except TokenExpiredError:
            resp = requests.get(url, headers=self.headers)
            data = self._handle_response(resp)
        
        return data.get("data", {}).get("items", [])
    
    def get_block(self, doc_token: str, block_id: str) -> Dict[str, Any]:
        """获取指定块"""
        url = f"{self.BASE_URL}/docx/v1/documents/{doc_token}/blocks/{block_id}"
        resp = requests.get(url, headers=self.headers)
        
        try:
            data = self._handle_response(resp)
        except TokenExpiredError:
            resp = requests.get(url, headers=self.headers)
            data = self._handle_response(resp)
        
        return data.get("data", {})
    
    def update_block(self, doc_token: str, block_id: str, content: str) -> Dict[str, Any]:
        """更新块内容"""
        url = f"{self.BASE_URL}/docx/v1/documents/{doc_token}/blocks/{block_id}"
        payload = {"block": {"text": {"content": content}}}
        
        resp = requests.put(url, json=payload, headers=self.headers)
        
        try:
            return self._handle_response(resp)
        except TokenExpiredError:
            resp = requests.put(url, json=payload, headers=self.headers)
            return self._handle_response(resp)
    
    def delete_block(self, doc_token: str, block_id: str) -> Dict[str, Any]:
        """删除块 (不支持)"""
        raise Exception("飞书文档 API 不支持删除块，请使用 delete_doc() 删除整个文档")
    
    def delete_doc(self, doc_token: str) -> Dict[str, Any]:
        """删除整个文档"""
        url = f"{self.BASE_URL}/drive/v1/files/{doc_token}"
        params = {"type": "docx", "token": doc_token}
        resp = requests.delete(url, params=params, headers=self.headers)
        
        try:
            return self._handle_response(resp)
        except TokenExpiredError:
            resp = requests.delete(url, params=params, headers=self.headers)
            return self._handle_response(resp)


class TokenExpiredError(Exception):
    """Token 过期异常"""
    pass


# ========== 便捷函数 ==========

def read_document(doc_token: str, user_access_token: str = None, manager: TokenManager = None) -> Dict[str, Any]:
    """读取文档便捷函数"""
    client = FeishuClient(user_access_token=user_access_token, manager=manager)
    return client.read_doc(doc_token)


def create_document(title: str, folder_token: str = None, user_access_token: str = None, manager: TokenManager = None) -> str:
    """创建文档便捷函数"""
    client = FeishuClient(user_access_token=user_access_token, manager=manager)
    return client.create_doc(title, folder_token)


def write_document(doc_token: str, content: str, user_access_token: str = None, manager: TokenManager = None) -> Dict[str, Any]:
    """写入文档便捷函数"""
    client = FeishuClient(user_access_token=user_access_token, manager=manager)
    return client.write_doc(doc_token, content)


def append_document(doc_token: str, content: str, user_access_token: str = None, manager: TokenManager = None) -> Dict[str, Any]:
    """追加文档便捷函数"""
    client = FeishuClient(user_access_token=user_access_token, manager=manager)
    return client.append_doc(doc_token, content)
