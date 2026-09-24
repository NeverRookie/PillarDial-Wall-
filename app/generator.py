"""
LifeGrid 壁纸生成核心引擎 (2.0 超高保真 1:1 还原版)
精准还原：
- Style 1 (pillars): 12 根时间立柱液位计 (Monolithic Pillars)
  - 12 根圆角胶囊横向排列，避让锁屏时钟
  - 前 N 月 100% 充盈白光并具备多级多通道大气泛光 (Ambient Halo & Bloom)
  - 当月按天数百分比从底部向上液位充盈，顶部具备柔美圆角倒角
  - 后 N 月具备暗灰透明轮廓
  - 底部极简 Swiss Typography 排印
- Style 3 (dial): 瑞士高级钟表 12 扇区年历光环罗盘 (Grand Chronometer Dial)
  - 纯黑 OLED 背景下的微倒角 12 扇区网格轮廓
  - 激活月份数字纯白高亮并自发光发散微光环
  - 外圈具备完美分离无交错的 12 段弯曲胶囊发光弧
  - 过去月份 100% 点亮，当月动态弧光充盈，未充盈部分细线暗廓
  - 中央超轻 (UltraLight) 悬浮倒数大字与字间距微调副标题
"""

import io
import os
import math
import datetime
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

# 项目内置字体资源目录 (随容器镜像分发，确保 Linux 公网服务器无缝可用)
ASSETS_FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")

# 多字体族候选路径 (支持开源商用花体、macOS 系统字体与 Linux 容器跨平台回退)
FONT_FAMILY_PATHS = {
    # 1. 顶级开源免费商用花体 (SIL Open Font License)
    "greatvibes": [
        os.path.join(ASSETS_FONTS_DIR, "GreatVibes-Regular.ttf"),
    ],
    "pinyon": [
        os.path.join(ASSETS_FONTS_DIR, "PinyonScript-Regular.ttf"),
    ],
    "alexbrush": [
        os.path.join(ASSETS_FONTS_DIR, "AlexBrush-Regular.ttf"),
    ],
    "allura": [
        os.path.join(ASSETS_FONTS_DIR, "Allura-Regular.ttf"),
    ],
    "tangerine": [
        os.path.join(ASSETS_FONTS_DIR, "Tangerine-Bold.ttf"),
        os.path.join(ASSETS_FONTS_DIR, "Tangerine-Regular.ttf"),
    ],

    # 2. Zapfino 请求安全合规重定向:
    # 由于 Zapfino 属于 Monotype 商业专有字体软件，云端不内置或分发任何专有字体文件；
    # 若客户端指定 zapfino，服务端安全平滑映射至顶级开源商用花体 Great Vibes (SIL OFL 1.1)，彻底消除侵权索赔风险。
    "zapfino": [
        os.path.join(ASSETS_FONTS_DIR, "GreatVibes-Regular.ttf"),
    ],

    # 3. 现代工整极简与系统制表字体
    "avenir": [
        "/System/Library/Fonts/Avenir Next.ttc",
        "/System/Library/Fonts/Supplemental/Avenir.ttc",
    ],
    "sf": [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFNSText.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/SFNSRounded.ttf",
    ],
    "futura": [
        "/System/Library/Fonts/Supplemental/Futura.ttc",
        "/Library/Fonts/Futura.ttc",
    ],
    "helvetica": [
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ],
}

# 书法花体家族集合标识
CALLIGRAPHY_FAMILIES = {
    "zapfino", "greatvibes", "great_vibes", "gv", "vibes",
    "pinyon", "pinyonscript", "pinyon_script",
    "alexbrush", "allura", "tangerine"
}

FONT_LINUX_FALLBACKS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]

ZH_FONTS_SANS = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]

def find_first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

FONT_ZH_PATH = find_first_existing(ZH_FONTS_SANS)

