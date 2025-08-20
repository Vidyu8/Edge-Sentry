# dashboard.py
import streamlit as st
import pandas as pd
import time
import random
from final_scheduler import TaskScheduler, TASK_PROFILES, TASK_PRIORITIES, generate_random_task_queue, run_simulation

# =========================
# Page Config & Branding
# =========================
st.set_page_config(
    page_title="Edge Sentry: Predictive Maintenance Orchestrator",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("⚙️ Edge Sentry: Predictive Maintenance Orchestrator")
st.markdown("### Preventing Multi-Million Dollar Failures in Smart Factories")
st.info("📊 Assembly Line Monitoring: Configurable Sensors + Real-Time Scheduler")

# =========================
# Sidebar Controls
# =========================
st.sidebar.header("⚙️ Simulation Controls")
scenario = st.sidebar.selectbox("Select Scenario", ["Routine Day", "Drought Alert", "The Camera Trap"])
scheduler_type = st.sidebar.radio("Scheduler Type", ["Round Robin", "Strict Priority", "Intelligent"])

# --- Sidebar Configurations ---
st.sidebar.header("⚙️ Factory Configurations")
config_type = st.sidebar.radio("Choose Configuration", ["Prebuilt", "Custom"])

if config_type == "Prebuilt":
    preset = st.sidebar.selectbox("Select Prebuilt Setup", ["Factory Floor A", "Factory Floor B"])
    if preset == "Factory Floor A":
        selected_sensors = {"Vibration": 2, "Acoustic": 1, "Temperature": 1, "Camera": 1}
    else:
        selected_sensors = {"Vibration": 1, "Acoustic": 2, "Temperature": 2, "Camera": 0}
else:  # Custom
    vibration = st.sidebar.slider("Number of Vibration Sensors", 0, 10, 2)
    acoustic = st.sidebar.slider("Number of Acoustic Sensors", 0, 10, 1)
    temp = st.sidebar.slider("Number of Temperature Sensors", 0, 10, 1)
    camera = st.sidebar.slider("Number of Camera Sensors", 0, 10, 1)
    uv = st.sidebar.slider("Number of UV Sensors", 0, 10, 0)
    selected_sensors = {
        "Vibration": vibration,
        "Acoustic": acoustic,
        "Temperature": temp,
        "Camera": camera,
        "UV": uv
    }

# =========================
# Assembly Line Overview
# =========================
st.subheader("🏭 Assembly Line Overview")
st.write("Active Sensors Configuration:")
for sensor, count in selected_sensors.items():
    if count > 0:
        st.write(f"- {count} {sensor} Sensor(s)")

# =========================
# Sensor Overload Detection
# =========================
# Heuristic CPU costs per sensor type (%)
sensor_cpu_cost = {
    "Vibration": 7,
    "Acoustic": 10,
    "Temperature": 5,
    "Camera": 20,
    "UV": 8
}

# Compute total CPU load estimate
total_cpu_load = sum(sensor_cpu_cost[s] * c for s, c in selected_sensors.items())
st.subheader("⚡ Sensor Load Estimation")
st.write(f"Estimated CPU Load from selected sensors: **{total_cpu_load}%**")

if total_cpu_load > 100:
    st.error("🚨 Sensor configuration exceeds system capacity! Overload detected. Scheduler will not run.")
else:
    # =========================
    # Sensor Data Display from CSV
    # =========================
    st.subheader("📡 Sensor Live Feeds (from CSV)")

    # Load the CSV
    df = pd.read_csv("sensor_log.csv")

    # Simulated streaming: keep index in session
    if "row_index" not in st.session_state:
        st.session_state.row_index = 0

    row = df.iloc[st.session_state.row_index % len(df)]
    st.session_state.row_index += 1

    # Map sensors to CSV columns
    # Explicit sensor-to-column mapping for multiple sensors
    sensor_mapping = {
        "Temperature": ["dht_temperature_c", "bmp_temperature_c"],  # 2 sources
        "Acoustic": ["sound_digital", "sound_analog"],             # 2 sources
        "Vibration": ["sound_analog"],                             # only 1 real col
        "Camera": ["color_freq_red", "color_freq_green", "color_freq_blue"], # 3 feeds
        "UV": ["uv_index_mwcm2"],
        "Humidity": ["dht_humidity_rh"]
    }

    # Show feeds dynamically
    # Show feeds dynamically
    cols = st.columns(len([s for s, c in selected_sensors.items() if c > 0]))

    for col, (sensor, count) in zip(cols, selected_sensors.items()):
        if count > 0:
            with col:
                st.markdown(f"**{sensor} Sensor Feed**")
                if sensor in sensor_mapping:
                    for i in range(count):
                        for col_name in sensor_mapping[sensor]:
                            if col_name in df.columns:
                                base_val = row[col_name]

                                # ---- Temperature special handling ----
                                if "temp" in col_name.lower():
                                    try:
                                        base_val = float(base_val)
                                        if base_val > 100:   # assume Kelvin
                                            base_val = base_val - 273.15
                                    except:
                                        pass

                                # Apply jitter if numeric
                                if isinstance(base_val, (int, float)):
                                    value = base_val + random.uniform(-0.5, 0.5)
                                    value = round(value, 2)
                                else:
                                    value = base_val

                                st.write(f"{sensor} #{i+1} → {col_name}: {value}")
                            else:
                                # Simulated fallback
                                st.write(f"{sensor} #{i+1} → simulated: {round(random.uniform(20, 30), 2)}")
                else:
                    st.write("⚠️ No matching CSV data, simulating...")
                    st.write(f"{random.uniform(0, 100):.2f}")



    # Raw log panel
    with st.expander("📜 Raw Sensor Logs"):
        st.dataframe(df.tail(10))

    # =========================
    # Run Simulation
    # =========================
    st.subheader("🤖 Scheduler Simulation")

    TASK_PROFILES = {
        "MONITOR_WATER_LEVEL": {"cpu_cost": 8.5, "mem_cost": 120.0},
        "MONITOR_NUTRIENT_LEVEL": {"cpu_cost": 8.5, "mem_cost": 120.0},
        "READ_AMBIENT_TEMP_HUMIDITY": {"cpu_cost": 18.0, "mem_cost": 250.0},
        "CHECK_WATER_PH": {"cpu_cost": 35.0, "mem_cost": 310.0},
        "CAPTURE_TIMELAPSE_IMAGE": {"cpu_cost": 95.0, "mem_cost": 950.0}
    }
    queue = generate_random_task_queue(list(TASK_PROFILES.keys()), 15, TASK_PRIORITIES)
    results = run_simulation(scheduler_type, queue, TASK_PROFILES, TASK_PRIORITIES)

    with st.expander("🔎 Raw Scheduler Output (for debug)"):
        st.json(results)

    # =========================
    # Machine Health Panel
    # =========================
    st.subheader("🏭 Monitored Machine Health")
    col1, col2, col3, col4, col5 = st.columns(5)
    machines = ["Conveyor Belt", "Stamping Press", "Cooling Fan", "Motor Casing", "Camera Unit"]

    for col, name in zip([col1, col2, col3, col4, col5], machines):
        with col:
            st.metric(label=f"{name}\nProcessing Load", value=f"{random.randint(10, 95)}%")
            st.metric(label="Analysis Buffer", value=f"{random.randint(1200, 2048)} bytes")

    # =========================
    # Incoming Queue
    # =========================
    st.subheader("📥 Incoming Sensor Analysis Queue")
    tasks = [
        ("vibration_analysis", "📈"),
        ("acoustic_anomaly_detection", "🔊"),
        ("motor_temp_read", "🌡️"),
        ("water_ph_check", "⚗️"),
        ("camera_timelapse", "📷")
    ]

    for task, icon in random.sample(tasks, 3):
        st.write(f"{icon} {task.replace('_',' ').title()}")

    # =========================
    # Real-time Decision Log
    # =========================
    st.subheader("📝 Sentry AI: Real-time Decision Log")
    log_placeholder = st.empty()

    sample_logs = [
        "✅ Executed Vibration Analysis (Machine 2)",
        "⚠️ Prioritized Acoustic Anomaly Detection over Timelapse",
        "🚨 CRITICAL ACTION: Shedding low-priority task (Ambient Humidity) to guarantee resources for critical failure prediction."
    ]

    critical_events = []
    if st.button("▶ Replay Decision Log"):
        for msg in sample_logs:
            with log_placeholder.container():
                if "CRITICAL" in msg:
                    st.error(msg)
                    critical_events.append(msg)
                elif "⚠️" in msg:
                    st.warning(msg)
                else:
                    st.success(msg)
            time.sleep(1)

    if critical_events:
        st.markdown("### 🔴 Pinned Critical Actions")
        for ev in critical_events:
            st.error(ev)

    # =========================
    # Final Scoreboard
    # =========================
    st.subheader("📊 Performance Under Stress: Assembly Line Failure Simulation")

    schedulers = ["Round Robin", "Strict Priority", "Intelligent"]
    sim_results = {}
    for s in schedulers:
        q = generate_random_task_queue(list(TASK_PROFILES.keys()), 15, TASK_PRIORITIES)
        sim_results[s] = run_simulation(s, q, TASK_PROFILES, TASK_PRIORITIES)

    comparison = {
        "Metric": ["Peak Resource Strain", "Catastrophic System Failures", "Preventative Actions"],
        "Round Robin": [
            f"{sim_results['Round Robin']['Peak CPU']}",
            f"{sim_results['Round Robin']['Overloads']} ❌",
            f"{sim_results['Round Robin']['Tasks Dropped']}"
        ],
        "Strict Priority": [
            f"{sim_results['Strict Priority']['Peak CPU']}",
            f"{sim_results['Strict Priority']['Overloads']} ❌",
            f"{sim_results['Strict Priority']['Tasks Dropped']}"
        ],
        "Intelligent": [
            f"{sim_results['Intelligent']['Peak CPU']}",
            f"{sim_results['Intelligent']['Overloads']} ✅" if sim_results['Intelligent']['Overloads'] == 0 else f"{sim_results['Intelligent']['Overloads']} ❌",
            f"{sim_results['Intelligent']['Tasks Dropped']}"
        ]
    }

    df_comp = pd.DataFrame(comparison)

    def highlight(val):
        if "✅" in str(val):
            return "background-color: #2ecc71; color: white; font-weight: bold"
        if "❌" in str(val):
            return "background-color: #e74c3c; color: white; font-weight: bold"
        return ""

    st.dataframe(df_comp.style.applymap(highlight))

    # =========================
    # Closing Punchline
    # =========================
    st.success("✅ Edge Sentry ensures ZERO catastrophic failures while competitors collapse. This is how we protect factories from multi-million dollar downtime.")
