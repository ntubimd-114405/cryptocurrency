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
        console.log("123");
    });

    // 顯示選中的內容區塊
    var selectedContent = document.getElementById(id);
    selectedContent.classList.add('active');
}

const cards = document.querySelectorAll('.card_invent');
const prevBtn = document.querySelector('.prev-btn');
const nextBtn = document.querySelector('.next-btn');
let currentIndex = 0;

    function updateActiveCard() {
        cards.forEach((card, index) => {
            card.classList.remove('active', 'prev', 'next', 'flip');
            
            if (index === currentIndex) {
                card.classList.add('active');
            } else if (index === (currentIndex - 1 + cards.length) % cards.length) {
                card.classList.add('prev');
            } else if (index === (currentIndex + 1) % cards.length) {
                card.classList.add('next');
            }
        });
    }

    prevBtn.addEventListener('click', () => {
        currentIndex = (currentIndex - 1 + cards.length) % cards.length;
        updateActiveCard();
    });

    nextBtn.addEventListener('click', () => {
        currentIndex = (currentIndex + 1) % cards.length;
        updateActiveCard();
    });

    cards.forEach(card => {
        card.addEventListener('click', () => {
            if (card.classList.contains('active'))
                card.classList.toggle('flip');
        });
    });

updateActiveCard();