def get_font(
    family: str = "avenir",
    size: int = 24,
    weight: str = "regular",
    is_zh: bool = False
) -> ImageFont.FreeTypeFont:
    """
    根据字体族和字重获取高精美学字体：
    - avenir (默认): Avenir Next，现代几何与顶级腕表极简美学 (极细 UltraLight，正圆弧形数字)
    - sf: 苹果 iOS 原生系统字体 (SF Pro)
    - futura: 包豪斯现代主义几何数字
    - helvetica: 经典瑞士国际排印风格
    支持 Linux 容器及无头环境自动平滑降级。
    """
    s = max(8, int(size))
    w = (weight or "regular").lower()
    fam = (family or "avenir").lower().strip()

    if is_zh and FONT_ZH_PATH:
        try:
            return ImageFont.truetype(FONT_ZH_PATH, s)
        except Exception:
            pass

    # 1. 尝试选定字体族
    fam_candidates = FONT_FAMILY_PATHS.get(fam, [])
    chosen_path = find_first_existing(fam_candidates)

    # 2. 如果选定字体不存在，按优先级回退: avenir -> helvetica -> sf -> futura
    if not chosen_path:
        for fallback_fam in ["avenir", "helvetica", "sf", "futura"]:
            chosen_path = find_first_existing(FONT_FAMILY_PATHS[fallback_fam])
            if chosen_path:
                fam = fallback_fam
                break

    # 3. 如果依然未找到（如在精简版 Linux 容器），尝试 Linux 通用字体
    if not chosen_path:
        chosen_path = find_first_existing(FONT_LINUX_FALLBACKS)
        if chosen_path:
            try:
                return ImageFont.truetype(chosen_path, s)
            except Exception:
                pass
        return ImageFont.load_default()

    # 4. 根据字体家族与 TTC 索引提取精确字重
    try:
        if fam == "avenir":
            # Avenir Next.ttc: 10: UltraLight, 7: Regular, 5: Medium, 2: Demi Bold, 0: Bold
            weight_indices = {
                "ultralight": 10,
                "thin": 10,
                "light": 7,
                "regular": 7,
                "medium": 5,
                "demibold": 2,
                "bold": 0,
            }
            idx = weight_indices.get(w, 7)
            return ImageFont.truetype(chosen_path, s, index=idx)

        elif fam == "helvetica":
            # Helvetica Neue.ttc: 5: UltraLight, 12: Thin, 7: Light, 0: Regular, 10: Medium, 1: Bold
            weight_indices = {
                "ultralight": 5,
                "thin": 12,
                "light": 7,
                "regular": 0,
                "medium": 10,
                "bold": 1,
            }
            idx = weight_indices.get(w, 0)
            return ImageFont.truetype(chosen_path, s, index=idx)

        elif fam == "futura":
            # Futura.ttc: 0: Medium, 2: Bold
            idx = 2 if w in ["bold", "demibold"] else 0
            return ImageFont.truetype(chosen_path, s, index=idx)

        elif fam == "sf":
            # SFNS.ttf 单一字重或变体直接加载
            return ImageFont.truetype(chosen_path, s)

        elif fam == "zapfino":
            # Zapfino.ttf 古典艺术花体直接加载
            return ImageFont.truetype(chosen_path, s)

        else:
            return ImageFont.truetype(chosen_path, s)

    except Exception:
        # TTC 索引解析失败时的安全降级尝试
        try:
            return ImageFont.truetype(chosen_path, s, index=0)
        except Exception:
            try:
                return ImageFont.truetype(chosen_path, s)
            except Exception:
                return ImageFont.load_default()

def get_font_by_weight(size: int, weight: str = "regular", is_zh: bool = False):
    """向后兼容辅助函数"""
    return get_font(family="avenir", size=size, weight=weight, is_zh=is_zh)

def parse_hex_color(hex_str: str, default: Tuple[int, int, int]) -> Tuple[int, int, int, int]:
    if not hex_str:
        return (*default, 255)
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        s = "".join([c*2 for c in s])
    if len(s) == 6:
        try:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)
        except ValueError:
            pass
    return (*default, 255)

def is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def get_days_in_month(year: int, month: int) -> int:
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month in [4, 6, 9, 11]:
        return 30
    return 29 if is_leap_year(year) else 28

