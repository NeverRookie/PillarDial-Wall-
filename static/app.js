/**
 * LifeGrid 动态壁纸 Web 交互、机型智能检测与快捷指令自动化生成逻辑
 */

document.addEventListener('DOMContentLoaded', () => {
  // 从 URL 参数读取隐藏预设
  const urlParams = new URLSearchParams(window.location.search);
  const initialFont = (urlParams.get('font') || 'greatvibes').toLowerCase();

  // 当前配置状态 (默认首推 Style 3 瑞士腕表年历盘 + Great Vibes 开源艺术花体)
  const state = {
    style: urlParams.get('style') || 'dial',
    model: urlParams.get('model') || 'iphone16pro',
    font: initialFont, // 支持隐藏调用 zapfino
    lang: urlParams.get('lang') || 'en',
    bg: '000000',
    accent: 'FFFFFF',
    showLockscreen: true,
  };

  // DOM 元素
  const styleBtns = document.querySelectorAll('.style-selector .segment-btn');
  const modelSelect = document.getElementById('modelSelect');
  const modelDetectBadge = document.getElementById('modelDetectBadge');
  const fontSelect = document.getElementById('fontSelect');
  const generatedUrlInput = document.getElementById('generatedUrl');
  const tutorialUrlText = document.getElementById('tutorialUrlText');
  const copyUrlBtn = document.getElementById('copyUrlBtn');
  const copyTutorialUrlBtn = document.getElementById('copyTutorialUrlBtn');
  const downloadBtn = document.getElementById('downloadBtn');
  const wallpaperImg = document.getElementById('wallpaperImg');
  const toggleLockscreenBtn = document.getElementById('toggleLockscreenBtn');
  const previewStatusText = document.getElementById('previewStatusText');
  const lockOverlay = document.getElementById('lockOverlay');
  const styleNameHeader = document.getElementById('styleNameHeader');
  const previewSpecs = document.getElementById('previewSpecs');
  const mockupAppleDate = document.getElementById('mockupAppleDate');

  // 若 URL 指定了隐藏字体 zapfino，在控制面板中追加隐藏选项或同步状态
  if (state.font === 'zapfino' && fontSelect) {
    let exists = false;
    for (let opt of fontSelect.options) {
      if (opt.value.toLowerCase() === 'zapfino') { exists = true; break; }
    }
    if (!exists) {
      const opt = document.createElement('option');
      opt.value = 'zapfino';
      opt.textContent = 'Zapfino (隐藏个性化模式)';
      opt.selected = true;
      fontSelect.insertBefore(opt, fontSelect.firstChild);
    }
  }

  // 1. 自动检测 iPhone 设备型号
  function detectDeviceModel() {
    const dpr = window.devicePixelRatio || 1;
    const w = Math.round(Math.min(window.screen.width, window.screen.height) * dpr);
    const h = Math.round(Math.max(window.screen.width, window.screen.height) * dpr);
    const key = `${w}x${h}`;

    const resolutionMap = {
      '1320x2868': 'iphone18promax', // 亦匹配 17/18 Pro Max
      '1260x2740': 'iphone18air',    // 匹配 iPhone 17/18 Air
      '1206x2622': 'iphone16pro',    // 亦匹配 17 Pro / 18 Pro
      '1179x2556': 'iphone16',       // 亦匹配 15/15Pro/14Pro
      '1290x2796': 'iphone16plus',   // 亦匹配 15ProMax/15Plus/14ProMax
      '1170x2532': 'iphone14',       // 亦匹配 12/13/14
      '1080x2340': 'iphone13mini',   // 匹配 12mini/13mini
      '1125x2436': 'iphonexs',
      '828x1792': 'iphone11',
      '750x1334': 'iphonese'
    };

    const matched = resolutionMap[key];
    if (matched && modelSelect) {
      modelSelect.value = matched;
      state.model = matched;
      if (modelDetectBadge) {
        modelDetectBadge.style.display = 'inline-block';
        modelDetectBadge.textContent = `✨ 已自动匹配您的 iPhone 分辨率 (${w}×${h})`;
      }
    } else {
      if (modelDetectBadge) {
        modelDetectBadge.style.display = 'inline-block';
        modelDetectBadge.style.background = 'rgba(255, 255, 255, 0.08)';
        modelDetectBadge.style.color = '#94A3B8';
        modelDetectBadge.textContent = '💡 电脑访问：请在下方自选 iPhone 机型';
      }
      if (modelSelect && !urlParams.get('model')) {
        state.model = modelSelect.value || 'iphone16pro';
      }
    }
  }

  // 2. 初始化今天锁屏日期文字
  function updateAppleDate() {
    const now = new Date();
    const month = now.getMonth() + 1;
    const date = now.getDate();
    const daysZh = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    if (mockupAppleDate) {
      mockupAppleDate.textContent = `${month}月${date}日 ${daysZh[now.getDay()]}`;
    }
  }

  // 3. 生成用于快捷指令的自动化 API URL (调用 /download 端点，直接返回 PNG 图片流)
  function buildAutomationUrl() {
    let path = window.location.pathname;
    if (!path.endsWith('/')) {
      path = path.substring(0, path.lastIndexOf('/') + 1);
    }
    const base = `${window.location.origin}${path}download`;
    const params = new URLSearchParams({
      style: state.style,
      model: state.model,
      font: state.font
    });
    return `${base}?${params.toString()}`;
  }

  // 4. 生成用于网页实时预览的 URL (调用 /generate 实时生成纯静态今日壁纸)
  function buildPreviewUrl() {
    let path = window.location.pathname;
    if (!path.endsWith('/')) {
      path = path.substring(0, path.lastIndexOf('/') + 1);
    }
    const base = `${window.location.origin}${path}generate`;
    const params = new URLSearchParams({
      style: state.style,
      model: state.model,
      font: state.font,
      lang: state.lang,
      bg: state.bg,
      accent: state.accent
    });
    return `${base}?${params.toString()}`;
  }

  // 5. 更新界面展示与纯静态高清实机壁纸 (所见即所得今日定格)
  let previewTimeout = null;
  function refreshUI(immediate = false) {
    const autoUrl = buildAutomationUrl();
    const previewUrl = buildPreviewUrl();

    if (generatedUrlInput) generatedUrlInput.value = autoUrl;
    if (tutorialUrlText) tutorialUrlText.textContent = autoUrl;
    if (downloadBtn) downloadBtn.href = autoUrl;

    // 更新标题与机型说明
    const selectedOption = modelSelect ? modelSelect.options[modelSelect.selectedIndex] : null;
    const modelText = selectedOption ? selectedOption.text : state.model;
    if (previewSpecs) previewSpecs.textContent = modelText;
    
    if (styleNameHeader) {
      if (state.style === 'pillars') {
        styleNameHeader.textContent = '时间立柱液位计 (Style 1)';
      } else {
        styleNameHeader.textContent = '瑞士腕表年历盘 (Style 3)';
      }
    }

    if (previewStatusText) {
      previewStatusText.textContent = '✨ 锁屏实机定格：展示当前机型今日即时渲染状态（所见即所得）';
    }

    // 立即或防抖加载今日实机渲染高清图
    if (wallpaperImg) {
      if (immediate) {
        if (previewTimeout) clearTimeout(previewTimeout);
        wallpaperImg.style.opacity = '0.7';
        wallpaperImg.src = previewUrl;
        wallpaperImg.onload = () => { wallpaperImg.style.opacity = '1'; };
        wallpaperImg.onerror = () => { wallpaperImg.style.opacity = '1'; };
      } else {
        wallpaperImg.style.opacity = '0.7';
        if (previewTimeout) clearTimeout(previewTimeout);
        previewTimeout = setTimeout(() => {
          wallpaperImg.src = previewUrl;
          wallpaperImg.onload = () => { wallpaperImg.style.opacity = '1'; };
          wallpaperImg.onerror = () => { wallpaperImg.style.opacity = '1'; };
        }, 120);
      }
    }
  }

  // 6. 核心样式切换 (Style 1 vs Style 3) - 点击立即切换预览
  styleBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      styleBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      state.style = btn.dataset.style;
      refreshUI(true); // 立即响应无延迟
    });
  });

  // 7. 机型选择监听
  if (modelSelect) {
    modelSelect.addEventListener('change', () => {
      state.model = modelSelect.value;
      refreshUI();
    });
  }

  // 8. 字体选择监听
  if (fontSelect) {
    fontSelect.addEventListener('change', () => {
      state.font = fontSelect.value;
      refreshUI();
    });
  }

  // 9. 统一的复制到剪贴板功能
  async function copyToClipboard(text, btnElement) {
    try {
      await navigator.clipboard.writeText(text);
      if (btnElement) {
        const orig = btnElement.textContent;
        btnElement.textContent = '✅ 已复制！请去快捷指令粘贴';
        btnElement.style.background = '#10B981';
        btnElement.style.color = '#FFFFFF';
        setTimeout(() => {
          btnElement.textContent = orig;
          btnElement.style.background = '';
          btnElement.style.color = '';
        }, 2500);
      }
    } catch (err) {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      alert('已成功复制链接到剪贴板！');
    }
  }

  if (copyUrlBtn) {
    copyUrlBtn.addEventListener('click', () => {
      copyToClipboard(buildAutomationUrl(), copyUrlBtn);
    });
  }

  if (copyTutorialUrlBtn) {
    copyTutorialUrlBtn.addEventListener('click', () => {
      copyToClipboard(buildAutomationUrl(), copyTutorialUrlBtn);
    });
  }

  // 10. 锁屏时钟仿真开关
  if (toggleLockscreenBtn && lockOverlay) {
    toggleLockscreenBtn.addEventListener('click', () => {
      state.showLockscreen = !state.showLockscreen;
      if (state.showLockscreen) {
        lockOverlay.classList.remove('hidden');
        toggleLockscreenBtn.classList.add('active');
        toggleLockscreenBtn.textContent = '锁屏时钟: 开';
      } else {
        lockOverlay.classList.add('hidden');
        toggleLockscreenBtn.classList.remove('active');
        toggleLockscreenBtn.textContent = '锁屏时钟: 关';
      }
    });
  }

  // 初始化执行
  detectDeviceModel();
  updateAppleDate();
  refreshUI();
});
