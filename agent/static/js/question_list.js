document.addEventListener('DOMContentLoaded', function () {
    const modal = new bootstrap.Modal(document.getElementById('infoModal'));
    modal.show();
  });

const btn = document.getElementById('analysisBtn');
const tooltip = document.getElementById('tooltip');

btn.addEventListener('mouseenter', () => {
    // 取得按鈕在視窗中的位置
    const rect = btn.getBoundingClientRect();

    // 計算水平置中位置
    const left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2;
    // 計算垂直位置（按鈕底部 + 8px 間距）
    const top = rect.bottom + window.scrollY + 8; // 加上 scrollY 防止滾動錯位

    // 設定 tooltip 位置
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
    tooltip.style.display = 'block';
});

btn.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
});   