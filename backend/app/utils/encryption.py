"""
GBSkillEngine API Key加密工具

使用Fernet对称加密保护敏感信息（如API Key）
"""
import base64
import os
import secrets
from typing import Tuple, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings


class EncryptionError(Exception):
    """加密/解密错误"""
    pass


def _get_encryption_key() -> bytes:
    """
    获取加密密钥
    
    从环境变量获取密钥，如果未设置则生成一个警告
    """
    key = settings.llm_encryption_key
    if not key:
        # 开发环境使用默认密钥，生产环境应该配置
        key = "gbskillengine-default-encryption-key-change-in-production"
    
    # 使用PBKDF2派生固定长度的密钥
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"gbskillengine-salt",  # 固定salt，确保相同密钥生成相同派生密钥
        iterations=100000,
    )
    derived_key = kdf.derive(key.encode())
    return base64.urlsafe_b64encode(derived_key)


def encrypt_api_key(plain_key: str) -> Tuple[str, str]:
    """
    加密API Key
    
    Args:
        plain_key: 明文API Key
        
    Returns:
        Tuple[encrypted_data, iv]: 加密后的数据和初始化向量（Base64编码）
        
    Raises:
        EncryptionError: 加密失败时抛出
    """
    if not plain_key:
        raise EncryptionError("API Key不能为空")
    
    try:
        # 生成随机IV用于标识
        iv = secrets.token_urlsafe(16)
        
        # 使用Fernet加密
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(plain_key.encode())
        
        return encrypted.decode(), iv
    except Exception as e:
        raise EncryptionError(f"加密失败: {str(e)}")


def decrypt_api_key(encrypted_data: str, iv: str) -> str:
    """
    解密API Key
    
    Args:
        encrypted_data: 加密后的数据（Base64编码）
        iv: 初始化向量（用于验证，实际Fernet内部处理）
        
    Returns:
        解密后的明文API Key
        
    Raises:
        EncryptionError: 解密失败时抛出
    """
    if not encrypted_data:
        raise EncryptionError("加密数据不能为空")
    
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except Exception as e:
        raise EncryptionError(f"解密失败: {str(e)}")


def mask_api_key(api_key: str) -> str:
    """
    对API Key进行脱敏处理
    
    Args:
        api_key: 原始API Key
        
    Returns:
        脱敏后的字符串，如 "sk-****XXXX"
    """
    if not api_key:
        return ""
    
    if len(api_key) <= 8:
        return "*" * len(api_key)
    
    # 保留前4位和后4位
    prefix = api_key[:4]
    suffix = api_key[-4:]
    masked_middle = "*" * 4
    
    return f"{prefix}{masked_middle}{suffix}"


def generate_encryption_key() -> str:
    """
    生成新的加密密钥
    
    用于初始化或密钥轮换
    
    Returns:
        Base64编码的加密密钥
    """
    return Fernet.generate_key().decode()


def validate_api_key_format(api_key: str, provider: str) -> bool:
    """
    验证API Key格式是否符合供应商要求
    
    Args:
        api_key: API Key
        provider: 供应商名称
        
    Returns:
        是否格式正确
    """
    if not api_key:
        return False
    
    # 基本长度检查
    if len(api_key) < 10:
        return False
    
    # 供应商特定格式检查
    provider_patterns = {
        "openai": lambda k: k.startswith(("sk-", "sk-proj-")),
        "anthropic": lambda k: k.startswith("sk-ant-"),
        "baidu": lambda k: len(k) >= 20,  # 百度API Key通常较长
        "aliyun": lambda k: len(k) >= 20,  # 阿里云API Key
        "local": lambda k: True,  # 本地模型可能不需要Key
    }
    
    validator = provider_patterns.get(provider.lower(), lambda k: True)
    return validator(api_key)
