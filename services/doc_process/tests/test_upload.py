import io
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "doc_process"


def test_upload_asset_success(client: TestClient, sample_image_bytes):
    """测试成功上传图片"""
    files = {"file": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
    response = client.post("/v1/assets/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    # 验证响应字段
    assert "asset_id" in data
    assert data["asset_id"].startswith("ast_")
    assert "image_url" in data
    assert "width" in data
    assert "height" in data
    assert "sha256" in data
    assert len(data["sha256"]) == 64  # SHA256 长度


def test_upload_invalid_file_type(client: TestClient):
    """测试上传非图片文件"""
    files = {"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
    response = client.post("/v1/assets/upload", files=files)

    assert response.status_code == 400
    assert "must be an image" in response.json()["detail"]
