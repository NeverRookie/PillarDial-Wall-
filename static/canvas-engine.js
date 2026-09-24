/**
 * LifeGrid 纯前端 Canvas 矢量渲染引擎
 * 100% 运行于用户 iPhone 本地 GPU，调用 iOS 原生 Zapfino 字体
 * 零服务器版权隐患 · 极速离线出图
 */

(function(window) {
  'use strict';

  // 辅助函数：将角度转为弧度
  const toRad = deg => (deg * Math.PI) / 180.0;

  // 辅助函数：计算公历闰年与某天
  function getDateInfo(targetDate = new Date()) {
    const year = targetDate.getFullYear();
    const month = targetDate.getMonth() + 1; // 1-12
    const day = targetDate.getDate();

    const isLeap = (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
    const daysInMonth = [31, isLeap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    const totalDays = isLeap ? 366 : 365;

    // 当年第几天
    let dayOfYear = 0;
    for (let i = 0; i < month - 1; i++) {
      dayOfYear += daysInMonth[i];
    }
    dayOfYear += day;

    const daysLeft = totalDays - dayOfYear;
    const yearProgressPct = Math.round((dayOfYear / totalDays) * 100);

    return {
      year,
      month,
      day,
      daysInMonth: daysInMonth[month - 1],
      totalDays,
      dayOfYear,
      daysLeft,
      yearProgressPct
    };
  }

  /**
   * 绘制弯曲圆角胶囊 (Curved Capsule)
   */
  function drawCurvedCapsule(ctx, cx, cy, rMid, startDeg, endDeg, capR, fillStyle, strokeStyle, strokeWidth) {
    const startRad = toRad(startDeg);
    const endRad = toRad(endDeg);

    // 胶囊两端圆心
    const c1x = cx + rMid * Math.cos(startRad);
    const c1y = cy + rMid * Math.sin(startRad);
    const c2x = cx + rMid * Math.cos(endRad);
    const c2y = cy + rMid * Math.sin(endRad);

    ctx.save();
    ctx.beginPath();
    // 外圆弧
    ctx.arc(cx, cy, rMid + capR, startRad, endRad, false);
    // 终止端半圆
    ctx.arc(c2x, c2y, capR, endRad, endRad + Math.PI, false);
    // 内圆弧
    ctx.arc(cx, cy, rMid - capR, endRad, startRad, true);
    // 起始端半圆
    ctx.arc(c1x, c1y, capR, startRad + Math.PI, startRad, false);
    ctx.closePath();

    if (fillStyle) {
      ctx.fillStyle = fillStyle;
      ctx.fill();
    }
    if (strokeStyle && strokeWidth > 0) {
      ctx.strokeStyle = strokeStyle;
      ctx.lineWidth = strokeWidth;
      ctx.stroke();
    }
    ctx.restore();
  }

  /**
   * 跨平台兼容圆角矩形绘制
   */
  function drawRoundRect(ctx, x, y, w, h, r) {
    if (typeof r === 'number') r = [r, r, r, r];
    if (ctx.roundRect) {
      ctx.roundRect(x, y, w, h, r);
    } else {
      const tl = r[0] || 0, tr = r[1] || r[0] || 0, br = r[2] || r[0] || 0, bl = r[3] || r[0] || 0;
      ctx.moveTo(x + tl, y);
      ctx.lineTo(x + w - tr, y);
      ctx.quadraticCurveTo(x + w, y, x + w, y + tr);
      ctx.lineTo(x + w, y + h - br);
      ctx.quadraticCurveTo(x + w, y + h, x + w - br, y + h);
      ctx.lineTo(x + bl, y + h);
      ctx.quadraticCurveTo(x, y + h, x, y + h - bl);
      ctx.lineTo(x, y + tl);
      ctx.quadraticCurveTo(x, y, x + tl, y);
    }
  }

  /**
   * 样式 3: 瑞士腕表年历盘 (Grand Chronometer Dial)
   */
  function renderDial(ctx, width, height, fontName = 'Great Vibes', targetDate = new Date()) {
    const dateInfo = getDateInfo(targetDate);
    const scaleW = width / 1179.0;
    const scaleH = height / 2556.0;

    const fnLower = (fontName || '').toLowerCase();
    const isZapfino = fnLower.includes('zapfino');
    const isGreatVibes = fnLower.includes('great vibes') || fnLower.includes('greatvibes');
    const isPinyon = fnLower.includes('pinyon');
    const isCalligraphy = isZapfino || isGreatVibes || isPinyon;

    // 1. 纯黑 OLED 背景
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, width, height);

    const cx = width / 2.0;
    const cy = height * 0.495; // 黄金比例居中

    const rSecIn = width * 0.282;
    const rSecOut = width * 0.392;
    const capR = width * 0.0148;
    const rArcMid = width * 0.428;

    const capAngularExtent = (capR / rArcMid) * (180.0 / Math.PI); // 约 1.98度
    const desiredTipGap = 2.4;
    const deltaArc = capAngularExtent + desiredTipGap / 2.0; // 约 3.18度
    const secGap = 2.2;

    // 2. 绘制未来月份暗灰轮廓 (Outer Track)
    for (let m = dateInfo.month; m <= 12; m++) {
      const degStart = 270.0 + (m - 1) * 30.0;
      const degEnd = 270.0 + m * 30.0;
      const aStart = degStart + deltaArc;
      const aEnd = degEnd - deltaArc;
      const outlineColor = (m === dateInfo.month) ? 'rgba(50, 55, 65, 0.8)' : 'rgba(36, 40, 48, 0.7)';
      drawCurvedCapsule(ctx, cx, cy, rArcMid, aStart, aEnd, capR, null, outlineColor, Math.max(2, 2 * scaleW));
    }

    // 3. 绘制内圈 12 扇区轮廓与月份数字
    for (let m = 1; m <= 12; m++) {
      const degStart = 270.0 + (m - 1) * 30.0;
      const degEnd = 270.0 + m * 30.0;
      const degMid = (degStart + degEnd) / 2.0;

      const bStart = degStart + secGap / 2.0;
      const bEnd = degEnd - secGap / 2.0;

      // 绘制扇区边框
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, rSecOut, toRad(bStart), toRad(bEnd), false);
      ctx.arc(cx, cy, rSecIn, toRad(bEnd), toRad(bStart), true);
      ctx.closePath();
      ctx.strokeStyle = (m === dateInfo.month) ? 'rgba(95, 105, 120, 0.9)' : 'rgba(42, 46, 54, 0.8)';
      ctx.lineWidth = Math.max(1.5, 1.8 * scaleW);
      ctx.stroke();
      ctx.restore();

      // 绘制月份数字 1-12
      const rNum = (rSecIn + rSecOut) / 2.0;
      const numX = cx + rNum * Math.cos(toRad(degMid));
      const numY = cy + rNum * Math.sin(toRad(degMid));

      ctx.save();
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      const fnLower = (fontName || '').toLowerCase();
      let numFontSize;
      if (fnLower.includes('great vibes') || fnLower.includes('greatvibes')) {
        numFontSize = Math.round((m === dateInfo.month ? 76 : 68) * scaleW);
      } else if (fnLower.includes('pinyon')) {
        numFontSize = Math.round((m === dateInfo.month ? 68 : 60) * scaleW);
      } else {
        numFontSize = Math.round((m === dateInfo.month ? 44 : 38) * scaleW);
      }
      ctx.font = `${numFontSize}px "${fontName}", -apple-system, sans-serif`;

      if (m === dateInfo.month) {
        ctx.fillStyle = '#FFFFFF';
        ctx.shadowColor = 'rgba(255, 255, 255, 0.6)';
        ctx.shadowBlur = 10 * scaleW;
      } else if (m < dateInfo.month) {
        ctx.fillStyle = '#8E95A5';
      } else {
        ctx.fillStyle = '#383D48';
      }
      ctx.fillText(m.toString(), numX, numY + (isCalligraphy ? 2 * scaleH : 0));
      ctx.restore();
    }

    // 4. 绘制已过去月份的实体充盈 (Past Months)
    for (let m = 1; m < dateInfo.month; m++) {
      const degStart = 270.0 + (m - 1) * 30.0;
      const degEnd = 270.0 + m * 30.0;
      const aStart = degStart + deltaArc;
      const aEnd = degEnd - deltaArc;

      ctx.save();
      ctx.shadowColor = 'rgba(255, 255, 255, 0.35)';
      ctx.shadowBlur = 12 * scaleW;
      drawCurvedCapsule(ctx, cx, cy, rArcMid, aStart, aEnd, capR, '#FFFFFF', null, 0);
      ctx.restore();
    }

    // 5. 绘制当前月份动态充盈与物理级高光晕 (Current Month Active Fill)
    const mCur = dateInfo.month;
    const curFrac = Math.max(0.02, Math.min(1.0, dateInfo.day / dateInfo.daysInMonth));
    const degStartCur = 270.0 + (mCur - 1) * 30.0;
    const degEndCur = 270.0 + mCur * 30.0;
    const aStartCur = degStartCur + deltaArc;
    const fullSpan = (degEndCur - deltaArc) - aStartCur;
    const aEndCur = aStartCur + fullSpan * curFrac;

    if (aEndCur > aStartCur) {
      // 多层漫反射自发光 (Glow Bloom)
      ctx.save();
      ctx.shadowColor = 'rgba(255, 255, 255, 0.9)';
      ctx.shadowBlur = 24 * scaleW;
      drawCurvedCapsule(ctx, cx, cy, rArcMid, aStartCur, aEndCur, capR, '#FFFFFF', null, 0);
      ctx.restore();

      // 叠加纯白主体
      drawCurvedCapsule(ctx, cx, cy, rArcMid, aStartCur, aEndCur, capR, '#FFFFFF', null, 0);
    }

    // 6. 绘制 12 放射状刻度线
    for (let m = 0; m < 12; m++) {
      const deg = 270.0 + m * 30.0;
      const rad = toRad(deg);
      const isCard = (m % 3 === 0);
      const tickIn = rSecOut + (isCard ? 10 * scaleW : 14 * scaleW);
      const tickOut = rArcMid - capR - (isCard ? 10 * scaleW : 14 * scaleW);

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(cx + tickIn * Math.cos(rad), cy + tickIn * Math.sin(rad));
      ctx.lineTo(cx + tickOut * Math.cos(rad), cy + tickOut * Math.sin(rad));
      ctx.strokeStyle = isCard ? 'rgba(120, 130, 150, 0.75)' : 'rgba(55, 62, 75, 0.6)';
      ctx.lineWidth = Math.max(1.5, (isCard ? 2.5 : 1.5) * scaleW);
      ctx.stroke();
      ctx.restore();
    }

    // 7. 绘制中央大字倒计时 (Central Count: e.g. "100")
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    let countFontSize;
    let subFontSize;
    let offsetY;
    let subOffsetY;

    if (isGreatVibes) {
      countFontSize = Math.round(420 * scaleW);
      subFontSize = Math.round(68 * scaleW);
      offsetY = cy - 36 * scaleH;
      subOffsetY = cy + Math.round(84 * scaleH);
    } else if (isPinyon) {
      countFontSize = Math.round(360 * scaleW);
      subFontSize = Math.round(64 * scaleW);
      offsetY = cy - 28 * scaleH;
      subOffsetY = cy + Math.round(80 * scaleH);
    } else if (isZapfino) {
      countFontSize = Math.round(210 * scaleW);
      subFontSize = Math.round(36 * scaleW);
      offsetY = cy - 20 * scaleH;
      subOffsetY = cy + Math.round(76 * scaleH);
    } else {
      countFontSize = Math.round(200 * scaleW);
      subFontSize = Math.round(32 * scaleW);
      offsetY = cy - 14 * scaleH;
      subOffsetY = cy + Math.round(76 * scaleH);
    }

    ctx.font = `${countFontSize}px "${fontName}", -apple-system, sans-serif`;
    ctx.fillStyle = '#FFFFFF';

    // 优雅光晕
    ctx.shadowColor = 'rgba(255, 255, 255, 0.45)';
    ctx.shadowBlur = 18 * scaleW;
    ctx.fillText(dateInfo.daysLeft.toString(), cx, offsetY);
    ctx.restore();

    // 8. 绘制中央副标题 (Days Left in 2026)
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = `${subFontSize}px "${fontName}", -apple-system, sans-serif`;
    ctx.fillStyle = 'rgba(235, 240, 255, 0.9)';

    if (!isCalligraphy) {
      ctx.letterSpacing = '2px';
    }
    const subText = isCalligraphy ? `Days Left in ${dateInfo.year}` : `DAYS LEFT IN ${dateInfo.year}`;
    ctx.fillText(subText, cx, subOffsetY);
    ctx.restore();
  }

  /**
   * 样式 1: 时间立柱液位计 (Monolithic Pillars)
   */
  function renderPillars(ctx, width, height, fontName = 'Great Vibes', targetDate = new Date()) {
    const dateInfo = getDateInfo(targetDate);
    const scaleW = width / 1179.0;
    const scaleH = height / 2556.0;

    const fnLowerPillars = (fontName || '').toLowerCase();
    const isZapfino = fnLowerPillars.includes('zapfino');
    const isGreatVibes = fnLowerPillars.includes('great vibes') || fnLowerPillars.includes('greatvibes');
    const isPinyon = fnLowerPillars.includes('pinyon');
    const isCalligraphy = isZapfino || isGreatVibes || isPinyon;

    // 1. 纯黑 OLED 背景
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, width, height);

    const pillarW = Math.round(width * 0.046);
    const pillarH = Math.round(height * 0.32);
    const totalPillars = 12;
    const gap = Math.round(width * 0.024);

    const totalSpan = totalPillars * pillarW + (totalPillars - 1) * gap;
    const startX = Math.round((width - totalSpan) / 2.0);
    const startY = Math.round(height * 0.36);
    const endY = startY + pillarH;
    const radius = pillarW / 2.0;

    // 绘制 12 根立柱
    for (let m = 1; m <= 12; m++) {
      const px = startX + (m - 1) * (pillarW + gap);

      // A. 底层暗灰色轮廓槽
      ctx.save();
      ctx.beginPath();
      drawRoundRect(ctx, px, startY, pillarW, pillarH, radius);
      ctx.strokeStyle = (m === dateInfo.month) ? 'rgba(70, 78, 92, 0.9)' : 'rgba(38, 42, 50, 0.8)';
      ctx.lineWidth = Math.max(2, 2 * scaleW);
      ctx.stroke();
      ctx.restore();

      // B. 液位充盈
      if (m < dateInfo.month) {
        // 已过去月份 100% 充盈
        ctx.save();
        ctx.beginPath();
        drawRoundRect(ctx, px, startY, pillarW, pillarH, radius);
        ctx.fillStyle = '#FFFFFF';
        ctx.shadowColor = 'rgba(255, 255, 255, 0.35)';
        ctx.shadowBlur = 10 * scaleW;
        ctx.fill();
        ctx.restore();
      } else if (m === dateInfo.month) {
        // 当前月份动态液位填充 (从底部往上升)
        const frac = Math.max(0.03, Math.min(1.0, dateInfo.day / dateInfo.daysInMonth));
        const fillH = Math.round(pillarH * frac);
        const fillY = endY - fillH;

        ctx.save();
        // 限制在圆角立柱轮廓内裁剪
        ctx.beginPath();
        drawRoundRect(ctx, px, startY, pillarW, pillarH, radius);
        ctx.clip();

        // 填充液位
        ctx.beginPath();
        drawRoundRect(ctx, px, fillY, pillarW, fillH, [radius, radius, radius, radius]);
        ctx.fillStyle = '#FFFFFF';
        ctx.shadowColor = 'rgba(255, 255, 255, 0.85)';
        ctx.shadowBlur = 20 * scaleW;
        ctx.fill();
        ctx.restore();
      }
    }

    // 底端文字
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    let fSize;
    if (fnLowerPillars.includes('great vibes') || fnLowerPillars.includes('greatvibes')) {
      fSize = Math.round(96 * scaleW);
    } else if (fnLowerPillars.includes('pinyon')) {
      fSize = Math.round(84 * scaleW);
    } else if (fnLowerPillars.includes('zapfino')) {
      fSize = Math.round(48 * scaleW);
    } else {
      fSize = Math.round(44 * scaleW);
    }

    ctx.font = `${fSize}px "${fontName}", -apple-system, sans-serif`;
    ctx.fillStyle = 'rgba(245, 245, 248, 0.95)';

    const textY = endY + Math.round(height * 0.052);
    const textStr = isCalligraphy
      ? `${dateInfo.daysLeft} Days Left · ${dateInfo.yearProgressPct}%`
      : `${dateInfo.daysLeft} DAYS LEFT · ${dateInfo.yearProgressPct}%`;

    ctx.fillText(textStr, width / 2.0, textY);
    ctx.restore();
  }

  // 导出到全局
  window.LifeGridEngine = {
    renderDial,
    renderPillars,
    getDateInfo
  };

})(window);