def draw_tracked_text(draw, text: str, center_x: float, center_y: float, font, fill, letter_spacing: float = 2.5):
    """
    绘制带精确字间距微调 (Tracking) 的居中文本
    """
    chars = list(text)
    char_widths = []
    for c in chars:
        bbox = font.getbbox(c)
        w = bbox[2] - bbox[0]
        char_widths.append(w)

    total_w = sum(char_widths) + letter_spacing * (len(chars) - 1)
    std_bbox = font.getbbox("1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    char_h = std_bbox[3] - std_bbox[1]

    start_x = center_x - total_w / 2.0
    baseline_y = center_y - char_h / 2.0 - std_bbox[1]

    curr_x = start_x
    for i, c in enumerate(chars):
        draw.text((curr_x, baseline_y), c, fill=fill, font=font)
        curr_x += char_widths[i] + letter_spacing

def apply_neon_glow(emission_img: Image.Image, wide_r: int = 48, mid_r: int = 20, tight_r: int = 7) -> Image.Image:
    """
    四级多尺度高斯泛光合成 (Ultra-wide Bloom + Mid Halo + Core Corona)
    真实还原 OLED 自发光穿透与柔美空气光晕
    """
    W, H = emission_img.size
    h_ultra = emission_img.filter(ImageFilter.GaussianBlur(radius=int(wide_r * 1.6)))
    h_wide = emission_img.filter(ImageFilter.GaussianBlur(radius=wide_r))
    h_mid = emission_img.filter(ImageFilter.GaussianBlur(radius=mid_r))
    h_tight = emission_img.filter(ImageFilter.GaussianBlur(radius=tight_r))

    result = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for layer, alpha_mult in [(h_ultra, 0.28), (h_wide, 0.48), (h_mid, 0.68), (h_tight, 0.92)]:
        r, g, b, a = layer.split()
        a = a.point(lambda p: int(p * alpha_mult))
        result = Image.alpha_composite(result, Image.merge("RGBA", (r, g, b, a)))

    result = Image.alpha_composite(result, emission_img)
    return result

def draw_curved_capsule(draw, cx: float, cy: float, r_mid: float, start_deg: float, end_deg: float, cap_r: float, fill_color):
    """
    沿圆弧绘制两端为正圆倒角的发光弯曲胶囊条
    """
    deg = start_deg
    step_deg = 0.3
    while deg <= end_deg:
        rad = math.radians(deg)
        x = cx + r_mid * math.cos(rad)
        y = cy + r_mid * math.sin(rad)
        draw.ellipse([x - cap_r, y - cap_r, x + cap_r, y + cap_r], fill=fill_color)
        deg += step_deg
    rad_end = math.radians(end_deg)
    x_end = cx + r_mid * math.cos(rad_end)
    y_end = cy + r_mid * math.sin(rad_end)
    draw.ellipse([x_end - cap_r, y_end - cap_r, x_end + cap_r, y_end + cap_r], fill=fill_color)

def draw_curved_capsule_outline_morph(target_img: Image.Image, cx: float, cy: float, r_mid: float, start_deg: float, end_deg: float, cap_r: float, outline_color, stroke_w: int = 2):
    """
    使用形态学边缘提取绘制 100% 毫无数学自交交叠与视觉毛刺的平滑胶囊外廓
    """
    W, H = target_img.size
    mask = Image.new("L", (W, H), 0)
    d_mask = ImageDraw.Draw(mask)
    draw_curved_capsule(d_mask, cx, cy, r_mid, start_deg, end_deg, cap_r, fill_color=255)

    filter_size = max(3, stroke_w * 2 - 1)
    eroded = mask.filter(ImageFilter.MinFilter(filter_size))
    outline = ImageChops.subtract(mask, eroded)

    color_layer = Image.new("RGBA", (W, H), outline_color)
    target_img.paste(color_layer, (0, 0), outline)

def generate_wallpaper(
    width: int = 1179,
    height: int = 2556,
    style: str = "pillars",
    font: str = "avenir",
    bg_hex: str = "000000",
    accent_hex: str = "FFFFFF",
    lang: str = "en",
    target_date: Optional[datetime.date] = None,
) -> bytes:
    """
    生成 Style 1 或 Style 3 像素级 1:1 动态壁纸二进制流
    """
    if target_date is None:
        target_date = datetime.date.today()

    year = target_date.year
    month = target_date.month
    day = target_date.day

    is_leap = is_leap_year(year)
    total_days_year = 366 if is_leap else 365
    day_of_year = (target_date - datetime.date(year, 1, 1)).days + 1
    days_left = max(0, total_days_year - day_of_year)
    year_progress_pct = int(round((day_of_year / total_days_year) * 100))

    days_in_cur_month = get_days_in_month(year, month)
    month_progress = min(1.0, max(0.0, day / days_in_cur_month))

    c_bg = parse_hex_color(bg_hex, (0, 0, 0))
    c_accent = parse_hex_color(accent_hex, (255, 255, 255))
    is_zh = (lang or "").lower() in ["zh", "cn", "chinese"]

    # 基准缩放因子 (以标准 1179x2556 为参考)
    scale_w = width / 1179.0
    scale_h = height / 2556.0

    img = Image.new("RGBA", (width, height), c_bg)
    draw_base = ImageDraw.Draw(img)

    emission = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_emit = ImageDraw.Draw(emission)

    norm_style = str(style).lower()

    if norm_style in ["pillars", "1", "pillar", "bar", "bars"]:
        # ==========================================
        # 样式 1: 时间立柱液位计 (Monolithic Pillars)
        # ==========================================
        num_pillars = 12
        total_w = int(width * 0.814)
        pill_w = int(total_w / (num_pillars + (num_pillars - 1) * 0.72))
        pill_gap = int(pill_w * 0.72)
        actual_total_w = num_pillars * pill_w + (num_pillars - 1) * pill_gap
        start_x = (width - actual_total_w) // 2

        pill_h = int(height * 0.268)
        start_y = int(height * 0.364) # 完美避开 iPhone 锁屏时钟
        end_y = start_y + pill_h
        corner_r = pill_w // 2

        # 1. 绘制未满柱子的暗灰背景线框
        outline_color = (48, 52, 60, 255)
        for m in range(1, 13):
            px0 = start_x + (m - 1) * (pill_w + pill_gap)
            px1 = px0 + pill_w
            if m >= month:
                draw_base.rounded_rectangle([px0, start_y, px1, end_y], radius=corner_r, outline=outline_color, width=max(2, int(2 * scale_w)))

        # 2. 绘制发光立柱 (发射层)
        for m in range(1, 13):
            px0 = start_x + (m - 1) * (pill_w + pill_gap)
            px1 = px0 + pill_w

            if m < month:
                # 已经过去的月份: 100% 满格高亮发光
                draw_emit.rounded_rectangle([px0, start_y, px1, end_y], radius=corner_r, fill=c_accent)
            elif m == month:
                # 当前月份: 根据天数进度自底向上充盈液位
                fill_h = int(pill_h * month_progress)
                fill_top = end_y - fill_h
                if fill_h >= pill_w:
                    draw_emit.rounded_rectangle([px0, fill_top, px1, end_y], radius=corner_r, fill=c_accent)
                elif fill_h > 0:
                    draw_emit.rounded_rectangle([px0, end_y - pill_w, px1, end_y], radius=corner_r, fill=c_accent)

        # 3. 对发射层施加多级高斯泛光
        glow_composite = apply_neon_glow(emission, wide_r=int(46 * scale_w), mid_r=int(18 * scale_w), tight_r=max(4, int(6 * scale_w)))
        img = Image.alpha_composite(img, glow_composite)

        # 4. 底部极简西文排印 (全面避免中文字符以保证视觉纯粹与高级感)
        draw_final = ImageDraw.Draw(img)
        text_y = end_y + int(height * 0.048)

        is_calligraphy = (font or "").lower().strip() in CALLIGRAPHY_FAMILIES
        font_key = (font or "").lower().strip()
        if is_calligraphy:
            text_str = f"{days_left} Days Left · {year_progress_pct}%"
            if font_key in ["greatvibes", "great_vibes", "gv", "vibes", "zapfino"]:
                f_size = int(96 * scale_w)
            elif font_key in ["pinyon", "pinyonscript"]:
                f_size = int(84 * scale_w)
            else:
                f_size = int(54 * scale_w)
            font_text = get_font(family=font, size=f_size)
            bbox_t = font_text.getbbox(text_str)
            tw = bbox_t[2] - bbox_t[0]
            th = bbox_t[3] - bbox_t[1]
            tx = width / 2.0 - tw / 2.0 - bbox_t[0]
            ty = text_y + int(18 * scale_h) - th / 2.0 - bbox_t[1]
            draw_final.text((tx, ty), text_str, fill=(245, 245, 248, 255), font=font_text)
        else:
            text_str = f"{days_left} DAYS LEFT · {year_progress_pct}%"
            font_text = get_font(family=font, size=int(44 * scale_w), weight="light")
            draw_tracked_text(draw_final, text_str, width / 2.0, text_y + int(20 * scale_h), font_text, (245, 245, 248, 255), letter_spacing=2.5 * scale_w)

    else:
        # ==========================================
        # 样式 3: 瑞士腕表年历盘 (Grand Chronometer Dial)
        # ==========================================
        cx = width / 2.0
        cy = height * 0.495 # 黄金分割黄金居中

        r_sec_in = width * 0.282
        r_sec_out = width * 0.392

        cap_r = width * 0.0148
        r_arc_mid = width * 0.428

        cap_angular_extent = math.degrees(cap_r / r_arc_mid) # ~1.98度
        desired_tip_gap = 2.4
        delta_arc = cap_angular_extent + desired_tip_gap / 2.0 # ~3.18度
        sec_gap = 2.2

        is_calligraphy = (font or "").lower().strip() in CALLIGRAPHY_FAMILIES
        font_key = (font or "").lower().strip()
        if is_calligraphy:
            if font_key in ["greatvibes", "great_vibes", "gv", "vibes", "zapfino"]:
                font_month_active = get_font(family=font, size=int(76 * scale_w))
                font_month_past = get_font(family=font, size=int(70 * scale_w))
                font_month_future = get_font(family=font, size=int(66 * scale_w))
            elif font_key in ["pinyon", "pinyonscript"]:
                font_month_active = get_font(family=font, size=int(68 * scale_w))
                font_month_past = get_font(family=font, size=int(62 * scale_w))
                font_month_future = get_font(family=font, size=int(58 * scale_w))
            else:
                font_month_active = get_font(family=font, size=int(46 * scale_w))
                font_month_past = get_font(family=font, size=int(42 * scale_w))
                font_month_future = get_font(family=font, size=int(38 * scale_w))
        else:
            font_month_active = get_font(family=font, size=int(46 * scale_w), weight="medium")
            font_month_past = get_font(family=font, size=int(44 * scale_w), weight="regular" if font == "avenir" else "light")
            font_month_future = get_font(family=font, size=int(42 * scale_w), weight="ultralight" if font == "avenir" else "light")

        # 1. 绘制当前月份与未来月份的暗灰胶囊轮廓
        for m in range(month, 13):
            deg_start = 270.0 + (m - 1) * 30.0
            deg_end = 270.0 + m * 30.0
            a_start = deg_start + delta_arc
            a_end = deg_end - delta_arc
            outline_c = (50, 55, 65, 255) if m == month else (36, 40, 48, 255)
            draw_curved_capsule_outline_morph(img, cx, cy, r_arc_mid, a_start, a_end, cap_r, outline_color=outline_c, stroke_w=max(2, int(2 * scale_w)))

        for m in range(1, 13):
            deg_start = 270.0 + (m - 1) * 30.0
            deg_end = 270.0 + m * 30.0
            deg_mid = (deg_start + deg_end) / 2.0

            # --- A. 绘制内圈 12 扇区网格轮廓 ---
            b_start = deg_start + sec_gap / 2.0
            b_end = deg_end - sec_gap / 2.0

            rad_steps = [math.radians(deg) for deg in [b_start + i * 1.5 for i in range(int((b_end - b_start) / 1.5) + 1)]]
            rad_steps.append(math.radians(b_end))

            poly_outer = [(cx + r_sec_out * math.cos(rad), cy + r_sec_out * math.sin(rad)) for rad in rad_steps]
            poly_inner = [(cx + r_sec_in * math.cos(rad), cy + r_sec_in * math.sin(rad)) for rad in reversed(rad_steps)]
            sector_poly = poly_outer + poly_inner

            if m == month:
                draw_base.polygon(sector_poly, outline=(85, 92, 105, 255), width=max(2, int(2 * scale_w)))
            else:
                draw_base.polygon(sector_poly, outline=(42, 46, 54, 255), width=max(2, int(2 * scale_w)))

            # --- B. 绘制内圈月份数字 1~12 ---
            r_num = (r_sec_in + r_sec_out) / 2.0
            num_x = cx + r_num * math.cos(math.radians(deg_mid))
            num_y = cy + r_num * math.sin(math.radians(deg_mid))

            text_m = str(m)
            f_use = font_month_active if m == month else (font_month_past if m < month else font_month_future)
            f_box = f_use.getbbox(text_m)
            tw, th = f_box[2] - f_box[0], f_box[3] - f_box[1]
            tx = num_x - tw / 2.0 - f_box[0]
            ty = num_y - th / 2.0 - f_box[1]

            if m < month:
                draw_base.text((tx, ty), text_m, fill=(215, 220, 230, 255), font=f_use)
            elif m == month:
                # 当前月数字高亮发光
                draw_base.text((tx, ty), text_m, fill=c_accent, font=f_use)
                draw_emit.text((tx, ty), text_m, fill=c_accent, font=f_use)
            else:
                draw_base.text((tx, ty), text_m, fill=(65, 70, 80, 255), font=f_use)

            # --- C. 绘制外圈月度发光弧线 ---
            a_start = deg_start + delta_arc
            a_end = deg_end - delta_arc
            a_span = a_end - a_start

            if m < month:
                draw_curved_capsule(draw_emit, cx, cy, r_arc_mid, a_start, a_end, cap_r, fill_color=c_accent)
            elif m == month:
                fill_span = a_span * month_progress
                fill_end = a_start + fill_span
                if fill_span > 0:
                    draw_curved_capsule(draw_emit, cx, cy, r_arc_mid, a_start, fill_end, cap_r, fill_color=c_accent)

        # 2. 对发射层施加多级高斯泛光
        glow_composite = apply_neon_glow(emission, wide_r=int(48 * scale_w), mid_r=int(20 * scale_w), tight_r=max(4, int(7 * scale_w)))
        img = Image.alpha_composite(img, glow_composite)

        # 3. 绘制中心宏伟极简排版: "100" 与 "Days Left in 2026" (纯英文，杜绝中文字符)
        draw_final = ImageDraw.Draw(img)

        if is_calligraphy:
            if font_key in ["greatvibes", "great_vibes", "gv", "vibes", "zapfino"]:
                c_size = int(420 * scale_w)
                sub_size = int(68 * scale_w)
                days_y_offset = 64.0 * scale_h
                sub_y_offset = int(112 * scale_h)
            elif font_key in ["pinyon", "pinyonscript"]:
                c_size = int(360 * scale_w)
                sub_size = int(64 * scale_w)
                days_y_offset = 50.0 * scale_h
                sub_y_offset = int(108 * scale_h)
            else:
                c_size = int(210 * scale_w)
                sub_size = int(36 * scale_w)
                days_y_offset = 36.0 * scale_h
                sub_y_offset = int(105 * scale_h)

            font_days = get_font(family=font, size=c_size)
            font_sub = get_font(family=font, size=sub_size)
            text_days = str(days_left)
            text_sub = f"Days Left in {year}"

            bbox_days = font_days.getbbox(text_days)
            dw = bbox_days[2] - bbox_days[0]
            dh = bbox_days[3] - bbox_days[1]
            dx = cx - dw / 2.0 - bbox_days[0]
            dy = cy - days_y_offset - dh / 2.0 - bbox_days[1]
            draw_final.text((dx, dy), text_days, fill=(255, 255, 255, 255), font=font_days)

            bbox_sub = font_sub.getbbox(text_sub)
            sw = bbox_sub[2] - bbox_sub[0]
            sh = bbox_sub[3] - bbox_sub[1]
            sx = cx - sw / 2.0 - bbox_sub[0]
            sy = cy + sub_y_offset - sh / 2.0 - bbox_sub[1]
            draw_final.text((sx, sy), text_sub, fill=(195, 200, 210, 255), font=font_sub)
        else:
            font_days = get_font(family=font, size=int(195 * scale_w), weight="ultralight")
            font_sub = get_font(family=font, size=int(26 * scale_w), weight="regular")
            text_days = str(days_left)
            text_sub = f"DAYS LEFT IN {year}"

            bbox_days = font_days.getbbox(text_days)
            dw = bbox_days[2] - bbox_days[0]
            dh = bbox_days[3] - bbox_days[1]
            dx = cx - dw / 2.0 - bbox_days[0]
            dy = cy - 36.0 * scale_h - dh / 2.0 - bbox_days[1]
            draw_final.text((dx, dy), text_days, fill=(255, 255, 255, 255), font=font_days)

            draw_tracked_text(draw_final, text_sub, cx, cy + int(92 * scale_h), font_sub, (185, 190, 200, 255), letter_spacing=2.8 * scale_w)

    # 导出并保存为优化 PNG
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()
