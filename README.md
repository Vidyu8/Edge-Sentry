# ⚙️ EdgeSentry: Predictive Maintenance Orchestrator  

## 📌 Overview  
**EdgeSentry** is a smart factory dashboard and load balancer that prevents costly downtime in Industry 4.0 setups.  

It integrates **real sensor data (Arduino + CSV logs)** with **intelligent scheduling powered by a Decision Tree model** to ensure resilience under stress.  

Factories rely on **vibration, acoustic, temperature, UV, and camera sensors**. Without intelligent orchestration, these streams overload CPUs, leading to **catastrophic system failures**.  

EdgeSentry solves this by combining **heuristic overload detection** with a **Decision Tree–based scheduler** for predictive maintenance.  

---

## 🚀 Features  
- 📡 Multi-sensor monitoring (Vibration, Acoustic, Temperature, UV, Camera).  
- ⚡ Heuristic overload detection: Estimates CPU load per sensor before running.  
- 🧠 Three Schedulers:  
  - **Round Robin**  
  - **Strict Priority**  
  - **Intelligent (Decision Tree)**  
- 📊 Comparative performance dashboard: Stress-test schedulers on the same workload.  
- 📝 Real-time decision log: See how tasks are prioritized or dropped.  
- 🏭 Factory configs: Choose **prebuilt setups (Factory Floor A/B)** or create custom ones.  

---

## 🧠 Decision Tree: Intuition  
Scheduler decisions resemble **if-else rules**:  

- If CPU < 70% **and** task is high priority → ✅ run  
- If CPU > 90% **and** task is low priority → ❌ drop  

A **Decision Tree classifier** naturally models this behavior.  
Instead of hardcoding thresholds, the tree **learns from simulated task queues**.  

This enables the Intelligent scheduler to:  
✅ Avoid catastrophic failures  
✅ Shed only non-critical tasks  
✅ Maximize uptime of essential sensors  

---

## 🔧 Data Pipeline  
- **Sensors used**: Vibration, Acoustic, Temperature, Humidity, UV, Camera (RGB).  
- Captured using **Arduino UNO** and exported to **CSV logs** (`sensor_log.csv`).  
- Dashboard dynamically streams from this file, simulating real-time updates.  
- Each sensor feed is separated (e.g., *Temp #1, Temp #2*), with jitter added to mimic realistic variance.  

---

## 📂 Project Structure  
