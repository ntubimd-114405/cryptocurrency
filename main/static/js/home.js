window.onload = function() {
    fetch('https://api.coingecko.com/api/v3/global')
        .then(response => response.json())
        .then(data => {
            const marketData = data.data;

            // 更新總市值和24小時交易量
            document.getElementById('total_market_cap').textContent = marketData.total_market_cap.usd.toLocaleString();
            document.getElementById('total_24h_volume').textContent = marketData.total_volume.usd.toLocaleString();

            // 取得比特幣、以太坊和其他幣種的市占率
            const btcDominance = marketData.market_cap_percentage.btc.toFixed(2);
            const ethDominance = marketData.market_cap_percentage.eth.toFixed(2);
            const otherDominance = (100 - btcDominance - ethDominance).toFixed(2);

            // 更新市占率顯示
            document.getElementById('btc_dominance').textContent = `比特幣: ${btcDominance}%`;
            document.getElementById('eth_dominance').textContent = `以太坊: ${ethDominance}%`;
            document.getElementById('other_dominance').textContent = `其他: ${otherDominance}%`;
        })
        .catch(error => {
            console.error('無法取得市場數據:', error);
            document.getElementById('total_market_cap').textContent = '無法取得';
            document.getElementById('total_24h_volume').textContent = '無法取得';
            document.getElementById('btc_dominance').textContent = '無法取得';
            document.getElementById('eth_dominance').textContent = '無法取得';
            document.getElementById('other_dominance').textContent = '無法取得';
        });
}

const backToTopButton = document.getElementById("backToTop");

// 監聽滾動事件
window.onscroll = function() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop;
    if (scrollTop > 100) { 
        backToTopButton.style.display = "block"; // 滾動超過 100px 顯示按鈕
    } else {
        backToTopButton.style.display = "none"; // 否則隱藏按鈕
    }
};

// 點擊按鈕回到頂部
backToTopButton.onclick = function() {
    window.scrollTo({
        top: 0,
        behavior: "smooth" // 平滑滾動效果
    });
};

function showContent(id) {
    // 隱藏所有內容區塊
    var contents = document.querySelectorAll('.card-coin');
    contents.forEach(function(content) {
        content.classList.remove('active');
        
    });

    // 顯示選中的內容區塊
    var selectedContent = document.getElementById(id);
    selectedContent.classList.add('active');
}

document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll(".card_invent");

    cards.forEach(card => {
        card.addEventListener("click", function () {
            // 先把所有已經翻轉的卡片恢復
            cards.forEach(c => {
                if (c !== card) {
                    c.classList.remove("active");
                }
            });

            // 切換當前卡片的翻轉狀態
            card.classList.toggle("active");
        });
    });
});

// 監視 `.carousel` 是否進入視口
const carousel = document.querySelector('.carousel');
const ball = document.getElementById('ball');
const path = document.getElementById('motionPath');
let isInView = false;

// 當 `.carousel` 進入視口時啟動滾動事件
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            isInView = true;  // `.carousel` 進入視口，開始處理滾動
            // 計算初始位置，避免瞬移
            updateBallPosition();
        } else {
            isInView = false; // `.carousel` 離開視口，停止滾動
        }
    });
}, { threshold: 0.5 });  // 設定當元素至少一半進入視口時觸發

observer.observe(carousel);

// 計算球的位置，並設置初始位置
const updateBallPosition = () => {
    const scrollY = window.scrollY;
    const pathLength = path.getTotalLength();
    let scrollPercent = scrollY / (document.body.scrollHeight - window.innerHeight);
    scrollPercent = Math.min(Math.max(scrollPercent, 0), 1);

    const point = path.getPointAtLength(scrollPercent * pathLength);
    ball.setAttribute('cx', point.x);
    ball.setAttribute('cy', point.y);
};

// 滾動事件處理
window.addEventListener('scroll', function() {
    if (!isInView) return;  // 如果 `.carousel` 沒有進入視口，則不執行下面的代碼

    // 更新球的位置
    updateBallPosition();
});

function animateBall(pathId, ballId, speed, callback) {
    const path = document.getElementById(pathId);
    const ball = document.getElementById(ballId);
    const pathLength = path.getTotalLength();

    let progress = 0;

    function moveBall() {
        progress += speed;
        if (progress > 1) {
            progress = 1;
        }

        const point = path.getPointAtLength(progress * pathLength);
        ball.setAttribute('cx', point.x);
        ball.setAttribute('cy', point.y);

        if (progress < 1) {
            requestAnimationFrame(moveBall);
        } else if (callback) {
            callback(); // 動畫結束後執行 callback
        }
    }

    moveBall();
}

function animateImage() {
    const image = document.querySelector(".moving-image");
    let positionY = 100; // 圖片初始 y 位置，從水管底部（畫面外）開始
    const targetPositionY = -50; // 圖片最終 y 位置，水管的頂端
    const speed = 2; // 移動速度

    function moveImage() {
        positionY -= speed; // 圖片向上移動，減少 y 值
        image.setAttribute("y", positionY); // 設置圖片的 y 位置
        

        // 如果圖片還未到達頂端，繼續動畫
        if (positionY > targetPositionY) {
            requestAnimationFrame(moveImage);
        } else {
           
            setTimeout(startAnimationSequence, 1000); // 停留 1 秒後重新開始
        }
    }

    moveImage(); // 開始移動
}



function startAnimationSequence() {
    animateBall("leftPath", "ballLeft", 0.005, () => {
        animateBall("rightPath", "ballRight", 0.005, () => {
            animateImage(); // 圖片動畫
        });
    });
}

startAnimationSequence();

document.addEventListener("DOMContentLoaded", function () {
    const target = document.querySelector('.carousel1');
    const line = document.getElementById('line');
  
    const flatPoints = "40,180 80,180 120,180 160,180 200,180 240,180 280,180 320,180";
    const risePoints = "40,180 80,140 120,160 160,120 200,100 240,130 280,90 320,110";
  
    let animationFrame;
  
    function animateLine(fromPoints, toPoints, duration = 600) {
      const start = fromPoints.split(" ").map(p => p.split(",").map(Number));
      const end = toPoints.split(" ").map(p => p.split(",").map(Number));
      const startTime = performance.now();
  
      cancelAnimationFrame(animationFrame);
  
      function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
  
        const currentPoints = start.map((pt, i) => {
          const [x0, y0] = pt;
          const [x1, y1] = end[i];
          const y = y0 + (y1 - y0) * progress;
          return `${x0},${y.toFixed(1)}`;
        }).join(" ");
  
        line.setAttribute("points", currentPoints);
  
        if (progress < 1) {
          animationFrame = requestAnimationFrame(animate);
        }
      }
  
      animationFrame = requestAnimationFrame(animate);
    }
  
    // 使用 IntersectionObserver 偵測是否進入畫面
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateLine(flatPoints, risePoints); // 進入畫面：上升
        } else {
          animateLine(risePoints, flatPoints); // 離開畫面：下降
        }
      });
    }, {
      threshold: 0.9 // 當有一半進入畫面就觸發
    });
  
    observer.observe(target);
  
    // 初始狀態為平線
    line.setAttribute("points", flatPoints);
  });