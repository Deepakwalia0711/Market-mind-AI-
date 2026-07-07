/* ═══════════════════════════════════════════════
   MarketMind AI — app.js
   Full auth + dashboard logic (pure vanilla JS)
═══════════════════════════════════════════════ */

const API_BASE_URL = window.location.origin;
let priceInterval = null;
let currentSymbol = null;

/* ═══════════════════ AUTH ═══════════════════ */

// Simple localStorage-based auth (client-side, no backend needed)
const USERS_KEY = 'mm_users';
const SESSION_KEY = 'mm_session';

function getUsers() {
    return JSON.parse(localStorage.getItem(USERS_KEY) || '{}');
}
function saveUsers(users) {
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
}
function getSession() {
    return JSON.parse(localStorage.getItem(SESSION_KEY) || 'null');
}
function saveSession(user) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(user));
}
function clearSession() {
    localStorage.removeItem(SESSION_KEY);
}

function switchTab(tab) {
    const isLogin = tab === 'login';
    document.getElementById('tabLogin').classList.toggle('active', isLogin);
    document.getElementById('tabSignup').classList.toggle('active', !isLogin);
    document.getElementById('loginForm').classList.toggle('hidden', !isLogin);
    document.getElementById('signupForm').classList.toggle('hidden', isLogin);
    document.getElementById('loginError').textContent = '';
    document.getElementById('signupError').textContent = '';
}

function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim().toLowerCase();
    const password = document.getElementById('loginPassword').value;
    const users = getUsers();
    const errEl = document.getElementById('loginError');

    if (!users[email]) {
        errEl.textContent = '❌ No account found with this email. Please sign up.';
        return;
    }
    if (users[email].password !== btoa(password)) {
        errEl.textContent = '❌ Incorrect password. Please try again.';
        return;
    }

    saveSession({ email, name: users[email].name });
    launchApp(users[email].name);
}

function handleSignup(e) {
    e.preventDefault();
    const name = document.getElementById('signupName').value.trim();
    const email = document.getElementById('signupEmail').value.trim().toLowerCase();
    const password = document.getElementById('signupPassword').value;
    const confirm = document.getElementById('signupConfirm').value;
    const users = getUsers();
    const errEl = document.getElementById('signupError');

    if (!name) { errEl.textContent = '❌ Please enter your full name.'; return; }
    if (users[email]) { errEl.textContent = '❌ An account with this email already exists.'; return; }
    if (password !== confirm) { errEl.textContent = '❌ Passwords do not match.'; return; }
    if (password.length < 6) { errEl.textContent = '❌ Password must be at least 6 characters.'; return; }

    users[email] = { name, password: btoa(password) };
    saveUsers(users);
    saveSession({ email, name });
    launchApp(name);
}

function launchApp(name) {
    document.getElementById('authScreen').classList.add('hidden');
    document.getElementById('appContainer').classList.remove('hidden');
    document.getElementById('userGreeting').textContent = `👋 ${name}`;

    // Wire up dashboard buttons now that DOM is visible
    document.getElementById('searchBtn').addEventListener('click', handleSearch);
    document.getElementById('searchInput').addEventListener('keypress', e => {
        if (e.key === 'Enter') handleSearch();
    });
}

function handleLogout() {
    clearSession();
    if (priceInterval) clearInterval(priceInterval);
    priceInterval = null;
    currentSymbol = null;
    document.getElementById('appContainer').classList.add('hidden');
    document.getElementById('authScreen').classList.remove('hidden');
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('initialScreen').classList.remove('hidden');
    document.getElementById('loginForm').reset();
    document.getElementById('signupForm').reset();
    switchTab('login');
}

// On page load: check if already logged in
window.addEventListener('DOMContentLoaded', () => {
    const session = getSession();
    if (session && session.email) {
        launchApp(session.name || session.email);
    }
});

/* ═══════════════════ DASHBOARD ═══════════════════ */

function metricHtml(label, value, colorClass = '') {
    return `<div class="metric-tile">
        <div class="label">${label}</div>
        <div class="value ${colorClass}">${value}</div>
    </div>`;
}

function getColorVal(val) {
    if (!val) return 'amber';
    const v = val.toString().toLowerCase();
    if (['bull', 'positive', 'strong'].some(w => v.includes(w))) return 'green';
    if (['bear', 'negative', 'weak'].some(w => v.includes(w))) return 'red';
    return 'amber';
}

