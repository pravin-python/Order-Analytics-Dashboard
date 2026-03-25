/**
 * OrderPulse — Charts Module
 * Chart.js initialization and update functions.
 */

OrderPulse.Charts = OrderPulse.Charts || {};

// Design system color tokens
const COLORS = {
    PA: { bg: 'rgba(163, 166, 255, 0.7)', border: '#a3a6ff' },  // Primary - Blue
    PI: { bg: 'rgba(193, 128, 255, 0.7)', border: '#c180ff' },  // Secondary - Purple
    MA: { bg: 'rgba(90, 228, 208, 0.7)', border: '#5ae4d0' },   // Tertiary - Teal
    BL: { bg: 'rgba(245, 158, 11, 0.7)', border: '#f59e0b' },   // Warning - Amber
};

const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false
        },
        tooltip: {
            backgroundColor: '#1d1f27',
            titleColor: '#e5e4ed',
            bodyColor: '#aaaab3',
            borderColor: 'rgba(70, 72, 79, 0.3)',
            borderWidth: 1,
            cornerRadius: 8,
            padding: 12,
            titleFont: { family: 'Inter', weight: '600' },
            bodyFont: { family: 'Inter' }
        }
    }
};

let barChart, donutChart, lineChart;

// ============= Initialization =============
OrderPulse.Charts.init = function () {
    OrderPulse.Charts._initBar();
    OrderPulse.Charts._initDonut();
    OrderPulse.Charts._initLine();
};

OrderPulse.Charts._initBar = function () {
    const ctx = document.getElementById('barChart');
    if (!ctx) return;

    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['PA', 'PI', 'MA', 'BL'],
            datasets: [
                {
                    label: 'Within 24h',
                    data: [0, 0, 0, 0],
                    backgroundColor: 'rgba(90, 228, 208, 0.6)',
                    borderColor: '#5ae4d0',
                    borderWidth: 1,
                    borderRadius: 6,
                    barPercentage: 0.7,
                    categoryPercentage: 0.6
                },
                {
                    label: 'Beyond 24h',
                    data: [0, 0, 0, 0],
                    backgroundColor: 'rgba(245, 158, 11, 0.6)',
                    borderColor: '#f59e0b',
                    borderWidth: 1,
                    borderRadius: 6,
                    barPercentage: 0.7,
                    categoryPercentage: 0.6
                }
            ]
        },
        options: {
            ...CHART_DEFAULTS,
            scales: {
                x: {
                    grid: { color: 'rgba(70, 72, 79, 0.08)' },
                    ticks: { color: '#aaaab3', font: { family: 'Inter', size: 12 } }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(70, 72, 79, 0.08)' },
                    ticks: { color: '#aaaab3', font: { family: 'Inter', size: 11 } }
                }
            }
        }
    });
};

OrderPulse.Charts._initDonut = function () {
    const ctx = document.getElementById('donutChart');
    if (!ctx) return;

    donutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['PA', 'PI', 'MA', 'BL'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: [
                    COLORS.PA.bg, COLORS.PI.bg, COLORS.MA.bg, COLORS.BL.bg
                ],
                borderColor: [
                    COLORS.PA.border, COLORS.PI.border, COLORS.MA.border, COLORS.BL.border
                ],
                borderWidth: 2,
                cutout: '65%',
                hoverOffset: 8
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            plugins: {
                ...CHART_DEFAULTS.plugins,
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        color: '#aaaab3',
                        font: { family: 'Inter', size: 12 },
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                }
            }
        }
    });
};

OrderPulse.Charts._initLine = function () {
    const ctx = document.getElementById('lineChart');
    if (!ctx) return;

    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, 'rgba(163, 166, 255, 0.3)');
    gradient.addColorStop(1, 'rgba(163, 166, 255, 0.0)');

    lineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Orders',
                data: [],
                borderColor: '#a3a6ff',
                backgroundColor: gradient,
                borderWidth: 2.5,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#a3a6ff',
                pointBorderColor: '#0c0e14',
                pointBorderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#a3a6ff',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    grid: { color: 'rgba(70, 72, 79, 0.06)' },
                    ticks: { color: '#aaaab3', font: { family: 'Inter', size: 11 }, maxRotation: 45 }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(70, 72, 79, 0.08)' },
                    ticks: { color: '#aaaab3', font: { family: 'Inter', size: 11 } }
                }
            }
        }
    });
};

// ============= Update Functions =============
OrderPulse.Charts.updateBar = function (dispatchData) {
    if (!barChart || !dispatchData) return;

    const stores = ['PA', 'PI', 'MA', 'BL'];
    const within = stores.map(s => dispatchData.by_store?.within?.[s] || 0);
    const beyond = stores.map(s => dispatchData.by_store?.beyond?.[s] || 0);

    barChart.data.datasets[0].data = within;
    barChart.data.datasets[1].data = beyond;
    barChart.update('active');
};

OrderPulse.Charts.updateDonut = function (distribution) {
    if (!donutChart || !distribution) return;

    const stores = ['PA', 'PI', 'MA', 'BL'];
    donutChart.data.datasets[0].data = stores.map(s => distribution[s] || 0);
    donutChart.update('active');
};

OrderPulse.Charts.updateLine = function (ordersOverTime) {
    if (!lineChart || !ordersOverTime) return;

    const labels = Object.keys(ordersOverTime);
    const values = Object.values(ordersOverTime);

    lineChart.data.labels = labels;
    lineChart.data.datasets[0].data = values;
    lineChart.update('active');
};

