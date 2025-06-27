// frontend/script.js (phiên bản cuối cùng, đã sửa cấu trúc)
document.addEventListener('DOMContentLoaded', () => {
    console.log('[DEBUG] DOM Content Loaded. Script is running.');

    // --- DOM Element Selectors ---
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    const loader = document.getElementById('loader');

    // **NEU**: Mobile Menu Elements
    const menuToggleBtn = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');

    // Dashboard Elements
    const refreshDashboardBtn = document.getElementById('refresh-dashboard-btn');
    const aiPredictionsListEl = document.getElementById('ai-predictions-list');
    const hotStatsListEl = document.getElementById('hot-stats-list');
    const coldStatsListEl = document.getElementById('cold-stats-list');
    const resultBoardContainer = document.getElementById('result-board-container');
    const latestResultDateEl = document.getElementById('latest-result-date');

    // Analysis Elements
    const numberInput = document.getElementById('number-input');
    const inspectNumberBtn = document.getElementById('inspect-number-btn');
    const numberDetailsEl = document.getElementById('number-details');
    const analysisChartCanvas = document.getElementById('analysis-chart');
    let analysisChart = null;

    // Backtest Elements
    const backtestDateSelect = document.getElementById('backtest-date-select');
    const backtestBtn = document.getElementById('backtest-btn');
    const backtestResultsEl = document.getElementById('backtest-results');

    // History Elements
    const historyLimitInput = document.getElementById('history-limit-input');
    const showHistoryBtn = document.getElementById('show-history-btn');
    const historyTableEl = document.getElementById('history-table');
    
    // Chart Elements
    const generateChartBtn = document.getElementById('generate-chart-btn');
    const chartTypeSelect = document.getElementById('chart-type-select');
    const chartDaysInput = document.getElementById('chart-days-input');
    const barChartCanvas = document.getElementById('bar-chart');
    const heatmapChartCanvas = document.getElementById('heatmap-chart');
    const distributionChartCanvas = document.getElementById('distribution-chart');
    const barchartTitle = document.getElementById('barchart-title');
    const heatmapTitle = document.getElementById('heatmap-title');
    const distributionCard = document.getElementById('distribution-card');

    // Biến để lưu trữ các biểu đồ
    let barChartInstance = null;
    let heatmapInstance = null;
    let distributionInstance = null;

    // --- Logic Loader ---
    let activeRequests = 0;
    function showLoader() { if (activeRequests === 0) loader.classList.remove('hidden'); activeRequests++; }
    function hideLoader() { activeRequests--; if (activeRequests <= 0) { activeRequests = 0; loader.classList.add('hidden'); } }

    // --- API Helper ---
    const API_BASE_URL = window.location.origin;
    async function callApi(endpoint, params = {}) {
        const url = new URL(`${API_BASE_URL}${endpoint}`);
        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
        showLoader();
        try {
            const response = await fetch(url, { cache: "no-store" });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || 'Lỗi không xác định từ server');
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`API Error on ${endpoint}:`, error);
            alert(`Lỗi: ${error.message}`);
            return { error: `Lỗi khi gọi API ${endpoint}: ${error.message}` };
        } finally {
            hideLoader();
        }
    }

    // --- Navigation Logic ---
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('data-target');
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            contentSections.forEach(section => {
                section.classList.toggle('hidden', section.id !== targetId);
            });
            // **NEU**: Đóng sidebar khi click vào link trên mobile
            if (window.innerWidth <= 768) {
                closeMobileMenu();
            }
        });
    });

    // --- **NEU**: Mobile Menu Logic ---
    function openMobileMenu() {
        sidebar.classList.add('open');
        overlay.classList.remove('hidden');
    }

    function closeMobileMenu() {
        sidebar.classList.remove('open');
        overlay.classList.add('hidden');
    }

    menuToggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        sidebar.classList.contains('open') ? closeMobileMenu() : openMobileMenu();
    });
    overlay.addEventListener('click', closeMobileMenu);
    
    // --- Dashboard Logic ---
    async function updateDashboard() {
        if (!aiPredictionsListEl) return;
        const [predictions, hotCold, latestResult] = await Promise.all([
            callApi('/predict', { top_n: 10 }),
            callApi('/stats/hot-cold'),
            callApi('/history', { limit: 1 })
        ]);
        aiPredictionsListEl.innerHTML = '';
        if (predictions && !predictions.error && predictions.predictions) {
            const sortedPredictions = Object.entries(predictions.predictions).sort(([, a], [, b]) => parseFloat(b) - parseFloat(a));
            sortedPredictions.forEach(([number, probability]) => {
                const listItem = document.createElement('div'); listItem.className = 'list-item';
                listItem.innerHTML = `<div><span class="label">Số: </span><span class="number-ai">${number}</span></div><div><span class="label">Xác suất: </span><span class="probability">${probability}</span></div>`;
                aiPredictionsListEl.appendChild(listItem);
            });
        } else { aiPredictionsListEl.innerHTML = `<p>Không tải được dự đoán. Lỗi: ${predictions?.error ?? 'Không xác định'}</p>`; }
        hotStatsListEl.innerHTML = ''; coldStatsListEl.innerHTML = '';
        if (hotCold && !hotCold.error) {
            hotStatsListEl.innerHTML = `<div class="list-header">🔥 Số Nóng</div><div class="list-item"><span class="value">${(hotCold.hot ?? []).join(', ')}</span></div>`;
            coldStatsListEl.innerHTML = `<div class="list-header">❄️ Số Lạnh (Gan)</div><div class="list-item"><span class="value">${(hotCold.cold ?? []).join(', ')}</span></div>`;
        } else { hotStatsListEl.innerHTML = `<p>Không tải được thống kê. Lỗi: ${hotCold?.error ?? 'Không xác định'}</p>`; }
        if (latestResult && !latestResult.error && latestResult.length > 0) { renderResultBoard(latestResult[0]); } else {
            if(resultBoardContainer) resultBoardContainer.innerHTML = `<div class="card">Không tải được kết quả mới nhất.<br>Lỗi: ${latestResult?.error ?? 'Dữ liệu không có sẵn'}</div>`;
            if(latestResultDateEl) latestResultDateEl.textContent = 'N/A';
        }
    }
    
    // --- Result Board Rendering ---
    function renderResultBoard(resultData) {
        if (!resultData) return;
        const date = new Date(resultData.date);
        latestResultDateEl.textContent = date.toLocaleDateString('vi-VN');
        resultBoardContainer.innerHTML = '';
        const prizeLayout = [
            { name: 'G.ĐB', keys: ['special'], class: 'special-prize' },
            { name: 'G.1', keys: ['prize1'] },
            { name: 'G.2', keys: ['prize2_1', 'prize2_2'] },
            { name: 'G.3', keys: ['prize3_1', 'prize3_2', 'prize3_3', 'prize3_4', 'prize3_5', 'prize3_6'] },
            { name: 'G.4', keys: ['prize4_1', 'prize4_2', 'prize4_3', 'prize4_4'] },
            { name: 'G.5', keys: ['prize5_1', 'prize5_2', 'prize5_3', 'prize5_4', 'prize5_5', 'prize5_6'] },
            { name: 'G.6', keys: ['prize6_1', 'prize6_2', 'prize6_3'] },
            { name: 'G.7', keys: ['prize7_1', 'prize7_2', 'prize7_3', 'prize7_4'], class: 'prize-7' }
        ];
        prizeLayout.forEach(prize => {
            const rowDiv = document.createElement('div'); rowDiv.className = 'result-row';
            const nameDiv = document.createElement('div'); nameDiv.className = 'prize-name'; nameDiv.textContent = prize.name;
            const numbersDiv = document.createElement('div'); numbersDiv.className = 'prize-numbers';
            prize.keys.forEach(key => {
                const numberSpan = document.createElement('span');
                numberSpan.textContent = resultData[key] ?? 'N/A';
                if (prize.class) numberSpan.classList.add(prize.class);
                numbersDiv.appendChild(numberSpan);
            });
            rowDiv.appendChild(nameDiv); rowDiv.appendChild(numbersDiv); resultBoardContainer.appendChild(rowDiv);
        });
    }

    // --- Deep Analysis Logic ---
    async function inspectNumber() {
        const number = numberInput.value; if (!number || !/^\d+$/.test(number) || parseInt(number, 10) < 0 || parseInt(number, 10) > 99) { alert('Vui lòng nhập một số hợp lệ từ 00 đến 99.'); return; }
        const paddedNumber = number.padStart(2, '0');
        const data = await callApi(`/stats/number-details/${paddedNumber}`);
        if (!data || data.error) { numberDetailsEl.innerHTML = `<h3>Lỗi</h3><p>${data?.error ?? 'Không thể tải chi tiết.'}</p>`; if (analysisChart) analysisChart.destroy(); return; }
        const freq = data.frequency; 
        numberDetailsEl.innerHTML = `<h3>Phân tích chi tiết số: <strong>${data.number}</strong></h3>
        <ul>
            <li><strong>Tình trạng gan (chưa về):</strong> ${data.last_appearance_days_ago} ngày</li>
            <li><strong>Tần suất (30 ngày gần nhất):</strong> ${freq.last_30_days} lần</li>
            <li><strong>Tần suất (90 ngày gần nhất):</strong> ${freq.last_90_days} lần</li>
            <li><strong>Tổng số lần xuất hiện:</strong> ${freq.total} lần</li>
        </ul>`; 
        renderAnalysisChart(data);
    }
    
    function renderAnalysisChart(data) {
        if (analysisChart) { analysisChart.destroy(); }
        const historyDates = data?.appearance_history?.map(d => new Date(d)) ?? []; if (historyDates.length === 0) return;
        const dateLabels = [], appearanceData = []; const endDate = new Date(); const startDate = new Date(); startDate.setDate(endDate.getDate() - 365);
        for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) { dateLabels.push(d.toLocaleDateString('vi-VN')); const dateStr = d.toISOString().split('T')[0]; appearanceData.push(data.appearance_history.includes(dateStr) ? 1 : 0); }
        const ctx = analysisChartCanvas.getContext('2d'); analysisChart = new Chart(ctx, { type: 'bar', data: { labels: dateLabels, datasets: [{ label: `Sự xuất hiện của số ${data.number}`, data: appearanceData, backgroundColor: 'rgba(90, 142, 238, 0.6)', borderColor: 'rgba(90, 142, 238, 1)', borderWidth: 1 }] }, options: { scales: { y: { display: false, beginAtZero: true, ticks: { stepSize: 1 } }, x: { ticks: { maxRotation: 90, minRotation: 90, autoSkip: true, maxTicksLimit: 30 } } } } });
    }

    // --- Backtesting Logic ---
    async function populateBacktestDates() {
        if (!backtestDateSelect) return;
        const data = await callApi('/history', { limit: 365 }); 
        if (data && !data.error) { 
            backtestDateSelect.innerHTML = (data ?? []).map(item => `<option value="${item.date.split('T')[0]}">${new Date(item.date).toLocaleDateString('vi-VN')}</option>`).join(''); 
        } else { 
            backtestDateSelect.innerHTML = `<option>Lỗi tải dữ liệu</option>`; 
        }
    }
    
    async function runBacktest() {
        const date = backtestDateSelect.value; if (!date) return; 
        const data = await callApi('/predict/backtest', { date }); 
        if(data && !data.error){
            const { predictions, actual_results, hits } = data;
            const predictionsText = `- Dự đoán của AI: [${predictions.join(', ')}]`;
            const resultsText = `- Các số Lô đã về: [${actual_results.join(', ')}]`;
            const hitsText = `\n- AI đã đoán trúng: ${hits.length} số [${hits.join(', ')}]`;
            const accuracyText = `- Tỷ lệ chính xác: ${((hits.length / predictions.length) * 100).toFixed(2)}%`;

            backtestResultsEl.textContent = `Kết quả kiểm tra lại cho ngày ${new Date(date).toLocaleDateString('vi-VN')}:\n\n${predictionsText}\n${resultsText}\n${hitsText}\n${accuracyText}`;
        } else {
             backtestResultsEl.textContent = `Không thể lấy dữ liệu kiểm tra.\nLỗi: ${data?.error || 'Không xác định'}`;
        }
    }
    
    // --- History Logic ---
    async function showHistory() {
        const limit = historyLimitInput.value; 
        const data = await callApi('/history', { limit }); 
        if (data && !data.error) { 
            // Định dạng lại ngày tháng trước khi hiển thị
            const formattedData = data.map(item => ({...item, date: new Date(item.date).toLocaleDateString('vi-VN')}));
            renderGenericTable(historyTableEl, formattedData); 
        } else { 
            const tbody = historyTableEl.querySelector('tbody') || historyTableEl.createTBody(); 
            tbody.innerHTML = `<tr><td colspan="100%">Không tải được lịch sử. Lỗi: ${data?.error ?? 'Không xác định'}</td></tr>`; 
        }
    }
    
    function renderGenericTable(tableElement, data) {
        if (!data || data.length === 0) return; 
        let headers = Object.keys(data[0]);
        // Tùy chỉnh tên và thứ tự cột
        const displayHeaders = {
            date: 'Ngày', special: 'Đặc Biệt', prize1: 'Giải 1', prize2_1: 'Giải 2', prize3_1: 'Giải 3', prize4_1: 'Giải 4', prize5_1: 'Giải 5', prize6_1: 'Giải 6', prize7_1: 'Giải 7'
        };
        const orderedHeaders = ['date', 'special', 'prize1', 'prize2_1', 'prize3_1', 'prize4_1', 'prize5_1', 'prize6_1', 'prize7_1'];
        // Lấy các header khác không có trong danh sách trên
        const otherHeaders = headers.filter(h => !orderedHeaders.includes(h));

        headers = [...orderedHeaders, ...otherHeaders];

        const thead = tableElement.querySelector('thead') || tableElement.createTHead(); 
        const tbody = tableElement.querySelector('tbody') || tableElement.createTBody(); 
        thead.innerHTML = `<tr>${headers.map(h => `<th>${displayHeaders[h] || h}</th>`).join('')}</tr>`; 
        tbody.innerHTML = data.map(row => `<tr>${headers.map(h => `<td>${row[h] ?? ''}</td>`).join('')}</tr>`).join('');
    }

    // --- Charting Logic ---
    function renderBarChart(canvas, title, chartData) {
        if (barChartInstance) barChartInstance.destroy();
        barchartTitle.textContent = title;
        barChartInstance = new Chart(canvas, { type: 'bar', data: { labels: chartData.labels, datasets: [{ label: 'Số lần / Số ngày', data: chartData.data, backgroundColor: 'rgba(255, 107, 107, 0.7)', borderColor: 'rgba(255, 107, 107, 1)', borderWidth: 1 }] }, options: { indexAxis: 'y', scales: { x: { beginAtZero: true } }, plugins: { legend: { display: false } } } });
    }

    function renderHeatmap(canvas, title, chartData) {
        if (heatmapInstance) heatmapInstance.destroy();
        heatmapTitle.textContent = title;
        const values = chartData.map(d => d.v); const minVal = Math.min(...values); const maxVal = Math.max(...values);
        const data = { datasets: [{ label: 'Bản đồ nhiệt', data: chartData, 
            backgroundColor: (context) => { 
                if (context.raw === null) return 'transparent';
                const value = context.raw.v; 
                const alpha = (value - minVal) / (maxVal - minVal);
                // Chuyển màu từ Xanh (thấp) -> Vàng (trung bình) -> Đỏ (cao)
                const hue = (1 - alpha) * 120; // 120 (xanh lá) -> 0 (đỏ)
                return `hsla(${hue}, 100%, 50%, 0.8)`;
            }, 
            borderRadius: 4, radius: 15, hoverRadius: 18 }] };
        heatmapInstance = new Chart(canvas, { type: 'bubble', data: data, options: { plugins: { legend: { display: false }, tooltip: { callbacks: { label: function(context) { const d = context.raw; const number = d.y * 10 + d.x; return `Số ${number < 10 ? '0' : ''}${number}: ${d.v}`; } } } }, scales: { y: { min: -1, max: 10, ticks: { stepSize: 1, callback: (v) => v < 0 || v > 9 ? '' : v} }, x: { min: -1, max: 10, ticks: { stepSize: 1, callback: (v) => v < 0 || v > 9 ? '' : v} } } } });
    }

    function renderDistributionChart(canvas, title, chartData) {
        if (distributionInstance) distributionInstance.destroy();
        document.getElementById('distribution-title').textContent = title;
        distributionInstance = new Chart(canvas, { type: 'bar', data: { labels: chartData.labels, datasets: [{ label: 'Số lượng các số có cùng tần suất', data: chartData.data, backgroundColor: 'rgba(90, 142, 238, 0.7)', }] }, options: { plugins: { legend: { display: false } }, scales: { x: { title: { display: true, text: 'Số lần xuất hiện' } }, y: { title: { display: true, text: 'Số lượng các con số' } } } } });
    }

    async function generateCharts() {
        const type = chartTypeSelect.value; const days = chartDaysInput.value;
        const data = await callApi(`/charts/${type}`, { days });
        if (!data || data.error) { alert(`Không thể tải dữ liệu biểu đồ: ${data?.error ?? 'Lỗi không xác định'}`); return; }
        if (type === 'gan') {
            renderBarChart(barChartCanvas, `Top 15 Lô Gan Nhất (${days} ngày)`, data.barchart);
            renderHeatmap(heatmapChartCanvas, `Bản Đồ Nhiệt Lô Gan (${days} ngày)`, data.heatmap);
            distributionCard.classList.add('hidden');
        } else if (type === 'frequency') {
            renderBarChart(barChartCanvas, `Top 15 Số Về Nhiều Nhất (${days} ngày)`, data.barchart);
            renderHeatmap(heatmapChartCanvas, `Bản Đồ Nhiệt Tần Suất (${days} ngày)`, data.heatmap);
            renderDistributionChart(distributionChartCanvas, `Phân Phối Tần Suất (${days} ngày)`, data.distribution);
            distributionCard.classList.remove('hidden');
        }
    }
        function createResultBoardForDay(resultData) {
        const boardContainer = document.createElement('div');
        boardContainer.className = 'result-board-container';

        const prizeLayout = [
            { name: 'G.ĐB', keys: ['special'], class: 'special-prize' },
            { name: 'G.1', keys: ['prize1'] },
            { name: 'G.2', keys: ['prize2_1', 'prize2_2'] },
            { name: 'G.3', keys: ['prize3_1', 'prize3_2', 'prize3_3', 'prize3_4', 'prize3_5', 'prize3_6'] },
            { name: 'G.4', keys: ['prize4_1', 'prize4_2', 'prize4_3', 'prize4_4'] },
            { name: 'G.5', keys: ['prize5_1', 'prize5_2', 'prize5_3', 'prize5_4', 'prize5_5', 'prize5_6'] },
            { name: 'G.6', keys: ['prize6_1', 'prize6_2', 'prize6_3'] },
            { name: 'G.7', keys: ['prize7_1', 'prize7_2', 'prize7_3', 'prize7_4'], class: 'prize-7' }
        ];

        prizeLayout.forEach(prize => {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'result-row';

            const nameDiv = document.createElement('div');
            nameDiv.className = 'prize-name';
            nameDiv.textContent = prize.name;

            const numbersDiv = document.createElement('div');
            numbersDiv.className = 'prize-numbers';

            prize.keys.forEach(key => {
                const numberSpan = document.createElement('span');
                numberSpan.textContent = resultData[key] ?? 'N/A';
                if (prize.class) {
                    numberSpan.classList.add(prize.class);
                }
                numbersDiv.appendChild(numberSpan);
            });

            rowDiv.appendChild(nameDiv);
            rowDiv.appendChild(numbersDiv);
            boardContainer.appendChild(rowDiv);
        });

        return boardContainer;
    }

    // Hàm render chính cho mục Lịch Sử
    function renderHistoryResults(data) {
        const historyContainer = document.getElementById('history-results-container');
        historyContainer.innerHTML = ''; // Xóa kết quả cũ

        if (!data || data.length === 0) {
            historyContainer.innerHTML = `<div class="card"><p>Không có dữ liệu lịch sử để hiển thị.</p></div>`;
            return;
        }

        // Lặp qua từng ngày và tạo một "card" kết quả
        data.forEach(dailyResult => {
            // Tạo thẻ chứa toàn bộ kết quả của 1 ngày
            const historyCard = document.createElement('div');
            historyCard.className = 'history-card';

            // Tạo header cho thẻ (chứa ngày tháng)
            const cardHeader = document.createElement('div');
            cardHeader.className = 'history-card-header';
            cardHeader.textContent = `Kết quả ngày ${new Date(dailyResult.date).toLocaleDateString('vi-VN')}`;

            // Tạo bảng kết quả cho ngày đó
            const resultBoard = createResultBoardForDay(dailyResult);

            // Gắn header và bảng kết quả vào thẻ
            historyCard.appendChild(cardHeader);
            historyCard.appendChild(resultBoard);

            // Gắn thẻ của ngày đó vào container chính
            historyContainer.appendChild(historyCard);
        });
    }
    
    // Hàm chính được gọi khi bấm nút "Xem Lịch Sử"
    async function showHistory() {
        const limit = historyLimitInput.value;
        const data = await callApi('/history', { limit });

        if (data && !data.error) {
            // Gọi hàm render mới thay vì renderGenericTable
            renderHistoryResults(data);
        } else {
            const historyContainer = document.getElementById('history-results-container');
            historyContainer.innerHTML = `<div class="card"><p>Không tải được lịch sử. Lỗi: ${data?.error ?? 'Không xác định'}</p></div>`;
        }
    }
    
    // --- Initial Load & Event Listeners ---
    refreshDashboardBtn.addEventListener('click', updateDashboard);
    inspectNumberBtn.addEventListener('click', inspectNumber);
    backtestBtn.addEventListener('click', runBacktest);
    showHistoryBtn.addEventListener('click', showHistory);
    generateChartBtn.addEventListener('click', generateCharts);

    // Initial load for the main page
    updateDashboard();
    populateBacktestDates();
    generateCharts(); 
    showHistory();
});