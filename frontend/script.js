document.getElementById('searchBtn').addEventListener('click', async () => {
    const trainInput = document.getElementById('trainInput').value;
    if (!trainInput) return;

    // UI State: Loading
    document.getElementById('loader').classList.remove('hidden');
    document.getElementById('resultCard').classList.add('hidden');

    try {
        // Fetch from our local Flask backend
        const response = await fetch(`http://localhost:5000/api/track?train_no=${trainInput}`);
        const data = await response.json();

        // UI State: Success
        document.getElementById('loader').classList.add('hidden');
        document.getElementById('resultCard').classList.remove('hidden');

        // Populate API Data
        if (data.live_api && data.live_api.data) {
            const api = data.live_api.data;
            document.getElementById('trainName').innerText = api.trainName || `Train ${trainInput}`;
            
            document.getElementById('startCode').innerText = api.currentStation ? api.currentStation.substring(0,4).toUpperCase() : 'N/A';
            document.getElementById('startName').innerText = api.currentStation || 'Unknown';
            
            document.getElementById('endCode').innerText = api.nextStation ? api.nextStation.substring(0,4).toUpperCase() : 'N/A';
            document.getElementById('endName').innerText = api.nextStation || 'Unknown';
            
            document.getElementById('arrivalTime').innerText = api.estimatedArrivalTime || '--:--';
        }

        // Populate ML Prediction Data
        if (data.prediction) {
            const pred = data.prediction;
            const statusBadge = document.getElementById('statusBadge');
            
            statusBadge.innerText = pred.tag;
            document.getElementById('mlMessage').innerText = pred.message;
            document.getElementById('mlConfidence').innerText = `${pred.confidence}% Confident`;

            if (pred.tag.includes('DELAY')) {
                statusBadge.classList.replace('landed', 'delayed');
                document.getElementById('mlConfidence').style.color = '#f87171';
            } else {
                statusBadge.classList.replace('delayed', 'landed');
                document.getElementById('mlConfidence').style.color = '#34d399';
            }
        }

    } catch (error) {
        console.error("Failed to fetch data", error);
        document.getElementById('loader').classList.add('hidden');
        alert("Failed to connect to the backend server. Make sure `python backend.py` is running.");
    }
});
