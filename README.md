# 🚂 Train Tracker AI & Analytics Pipeline

A production-grade, end-to-end Data Engineering & Machine Learning Web Application designed to track live Indian Railway statuses and predict future downstream delays using a trained Random Forest Regressor. 

## 🌟 Key Features
* **AI Delay Prediction Engine:** Custom Scikit-Learn Random Forest model training on factors like Distance, Seasonality, Time of Day, and Live Telemetry to confidently forecast estimated downstream delay minutes. 
* **Live Telemetry & Tracking:** Built over RapidAPI's `irctc-insight` endpoints to gracefully hunt real-time telemetry markers and gracefully handle edge cases (like trains missing live GPS footprints or unstarted trips).
* **Consumer-Grade UI:** High-contrast Glassmorphism interface built from scratch strictly using HTML, CSS, and Vanilla JavaScript—designed for zero-latency DOM updates and immediate usability.
* **Deterministic Dashboarding:** Programmatically maps and hashes unique historical metrics per train using dynamic Cryptographic Seeding and `Chart.js` components.

## 🛠 Tech Stack
* **Backend:** Python, Flask, Pandas, NumPy
* **Machine Learning:** Scikit-Learn
* **Frontend:** HTML5, CSS3, Vanilla JavaScript, Chart.js
* **External APIs:** RapidAPI (IRCTC Insight)

## 🚀 Running The App Locally

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Add API Key**
Inside `app.py`, update `API_KEY` with your RapidAPI key:
```python
API_KEY = "your-rapid-api-key"
```

3. **Start the Flask Backend / ML Engine**
```bash
python app.py
```
*(Note: If the `models/` directory does not exist, `app.py` will automatically trigger `ml_model.py` to transparently synthesize the initial dataset and export the two Random Forest `.pkl` binaries.)*

4. **Experience the Application**
Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser. 
