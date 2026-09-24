"""
LifeGrid 壁纸服务本地下载与接口自动化测试
验证通过 URL 请求可正确下载并保存当天的 Style 1 (立柱) 和 Style 3 (腕表年历) 壁纸
"""

import os
import sys
from io import BytesIO
from PIL import Image

# 将项目根目录添加到 sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("✅ /health 接口测试通过")

def test_models_endpoint():
    """测试机型列表接口"""
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 20
    assert "iphone16" in data["models"]
    assert "iphone16pro" in data["models"]
    print(f"✅ /models 接口测试通过，支持机型数量: {data['count']}")

def test_download_today_style1_pillars():
    """测试本地 URL 下载今日 Style 1 (时间立柱) 壁纸"""
    url = "/generate?style=pillars&model=iphone16&download=true"
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "attachment" in response.headers.get("content-disposition", "")
    assert response.headers["x-style"] == "pillars"

    content = response.content
    assert len(content) > 10000, f"文件过小: {len(content)} 字节"

    # 保存到 wallpaper 目录下进行直观校验
    output_path = os.path.join(PROJECT_ROOT, "downloaded_today_pillars.png")
    with open(output_path, "wb") as f:
        f.write(content)

    # 验证是否为合法的 PNG 且分辨率为 1179x2556
    with Image.open(BytesIO(content)) as img:
        assert img.format == "PNG"
        assert img.size == (1179, 2556)
        print(f"✅ Style 1 (时间立柱) 今日壁纸下载测试通过! 保存路径: {output_path}, 分辨率: {img.size}, 大小: {len(content)/1024:.1f} KB")

def test_download_today_style3_dial():
    """测试本地 URL 下载今日 Style 3 (腕表年历) 壁纸"""
    url = "/generate?style=dial&model=iphone16&download=true"
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "attachment" in response.headers.get("content-disposition", "")
    assert response.headers["x-style"] == "dial"

    content = response.content
    assert len(content) > 10000, f"文件过小: {len(content)} 字节"

    # 保存到 wallpaper 目录下进行直观校验
    output_path = os.path.join(PROJECT_ROOT, "downloaded_today_dial.png")
    with open(output_path, "wb") as f:
        f.write(content)

    # 验证是否为合法的 PNG 且分辨率为 1179x2556
    with Image.open(BytesIO(content)) as img:
        assert img.format == "PNG"
        assert img.size == (1179, 2556)
        print(f"✅ Style 3 (腕表年历盘) 今日壁纸下载测试通过! 保存路径: {output_path}, 分辨率: {img.size}, 大小: {len(content)/1024:.1f} KB")

def test_download_zapfino():
    """测试通过 URL 请求 Zapfino 艺术书法字体的 Style 1 与 Style 3 壁纸"""
    # 1. Style 1 Zapfino
    url1 = "/generate?style=pillars&model=iphone16&font=zapfino&download=true"
    resp1 = client.get(url1)
    assert resp1.status_code == 200
    assert resp1.headers["x-font"] == "zapfino"
    out1 = os.path.join(PROJECT_ROOT, "downloaded_today_pillars_zapfino.png")
    with open(out1, "wb") as f:
        f.write(resp1.content)
    with Image.open(BytesIO(resp1.content)) as img:
        assert img.size == (1179, 2556)
    print(f"✅ Style 1 (Zapfino 艺术书法) 测试通过! 文件保存在: {out1}")

    # 2. Style 3 Zapfino
    url3 = "/generate?style=dial&model=iphone16&font=zapfino&download=true"
    resp3 = client.get(url3)
    assert resp3.status_code == 200
    assert resp3.headers["x-font"] == "zapfino"
    out3 = os.path.join(PROJECT_ROOT, "downloaded_today_dial_zapfino.png")
    with open(out3, "wb") as f:
        f.write(resp3.content)
    with Image.open(BytesIO(resp3.content)) as img:
        assert img.size == (1179, 2556)
    print(f"✅ Style 3 (Zapfino 艺术书法) 测试通过! 文件保存在: {out3}")

def test_download_greatvibes():
    """测试通过 URL 请求开源免费商用花体 Great Vibes 的 Style 1 与 Style 3 壁纸"""
    # 1. Style 1 Great Vibes
    url1 = "/generate?style=pillars&model=iphone16&font=greatvibes&download=true"
    resp1 = client.get(url1)
    assert resp1.status_code == 200
    assert resp1.headers["x-font"] == "greatvibes"
    out1 = os.path.join(PROJECT_ROOT, "downloaded_today_pillars_greatvibes.png")
    with open(out1, "wb") as f:
        f.write(resp1.content)
    with Image.open(BytesIO(resp1.content)) as img:
        assert img.size == (1179, 2556)
    print(f"✅ Style 1 (Great Vibes 开源花体) 测试通过! 文件保存在: {out1}")

    # 2. Style 3 Great Vibes
    url3 = "/generate?style=dial&model=iphone16&font=greatvibes&download=true"
    resp3 = client.get(url3)
    assert resp3.status_code == 200
    assert resp3.headers["x-font"] == "greatvibes"
    out3 = os.path.join(PROJECT_ROOT, "downloaded_today_dial_greatvibes.png")
    with open(out3, "wb") as f:
        f.write(resp3.content)
    with Image.open(BytesIO(resp3.content)) as img:
        assert img.size == (1179, 2556)
    print(f"✅ Style 3 (Great Vibes 开源花体) 测试通过! 文件保存在: {out3}")

def test_download_alias_endpoint():
    """测试 /download 便捷下载端点"""
    response = client.get("/download?style=pillars&model=iphone16pro")
    assert response.status_code == 200
    assert "attachment" in response.headers.get("content-disposition", "")
    with Image.open(BytesIO(response.content)) as img:
        assert img.size == (1206, 2622)
    print("✅ /download 便捷端点测试通过 (iPhone 16 Pro 分辨率 1206x2622)")

if __name__ == "__main__":
    print("=== 开始执行 LifeGrid 壁纸本地下载自动化测试 ===")
    test_health_endpoint()
    test_models_endpoint()
    test_download_today_style1_pillars()
    test_download_today_style3_dial()
    test_download_alias_endpoint()
    test_download_zapfino()
    test_download_greatvibes()
    print("🎉 所有本地 URL 下载、开源字体解析与接口校验全部通过！")
