
#  EdgeSentry: Predictive Maintenance Orchestrator  

<img width="1916" height="889" alt="image" src="https://github.com/user-attachments/assets/b1015cc7-5031-4a27-aaa6-e0243366ab3b" />
<img width="1909" height="873" alt="image" src="https://github.com/user-attachments/assets/0dd60c21-44e1-498d-8a20-09d4493374b0" />
<img width="1906" height="889" alt="image" src="https://github.com/user-attachments/assets/709ef791-b941-4c45-868d-397ff54ec728" />


##  Overview  
**EdgeSentry** is a smart factory dashboard and load balancer algorithm that prevents costly downtime in Industry 4.0 setups.  

It integrates **real sensor data (Arduino + CSV logs)** with **intelligent scheduling powered by a Decision Tree model** to ensure resilience under stress.  

Factories rely on **vibration, acoustic, temperature, UV, and camera sensors**. Without intelligent orchestration, these streams overload CPUs, leading to **catastrophic system failures**.  

EdgeSentry solves this by combining **heuristic overload detection** with a **Decision Tree–based scheduler** for predictive maintenance.  

---

##  Features  
- Multi-sensor monitoring (Vibration, Acoustic, Temperature, UV, Camera).  
- Heuristic overload detection: Estimates CPU load per sensor before running.  
- Three Schedulers:  
  - **Round Robin**  
  - **Strict Priority**  
  - **Intelligent (Decision Tree)**  
- Comparative performance dashboard: Stress-test schedulers on the same workload.  
- Real-time decision log: See how tasks are prioritized or dropped.  
- Factory configs: Choose **prebuilt setups (Factory Floor A/B)** or create custom ones.  

---

## Decision Tree: Intuition  
Scheduler decisions resemble **if-else rules**:  

- If CPU < 70% **and** task is high priority → ✅ run  
- If CPU > 90% **and** task is low priority → ❌ drop  

A **Decision Tree classifier** naturally models this behavior.  
Instead of hardcoding thresholds, the tree **learns from simulated task queues**.  

This enables the Intelligent scheduler to:  
- Avoid catastrophic failures
- Shed only non-critical tasks
- Maximize uptime of essential sensors  

---

## Data Pipeline  
- **Sensors used**: Vibration, Acoustic, Temperature, Humidity, UV, Camera (RGB).  
- Captured using **Arduino UNO** and exported to **CSV logs** (`sensor_log.csv`).  
- Dashboard dynamically streams from this file, simulating real-time updates.  
- Each sensor feed is separated (e.g., *Temp #1, Temp #2*), with jitter added to mimic realistic variance.  

---

## Project Structure  
EdgeSentry/ \
│── dashboard.py                  # Streamlit UI dashboard \
│── final_scheduler.py            # Scheduling algorithms + Decision Tree logic \
│── sensor_log.csv                # Sample Arduino sensor logs \
│── task_profiles.json            # Task definitions and priorities \
│── README.md                

## Installation & Execution  

### 1️. Clone Repository  
```bash
git clone https://github.com/<your-username>/EdgeSentry.git
cd EdgeSentry
```
### 2️. Setup Virtual Environment (Optional but Recommended)  
```bash
python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows
```
### 3️. Install Dependencies  
```bash
pip install -r requirements.txt
```
### 4️. Run Dashboard  
```bash
streamlit run dashboard.py
```

##  Future Enhancements  
-  Real-time Arduino streaming (no CSV).  
-  Support for **Random Forests / RL schedulers**.  
-  Multi-line factory coordination.  
