"""
LifeGrid 壁纸服务主入口 (FastAPI)
支持通过 URL 获取样式 1 (时间立柱) 或样式 3 (腕表年历盘) 动态壁纸
"""

import os
import datetime
import zoneinfo
from typing import Optional
from fastapi import FastAPI, Query, Response, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.models_db import IPHONE_MODELS, get_model_specs
from app.generator import generate_wallpaper
from app.cache import WALLPAPER_CACHE

app = FastAPI(
    title="LifeGrid 12-Month Progression Wallpaper API",
    description="支持 Style 1 (时间立柱液位计) 与 Style 3 (瑞士腕表年历光环) 的 iPhone 纯黑 OLED 动态壁纸服务",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_date(country: str = "cn", tz_name: Optional[str] = None) -> datetime.date:
    tz = None
    if tz_name:
        try:
            tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            pass
    if tz is None:
        if (country or "").lower() in ["cn", "china", "zh"]:
            tz = zoneinfo.ZoneInfo("Asia/Shanghai")
        else:
            tz = zoneinfo.ZoneInfo("UTC")
    return datetime.datetime.now(tz).date()

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok", "service": "lifegrid-wallpaper", "version": "2.0.0", "time": datetime.datetime.utcnow().isoformat()}

@app.get("/models")
def list_models():
    return {
        "count": len(IPHONE_MODELS),
        "models": IPHONE_MODELS
    }

def generate_wallpaper_response(
    request: Request,
    style: str = "pillars",
    model: Optional[str] = "iphone16",
    width: Optional[int] = None,
    height: Optional[int] = None,
    font: str = "avenir",
    bg: str = "000000",
    accent: str = "FFFFFF",
    lang: str = "en",
    download: bool = False,
    country: str = "cn",
    tz: Optional[str] = None,
    date: Optional[str] = None,
) -> Response:
    # 安全处理字符串与默认参数
    raw_date = date if isinstance(date, str) else None
    raw_country = country if isinstance(country, str) else "cn"
    raw_tz = tz if isinstance(tz, str) else None

    # 解析日期
    if raw_date and raw_date.strip():
        try:
            target_date = datetime.date.fromisoformat(raw_date.strip())
        except ValueError:
            target_date = get_current_date(raw_country, raw_tz)
    else:
        target_date = get_current_date(raw_country, raw_tz)

    # 安全处理数值与字符串
    model_str = model if isinstance(model, str) else "iphone16"
    width_val = width if isinstance(width, int) else None
    height_val = height if isinstance(height, int) else None
    font_str = (font if isinstance(font, str) else "avenir").lower().strip()
    bg_str = bg if isinstance(bg, str) else "000000"
    accent_str = accent if isinstance(accent, str) else "FFFFFF"
    lang_str = lang if isinstance(lang, str) else "en"
    style_str = style if isinstance(style, str) else "pillars"
    download_bool = bool(download)

    # 获取机型尺寸
    specs = get_model_specs(model_str, custom_width=width_val, custom_height=height_val)
    final_width = specs["width"]
    final_height = specs["height"]

    # 规范化 style
    norm_style = "dial" if style_str.lower() in ["dial", "3", "ring", "circle"] else "pillars"

    cache_params = {
        "date": str(target_date),
        "style": norm_style,
        "width": final_width,
        "height": final_height,
        "font": font_str,
        "bg": bg_str.upper().lstrip("#"),
        "accent": accent_str.upper().lstrip("#"),
        "lang": lang_str.lower(),
    }

    # 检查内存缓存
    cached = WALLPAPER_CACHE.get(cache_params)
    if cached:
        png_data, etag = cached
        headers = {
            "Content-Type": "image/png",
            "Cache-Control": "public, max-age=86400, stale-while-revalidate=3600",
            "ETag": etag,
            "X-Cache": "HIT",
            "X-Style": norm_style,
            "X-Font": font_str,
            "X-Model": specs.get("name", "Custom"),
            "X-Dimensions": f"{final_width}x{final_height}",
        }
        if download_bool:
            headers["Content-Disposition"] = f'attachment; filename="lifegrid_{norm_style}_{target_date}.png"'
        
        client_etag = request.headers.get("if-none-match") if request else None
        if client_etag and client_etag == etag:
            return Response(status_code=304, headers=headers)
        return Response(content=png_data, media_type="image/png", headers=headers)

    # 渲染壁纸
    png_data = generate_wallpaper(
        width=final_width,
        height=final_height,
        style=norm_style,
        font=font_str,
        bg_hex=bg_str,
        accent_hex=accent_str,
        lang=lang_str,
        target_date=target_date,
    )

    etag = WALLPAPER_CACHE.set(cache_params, png_data)

    headers = {
        "Content-Type": "image/png",
        "Cache-Control": "public, max-age=86400, stale-while-revalidate=3600",
        "ETag": etag,
        "X-Cache": "MISS",
        "X-Style": norm_style,
        "X-Font": font_str,
        "X-Model": specs.get("name", "Custom"),
        "X-Dimensions": f"{final_width}x{final_height}",
    }
    if download_bool:
        headers["Content-Disposition"] = f'attachment; filename="lifegrid_{norm_style}_{target_date}.png"'

    return Response(content=png_data, media_type="image/png", headers=headers)

@app.api_route("/generate", methods=["GET", "HEAD"])
def generate_endpoint(
    request: Request,
    style: str = Query("pillars", description="壁纸样式: pillars(样式1:时间立柱液位计) 或 dial(样式3:瑞士腕表年历盘)"),
    model: Optional[str] = Query("iphone16", description="iPhone 机型标识 (如 iphone16, iphone16pro, iphone16promax, iphone15 等)"),
    width: Optional[int] = Query(None, description="自定义宽度 (px)"),
    height: Optional[int] = Query(None, description="自定义高度 (px)"),
    font: str = Query("greatvibes", description="数字与排印字体: greatvibes(开源顶级艺术花体·推荐·公网商用免费), pinyon(开源浪漫花体), zapfino(苹果商业花体), avenir(现代高级腕表几何), sf(苹果原生), futura(包豪斯)"),
    bg: str = Query("000000", description="背景十六进制颜色 (默认 000000)"),
    accent: str = Query("FFFFFF", description="高亮强调色 (默认 FFFFFF)"),
    lang: str = Query("en", description="文案语言: en(英文) 或 zh(中文)"),
    download: bool = Query(False, description="是否以附件形式触发直接下载"),
    country: str = Query("cn", description="国家代码用于时区推断 (默认 cn)"),
    tz: Optional[str] = Query(None, description="明确指定的时区 (如 Asia/Shanghai)"),
    date: Optional[str] = Query(None, description="指定测试日期 YYYY-MM-DD"),
):
    return generate_wallpaper_response(
        request=request,
        style=style,
        model=model,
        width=width,
        height=height,
        font=font,
        bg=bg,
        accent=accent,
        lang=lang,
        download=download,
        country=country,
        tz=tz,
        date=date,
    )

@app.api_route("/download", methods=["GET", "HEAD"])
def download_endpoint(
    request: Request,
    style: str = Query("pillars"),
    model: Optional[str] = Query("iphone16"),
    font: str = Query("greatvibes"),
    lang: str = Query("en"),
    bg: str = Query("000000"),
    accent: str = Query("FFFFFF"),
):
    """直接下载当天的壁纸文件快捷入口"""
    return generate_wallpaper_response(
        request=request,
        style=style,
        model=model,
        font=font,
        lang=lang,
        bg=bg,
        accent=accent,
        download=True
    )

# 挂载 Web 页面与客户端
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

@app.get("/client")
def client_app():
    """iPhone 纯前端 Zapfino 极速渲染客户端"""
    client_file = os.path.join(static_path, "client.html")
    if os.path.exists(client_file):
        return FileResponse(client_file)
    return Response(content="Client page not found", status_code=404)

if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
