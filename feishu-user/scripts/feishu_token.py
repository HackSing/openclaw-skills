#!/usr/bin/env python3
"""
飞书用户访问令牌管理脚本

用于获取和刷新飞书用户访问令牌。

用法:
    # 1. 生成授权 URL
    python feishu_token.py --app-id YOUR_APP_ID --app-secret YOUR_SECRET --url
    
    # 2. 使用授权码获取 token
    python feishu_token.py --app-id YOUR_APP_ID --app-secret YOUR_SECRET --code AUTH_CODE
    
    # 3. 刷新 token (自动从配置读取)
    python feishu_token.py --refresh
    
    # 4. 带配置目录
    python feishu_token.py --app-id XXX --app-secret YYY --config-dir /path/to/config --refresh
"""

import argparse
import json
import os
import requests
import sys


DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/claw-feishu-user")


def load_config(config_dir: str = DEFAULT_CONFIG_DIR):
    """加载配置文件"""
    config_path = os.path.join(config_dir, "config.json")
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


def save_config(config: dict, config_dir: str = DEFAULT_CONFIG_DIR):
    """保存配置文件"""
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.json")
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"配置已保存到: {config_path}")


def generate_authorization_url(app_id: str, app_secret: str, redirect_uri: str, config_dir: str = DEFAULT_CONFIG_DIR):
    """生成授权 URL"""
    # 保存 app_id 和 app_secret 以便后续使用
    config = load_config(config_dir)
    config["app_id"] = app_id
    config["app_secret"] = app_secret
    save_config(config, config_dir)
    
    scope = "docx:document drive:drive.search:readonly search:docs:read"
    url = f"https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id={app_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}"
    
    print("=" * 50)
    print("授权 URL (请在浏览器中打开):")
    print(url)
    print("=" * 50)
    print(f"\n授权后会被重定向到: {redirect_uri}?code=XXX")
    print("拿到 code 后，运行:")
    print(f"  python feishu_token.py --app-id {app_id} --app-secret {app_secret} --code 你的CODE")


def get_token_with_code(app_id: str, app_secret: str, code: str, config_dir: str = DEFAULT_CONFIG_DIR):
    """使用授权码获取 token"""
    url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
    
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    print("正在获取 token...")
    resp = requests.post(url, json=payload)
    data = resp.json()
    
    if data.get("code") != 0:
        print(f"错误: {data.get('msg')}")
        sys.exit(1)
    
    result = data.get("data", {})
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")
    
    # 保存配置
    config = load_config(config_dir)
    config["access_token"] = access_token
    config["refresh_token"] = refresh_token
    config["app_id"] = app_id
    config["app_secret"] = app_secret
    save_config(config, config_dir)
    
    print(f"\n✅ Token 获取成功!")
    print(f"access_token: {access_token[:30]}...")
    print(f"refresh_token: {refresh_token[:30]}...")


def refresh_token(config_dir: str = DEFAULT_CONFIG_DIR):
    """刷新 access_token"""
    config = load_config(config_dir)
    
    app_id = config.get("app_id")
    app_secret = config.get("app_secret")
    refresh_token = config.get("refresh_token")
    
    if not all([app_id, app_secret, refresh_token]):
        print("错误: 配置文件中缺少必要信息 (app_id, app_secret, refresh_token)")
        print("请先运行: python feishu_token.py --app-id XXX --app-secret YYY --code YOUR_CODE")
        sys.exit(1)
    
    url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
    
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    print("正在刷新 token...")
    resp = requests.post(url, json=payload)
    data = resp.json()
    
    if data.get("code") != 0:
        print(f"刷新失败: {data.get('msg')}")
        # 如果是 app_id 不匹配，提示用户重新授权
        if "app id not match" in data.get("msg", ""):
            print("\n⚠️ 应用 ID 不匹配，可能需要重新授权")
            print("请运行: python feishu_token.py --app-id XXX --app-secret YYY --code YOUR_CODE")
        sys.exit(1)
    
    result = data.get("data", {})
    access_token = result.get("access_token")
    new_refresh_token = result.get("refresh_token")
    
    # 更新配置
    config["access_token"] = access_token
    config["refresh_token"] = new_refresh_token
    save_config(config, config_dir)
    
    print(f"\n✅ Token 刷新成功!")
    print(f"access_token: {access_token[:30]}...")


def main():
    parser = argparse.ArgumentParser(description="飞书用户访问令牌管理")
    parser.add_argument("--app-id", help="飞书应用 ID")
    parser.add_argument("--app-secret", help="飞书应用密钥")
    parser.add_argument("--redirect-uri", default="http://localhost/callback", help="授权回调地址")
    parser.add_argument("--url", action="store_true", help="生成授权 URL")
    parser.add_argument("--code", help="授权码")
    parser.add_argument("--refresh", action="store_true", help="刷新 token")
    parser.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR, help="配置目录")
    
    args = parser.parse_args()
    
    if args.url:
        if not args.app_id or not args.app_secret:
            print("错误: --url 需要 --app-id 和 --app-secret")
            sys.exit(1)
        generate_authorization_url(args.app_id, args.app_secret, args.redirect_uri, args.config_dir)
    
    elif args.code:
        if not args.app_id or not args.app_secret:
            print("错误: --code 需要 --app-id 和 --app-secret")
            sys.exit(1)
        get_token_with_code(args.app_id, args.app_secret, args.code, args.config_dir)
    
    elif args.refresh:
        refresh_token(args.config_dir)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
