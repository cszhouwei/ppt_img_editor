import hashlib


def compute_sha256(data: bytes) -> str:
    """
    计算数据的 SHA256 哈希值

    Args:
        data: 二进制数据

    Returns:
        str: SHA256 十六进制字符串
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data)
    return sha256_hash.hexdigest()


def compute_file_sha256(file_path: str) -> str:
    """
    计算文件的 SHA256 哈希值

    Args:
        file_path: 文件路径

    Returns:
        str: SHA256 十六进制字符串
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()
