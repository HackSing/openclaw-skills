"""
MemSaaS Python 客户端

用法:
    from memsaas_client import MemSaaSClient
    
    client = MemSaaSClient(api_key="your-api-key")
    
    # 记忆读取
    context = client.get_context("user_id", "用户的问题")
    
    # 记忆写入
    client.process_memory("user_id", "用户消息", "AI回复")
"""

import requests
from typing import Optional, Dict, Any


class MemSaaSClient:
    """MemSaaS API 客户端"""
    
    BASE_URL = "https://memsys-api-1076113452918.us-central1.run.app"
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    # ========== 用户相关 ==========
    
    def warmup(self, user_id: str, initial_biz_data: dict = None) -> Dict[str, Any]:
        """
        用户冷启动/建档
        
        Args:
            user_id: 用户唯一标识
            initial_biz_data: 初始业务数据，如 {"nickname": "小明"}
        
        Returns:
            {"status": "success"/"cached", "user_id": "xxx", ...}
        """
        url = f"{self.base_url}/api/v1/user/warmup"
        payload = {
            "user_id": user_id,
            "initial_biz_data": initial_biz_data or {}
        }
        resp = requests.post(url, json=payload, headers=self.headers)
        return resp.json()
    
    def reset(self, user_id: str) -> Dict[str, Any]:
        """删除用户所有数据（不可逆）"""
        url = f"{self.base_url}/api/v1/user/reset"
        payload = {"user_id": user_id}
        resp = requests.post(url, json=payload, headers=self.headers)
        return resp.json()
    
    # ========== 记忆相关 ==========
    
    def get_context(self, user_id: str, query: str, scene: str = None) -> Dict[str, Any]:
        """
        获取记忆上下文
        
        Args:
            user_id: 用户唯一标识
            query: 用户当前的对话内容/问题
            scene: 场景标识，用于过滤 domain_data
        
        Returns:
            {
                "prompts": {"system": "...", "context": "..."},
                "recent_clusters": [...]
            }
        """
        url = f"{self.base_url}/api/v1/memory/context"
        payload = {"user_id": user_id, "query": query}
        if scene:
            payload["scene"] = scene
        resp = requests.post(url, json=payload, headers=self.headers)
        return resp.json()
    
    def process_memory(self, user_id: str, user_message: str, assistant_message: str) -> Dict[str, Any]:
        """
        处理并存储记忆
        
        Args:
            user_id: 用户唯一标识
            user_message: 用户说的话
            assistant_message: AI 的回复
        
        Returns:
            {"status": "accepted", ...}
        """
        url = f"{self.base_url}/api/v1/memory/process"
        payload = {
            "user_id": user_id,
            "user_message": user_message,
            "assistant_message": assistant_message
        }
        resp = requests.post(url, json=payload, headers=self.headers)
        return resp.json()
    
    # ========== 业务数据 ==========
    
    def get_domain_field(self, user_id: str, field: str) -> Any:
        """
        获取用户业务数据字段
        
        Args:
            user_id: 用户唯一标识
            field: domain_data 下的字段名（如 "sleep", "stress"）
        
        Returns:
            字段值，或 None
        """
        url = f"{self.base_url}/api/v1/user/{user_id}/domain/{field}"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code == 200:
            return resp.json()
        return None


# ========== 便捷函数 ==========

def get_memory_context(user_id: str, query: str, api_key: str = None) -> Dict[str, Any]:
    """快捷函数：获取记忆上下文"""
    client = MemSaaSClient(api_key or "your-api-key")
    return client.get_context(user_id, query)


def process_memory(user_id: str, user_message: str, assistant_message: str, api_key: str = None) -> Dict[str, Any]:
    """快捷函数：处理记忆"""
    client = MemSaaSClient(api_key or "your-api-key")
    return client.process_memory(user_id, user_message, assistant_message)
