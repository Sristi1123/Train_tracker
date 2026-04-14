// Initialize based on which page we are on
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('searchBtn')) {
        initHome();
    } else if (document.getElementById('backBtn')) {
        initDashboard();
    }
});

function initHome() {
    const searchBtn = document.getElementById('searchBtn');
    const trainInput = document.getElementById('trainInput');
    const loader = document.getElementById('loader');
    const errorMsg = document.getElementById('errorMsg');
    const resultCard = document.getElementById('resultCard');

    searchBtn.addEventListener('click', async () => {
        const trainNo = trainInput.value.trim();
        if(!trainNo) return;

        // Reset UI
        resultCard.classList.add('hidden');
        errorMsg.classList.add('hidden');
        loader.classList.remove('hidden');

        try {
            const res = await fetch(`/api/train-status?number=${trainNo}`);
            const data = await res.json();

            if (!res.ok || data.error) {
                throw new Error(data.error || "Train not found.");
            }

            // Populate Result Card
            document.getElementById('r-train-name').innerText = data.train_name;
            document.getElementById('r-source').innerText = data.source;
            document.getElementById('r-dest').innerText = data.destination;
            document.getElementById('r-departure').innerText = data.departure;
            document.getElementById('r-arrival').innerText = data.arrival;
            document.getElementById('r-location').innerText = data.current_location;

            // Status Badge
            const badge = document.getElementById('r-status-badge');
            badge.innerText = data.status.label;
            badge.className = `badge ${data.status.color}`;

            // ML Box
            document.getElementById('r-prediction').innerText = data.prediction_label;
            document.getElementById('r-confidence').innerText = data.confidence;
            document.getElementById('r-reason').innerText = data.reason;

            // Show Card
            loader.classList.add('hidden');
            resultCard.classList.remove('hidden');

            // Store train number for dashboard
            document.getElementById('viewDashboardBtn').onclick = () => {
                window.location.href = `/dashboard?train=${trainNo}`;
            };

        } catch (err) {
            loader.classList.add('hidden');
            errorMsg.innerText = err.message || "Failed to connect to backend.";
            errorMsg.classList.remove('hidden');
        }
    });
}

function initDashboard() {
    document.getElementById('backBtn').onclick = () => window.location.href = '/';

    const urlParams = new URLSearchParams(window.location.search);
    const trainNo = urlParams.get('train') || "Unknown";
    document.getElementById('d-train-name').innerText = trainNo;

    // Fetch Dashboard Data
    fetch(`/api/dashboard?train=${trainNo}`)
        .then(res => res.json())
        .then(data => {
            // Populate metrics
            document.getElementById('d-avg-delay').innerText = data.avg_delay;
            document.getElementById('d-ontime').innerText = data.ontime_rate;
            document.getElementById('d-peak-season').innerText = data.peak_season;
            document.getElementById('d-busiest').innerText = data.busiest_month;
            
            document.getElementById('d-dist').innerText = `${data.distance_km} km`;
            document.getElementById('d-dur').innerText = `${data.duration_hrs} hrs`;
            document.getElementById('d-speed').innerText = data.avg_speed;
            document.getElementById('d-class').innerText = data.train_class;

            // Populate Season Heatmap Tiles
            const sContainer = document.getElementById('seasonCards');
            Object.keys(data.delay_by_season).forEach(season => {
                const s = data.delay_by_season[season];
                sContainer.innerHTML += `
                    <div class="s-card ${s.color}">
                        <h4>${s.emoji} ${season}</h4>
                        <p>${s.delay} avg delay</p>
                    </div>
                `;
            });

            // Initialize Charts
            initCharts(data);
        })
        .catch(err => {
            console.error(err);
            alert("Failed to load dashboard data.");
        });
}

function initCharts(data) {
    Chart.defaults.color = '#A0AABF';
    Chart.defaults.font.family = 'Inter';

    // 1. Demand Trend (Line Chart)
    const ctxDemand = document.getElementById('demandChart').getContext('2d');
    new Chart(ctxDemand, {
        type: 'line',
        data: {
            labels: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
            datasets: [{
                label: 'Relative Demand',
                data: data.monthly_demand,
                borderColor: '#6C63FF',
                tension: 0.4,
                pointBackgroundColor: '#4ECDC4'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, min: 0, max: 100 },
                x: { grid: { display: false } }
            },
            plugins: { legend: { display: false } }
        }
    });

    // 2. Cancellation Chart (Bar)
    const ctxCancel = document.getElementById('cancellationChart').getContext('2d');
    new Chart(ctxCancel, {
        type: 'bar',
        data: {
            labels: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
            datasets: [{
                label: 'Cancellations',
                data: data.cancellations_by_month,
                backgroundColor: '#E74C3C',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { stepSize: 1 } },
                x: { grid: { display: false } }
            },
            plugins: { legend: { display: false } },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}