function formatPrice(val, exchange) {
    const sym = (exchange === 'NSE' || exchange === 'BSE') ? '₹' : '$';
    return `${sym}${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

async function handleSearch() {
    const symbol = document.getElementById('searchInput').value.trim().toUpperCase();
    if (!symbol) return;

    currentSymbol = symbol;
    if (priceInterval) { clearInterval(priceInterval); priceInterval = null; }

    document.getElementById('initialScreen').classList.add('hidden');
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('loader').classList.remove('hidden');

    try {
        const [anaRes, chartRes] = await Promise.all([
            fetch(`${API_BASE_URL}/analyze/${symbol}`),
            fetch(`${API_BASE_URL}/chart-data/${symbol}`)
        ]);

        if (!anaRes.ok) throw new Error(`Server error ${anaRes.status}: ${await anaRes.text()}`);
        if (!chartRes.ok) throw new Error(`Server error ${chartRes.status}: ${await chartRes.text()}`);

        const analysis = await anaRes.json();
        const chartData = await chartRes.json();

        if (analysis.error) throw new Error(analysis.error);

        renderDashboard(analysis, chartData);
        document.getElementById('loader').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');

    } catch (err) {
        document.getElementById('loader').classList.add('hidden');
        document.getElementById('initialScreen').classList.remove('hidden');
        alert(`⚠️ Error: ${err.message}`);
    }
}

function renderDashboard(data, chartData) {
    document.getElementById('successMsg').textContent = `✅ Resolved ${data.stock} → ${data.resolved_symbol}`;

    /* ── ROW 1: Decision ── */
    const badge = document.getElementById('decisionBadge');
    badge.textContent = data.decision.toUpperCase();
    badge.className = `badge badge-${data.decision.toLowerCase()}`;

    document.getElementById('scoreVal').textContent = data.confidence.toFixed(1);
    document.getElementById('confBarFill').style.width = `${Math.min(data.confidence, 100)}%`;

    /* ── ROW 1: Live Prices ── */
    const pricesHtml = Object.entries(data.prices || {}).map(([exc, val]) =>
        metricHtml(`🟢 Live · ${exc}`, formatPrice(val, exc))
    ).join('');
    document.getElementById('livePricesRow').innerHTML = pricesHtml;

    // 3-second live price polling
    priceInterval = setInterval(async () => {
        if (!currentSymbol) return;
        try {
            const r = await fetch(`${API_BASE_URL}/price/${currentSymbol}`);
            if (!r.ok) return;
            const d = await r.json();
            if (d.prices) {
                document.getElementById('livePricesRow').innerHTML =
                    Object.entries(d.prices).map(([exc, val]) =>
                        metricHtml(`🟢 Live · ${exc}`, formatPrice(val, exc))
                    ).join('');
            }
        } catch (_) { }
    }, 3000);

    /* ── ROW 1.5: Prediction & Risk ── */
    const pred = data.prediction || {};
    const risk = data.risk || {};

    document.getElementById('predictionRow').innerHTML = [
        metricHtml('Today Range', `₹${pred.today_low ?? 'N/A'} – ${pred.today_high ?? 'N/A'}`),
        metricHtml('Tomorrow Range', `₹${pred.tomorrow_low ?? 'N/A'} – ${pred.tomorrow_high ?? 'N/A'}`),
        metricHtml('Next Week Range', `₹${pred.next_week_low ?? 'N/A'} – ${pred.next_week_high ?? 'N/A'}`),
        metricHtml('Prediction Probability', pred.probability || 'N/A', 'green'),
        metricHtml('AI Risk Meter', risk.signal || 'Unknown',
            risk.signal?.includes('Low') ? 'green' :
                risk.signal?.includes('Moderate') ? 'amber' : 'red')
    ].join('');

    /* ── ROW 2: Signals ── */
    const hist = data.history || {};
    const tech = data.technical || {};
    const newsData = data.news || {};
    const trend = hist.trend || 'Neutral';
    const change = hist.change_pct ?? 0;
    const rsi = tech.RSI ?? 50;
    const smaSig = tech.sma_signal || 'Neutral';
    const macdTrend = tech.macd_trend || 'Neutral';
    const newsSent = newsData.sentiment || 'Neutral';

    document.getElementById('signalsRow').innerHTML = [
        metricHtml('2Y Trend', trend, getColorVal(trend)),
        metricHtml('Change', `${change >= 0 ? '+' : ''}${change.toFixed(1)}%`, change >= 0 ? 'green' : 'red'),
        metricHtml('RSI-14', rsi.toFixed(1), rsi > 70 ? 'red' : rsi < 30 ? 'green' : 'amber'),
        metricHtml('MACD', macdTrend, getColorVal(macdTrend)),
        metricHtml('News', newsSent, getColorVal(newsSent))
    ].join('');

    /* ── ROW 3: Charts ── */
    const pat = data.pattern || {};
    if (pat.pattern && pat.pattern !== 'None') {
        const c = pat.signal?.includes('Bullish') ? '#10b981' : '#ef4444';
        document.getElementById('patternDetected').innerHTML =
            `<strong>Pattern Detected:</strong> <span style="color:${c}">${pat.pattern}</span> (Confidence: ${pat.confidence})`;
    } else {
        document.getElementById('patternDetected').innerHTML = '';
    }
    renderCandlestick(chartData, tech);
    renderWaterfall(data.agent_scores || {}, data.confidence);

    /* ── Reasons ── */
    document.getElementById('reasonsList').innerHTML = (data.reasons || []).map(r => {
        const rl = r.toLowerCase();
        const icon = ['bull', 'positive', 'healthy', 'oversold', 'strength', 'above'].some(w => rl.includes(w)) ? '🟢'
            : ['bear', 'negative', 'overbought', 'caution', 'below', 'risk'].some(w => rl.includes(w)) ? '🔴' : '🟡';
        return `<p>${icon} ${r}</p>`;
    }).join('');

    /* ── ROW 4: Technical ── */
    document.getElementById('techRow').innerHTML = [
        metricHtml('SMA 20', `₹${tech.sma20 || 'N/A'}`),
        metricHtml('SMA 50', `₹${tech.sma50 || 'N/A'}`),
        metricHtml('SMA Signal', smaSig, getColorVal(smaSig)),
        metricHtml('Volatility', `${(hist.volatility || 0).toFixed(2)}% /day`)
    ].join('');

    /* ── ROW 5: Moneycontrol ── */
    const mc = data.moneycontrol || {};
    if (mc && Object.keys(mc).length > 0) {
        document.getElementById('mcSection').classList.remove('hidden');
        document.getElementById('mcTitle').textContent = mc.company_name || data.resolved_symbol;
        document.getElementById('mcSector').textContent = mc.sector || '—';
        document.getElementById('mcLink').innerHTML = mc.mc_url
            ? `<a href="${mc.mc_url}" target="_blank" style="color:#60a5fa;">↗ View on Moneycontrol</a>` : '';

        const metrics = mc.metrics || {};
        document.getElementById('mcMetricsRow').innerHTML = [
            ['market_cap_cr', 'Mkt Cap (Cr)'], ['pe', 'P/E (TTM)'],
            ['sector_pe', 'Sector P/E'], ['pb', 'P/B'], ['eps', 'EPS (TTM)']
        ].filter(([k]) => metrics[k])
            .map(([k, l]) => metricHtml(l, metrics[k]))
            .join('');

        const swot = mc.swot || {};
        const mcAna = mc.analysis || {};
        const getItems = key => Object.entries(swot).find(([k]) => k.toLowerCase().includes(key))?.[1] || [];

        const renderSwot = (cls, title, key) => {
            const items = getItems(key);
            const apiField = key === 'opportunit' ? 'opportunities' : key === 'weakness' ? 'weaknesses' : key + 's';
            const count = mcAna[`${apiField}_total`] ?? items.length;
            const lis = items.slice(0, 2).map(i => `<li>${i.substring(0, 60)}${i.length > 60 ? '…' : ''}</li>`).join('');
            return `<div class="swot-box ${cls}">
                <div class="swot-label">${title}</div>
                <div class="swot-count">${count}</div>
                <ul>${lis}</ul>
            </div>`;
        };

        document.getElementById('swotRow').innerHTML = [
            renderSwot('swot-s', '💪 Strengths', 'strength'),
            renderSwot('swot-w', '⚠️ Weaknesses', 'weakness'),
            renderSwot('swot-o', '🚀 Opportunities', 'opportunit'),
            renderSwot('swot-t', '🔥 Threats', 'threat')
        ].join('');
    } else {
        document.getElementById('mcSection').classList.add('hidden');
    }

    /* ── ROW 6: News ── */
    const sentColor = newsSent === 'Positive' ? '#10b981' : newsSent === 'Negative' ? '#ef4444' : '#f59e0b';
    document.getElementById('newsSentimentCard').innerHTML = `
        <div class="label">Overall</div>
        <div style="font-size:1.8rem;font-weight:800;color:${sentColor};margin:0.4rem 0;">${newsSent}</div>
        <div style="color:#64748b;font-size:0.85rem;">${newsData.news_count || 0} articles analysed</div>`;

    const articles = newsData.articles || [];
    document.getElementById('newsList').innerHTML = articles.length > 0
        ? articles.map(a => {
            const pub = a.publishedAt ? a.publishedAt.substring(0, 10) : '';
            const source = a.source?.name || '';
            return `<div class="news-item">
                <a href="${a.url || '#'}" target="_blank">${a.title || 'No title'}</a>
                <div class="news-meta">📅 ${pub}${source ? ' · ' + source : ''}</div>
            </div>`;
        }).join('')
        : '<p style="color:#94a3b8; padding:1rem;">No recent news found.</p>';

    /* ── ROW 7: Backtesting ── */
    const bt = data.backtesting || {};
    document.getElementById('backtestRow').innerHTML = [
        metricHtml('Total Return', bt.total_return || 'N/A', 'green'),
        metricHtml('Annualized', bt.annualized_return || 'N/A', 'green'),
        metricHtml('Win Rate', bt.win_rate || 'N/A'),
        metricHtml('Max Drawdown', bt.max_drawdown || 'N/A', 'red')
    ].join('');
    document.getElementById('backtestCaption').textContent =
        `Strategy: ${bt.strategy || '—'} | Signal: ${bt.signal || '—'}`;
}

/* ═══════════════════ CHARTS ═══════════════════ */

let lwChart = null;
function renderCandlestick(data, tech) {
    const container = document.getElementById('candlestickChart');
    
    if (lwChart) {
        lwChart.remove();
        lwChart = null;
    }
    container.innerHTML = '';

    lwChart = LightweightCharts.createChart(container, {
        layout: {
            background: { type: 'solid', color: '#060d1a' },
            textColor: '#94a3b8',
        },
        grid: {
            vertLines: { color: '#1e3a5f' },
            horzLines: { color: '#1e3a5f' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: '#1e3a5f',
        },
        timeScale: {
            borderColor: '#1e3a5f',
            timeVisible: false,
        },
    });

    const candlestickSeries = lwChart.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
    });

    const chartData = [];
    for (let i = 0; i < data.dates.length; i++) {
        if (!data.open[i] || !data.high[i] || !data.low[i] || !data.close[i]) continue;
        chartData.push({
            time: data.dates[i],
            open: data.open[i],
            high: data.high[i],
            low: data.low[i],
            close: data.close[i],
        });
    }
    candlestickSeries.setData(chartData);

    if (data.sma20 && data.sma20.length > 0) {
        const sma20Series = lwChart.addLineSeries({
            color: '#f59e0b',
            lineWidth: 2,
            lineStyle: 1, // Dashed
        });
        const sma20Data = [];
        for (let i = 0; i < data.dates.length; i++) {
            if (data.sma20[i]) {
                sma20Data.push({ time: data.dates[i], value: data.sma20[i] });
            }
        }
        sma20Series.setData(sma20Data);
    }

    if (data.sma50 && data.sma50.length > 0) {
        const sma50Series = lwChart.addLineSeries({
            color: '#a78bfa',
            lineWidth: 2,
            lineStyle: 1, // Dashed
        });
        const sma50Data = [];
        for (let i = 0; i < data.dates.length; i++) {
            if (data.sma50[i]) {
                sma50Data.push({ time: data.dates[i], value: data.sma50[i] });
            }
        }
        sma50Series.setData(sma50Data);
    }
    
    lwChart.timeScale().fitContent();

    new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== container) { return; }
        const newRect = entries[0].contentRect;
        lwChart.applyOptions({ height: newRect.height, width: newRect.width });
    }).observe(container);
}

function renderWaterfall(agentScores, finalScore) {
    const weights = {
        Historical: 0.05, Technical: 0.20, News: 0.10, Moneycontrol: 0.10,
        Fundamental: 0.20, Sentiment: 0.10, Insider: 0.05, Sector: 0.10
    };

    const x = ['Base'], y = [0], measure = ['relative'], text = ['0'];

    for (const [k, w] of Object.entries(weights)) {
        if (agentScores[k] !== undefined) {
            const val = agentScores[k] * w;
            x.push(k); y.push(val); measure.push('relative');
            text.push(`${val >= 0 ? '+' : ''}${val.toFixed(1)}`);
        }
    }

    if (agentScores['Risk Penalty'] !== undefined) {
        x.push('Risk Penalty'); y.push(agentScores['Risk Penalty']);
        measure.push('relative'); text.push(agentScores['Risk Penalty'].toFixed(1));
    }

    x.push('Total AI Score'); y.push(finalScore);
    measure.push('total'); text.push(finalScore.toFixed(1));

    Plotly.newPlot('waterfallChart', [{
        type: 'waterfall', orientation: 'v',
        name: 'AI Score', measure, x, y, text,
        textposition: 'outside',
        decreasing: { marker: { color: '#ef4444' } },
        increasing: { marker: { color: '#10b981' } },
        totals: { marker: { color: '#38bdf8' } },
    }], {
        paper_bgcolor: '#0d1f35',
        plot_bgcolor: '#0d1f35',
        margin: { l: 40, r: 15, t: 30, b: 40 },
        font: { family: 'Inter', color: '#94a3b8' },
        xaxis: { tickangle: -45 }
    }, { responsive: true });
}
