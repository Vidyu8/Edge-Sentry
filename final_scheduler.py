# scheduler.py (Final Version with Explainability)

import numpy as np
import copy
import random

# --- Constants ---
TOTAL_SRAM = 2048
SIMULATION_DEPTH = 5
CHOICES_TO_SIMULATE = 3

# --- Weights for the Cost Function ---
COST_WEIGHT_CPU_LOAD = 1.0
COST_WEIGHT_MEM_LOAD = 0.005
COST_WEIGHT_WAIT_TIME = 10.0

# --- Task Priorities for the Greenhouse Scenario ---
TASK_PRIORITIES = {
    'MONITOR_WATER_LEVEL': 10,
    'MONITOR_NUTRIENT_LEVEL': 10,
    'CHECK_WATER_PH': 9,
    'READ_AMBIENT_TEMP_HUMIDITY': 5,
    'CAPTURE_TIMELAPSE_IMAGE': 1,
    'UNKNOWN_TASK': 1
}

# --- Global variable for our profiles ---
TASK_PROFILES = None 

class TaskScheduler:
    """The final hybrid scheduler with explainability logging."""
    def __init__(self, task_profiles, task_priorities):
        self.arduino_state = {'cpu_load': 0.0, 'mem_load': 0.0}
        self.task_profiles = task_profiles
        self.task_priorities = task_priorities

    def _calculate_cost(self, arduino_state, task_queue, return_components=False):
        if arduino_state['cpu_load'] > 100.0 or arduino_state['mem_load'] > TOTAL_SRAM:
            if return_components: return {'load': float('inf'), 'wait': float('inf'), 'total': float('inf')}
            return float('inf')
        load_cost = (COST_WEIGHT_CPU_LOAD * arduino_state['cpu_load']) + (COST_WEIGHT_MEM_LOAD * arduino_state['mem_load'])
        wait_cost = sum(task['priority'] * task['time_in_queue'] for task in task_queue)
        total_cost = load_cost + (COST_WEIGHT_WAIT_TIME * wait_cost)
        if return_components:
            return {'load': load_cost, 'wait': COST_WEIGHT_WAIT_TIME * wait_cost, 'total': total_cost}
        return total_cost

    def _find_best_simulated_move(self, sim_state, sim_queue):
        best_move, min_cost = None, float('inf')
        for task in sim_queue[:CHOICES_TO_SIMULATE]:
            temp_state = copy.deepcopy(sim_state)
            task_cost = self.task_profiles.get(task['name'], {})
            temp_state['cpu_load'] += task_cost.get('cpu_cost', 0)
            temp_state['mem_load'] += task_cost.get('mem_cost', 0)
            cost = self._calculate_cost(temp_state, sim_queue)
            if cost < min_cost:
                min_cost, best_move = cost, task
        return best_move if best_move is not None else (sim_queue[0] if sim_queue else None)

    def _simulate_rollout(self, current_arduino_state, current_task_queue, depth):
        if not current_task_queue or depth <= 0:
            return self._calculate_cost(current_arduino_state, current_task_queue)
        best_move = self._find_best_simulated_move(current_arduino_state, current_task_queue)
        if not best_move:
            return self._calculate_cost(current_arduino_state, current_task_queue)
        future_state = copy.deepcopy(current_arduino_state)
        task_cost = self.task_profiles.get(best_move['name'], {})
        future_state['cpu_load'] += task_cost.get('cpu_cost', 0)
        future_state['mem_load'] += task_cost.get('mem_cost', 0)
        if future_state['cpu_load'] > 100 or future_state['mem_load'] > TOTAL_SRAM:
            return float('inf')
        future_state['cpu_load'] *= (1 - 0.40)
        future_state['mem_load'] *= (1 - 0.40)
        future_queue = [t for t in current_task_queue if t != best_move]
        for task in future_queue: task['time_in_queue'] += 1
        return self._simulate_rollout(future_state, future_queue, depth - 1)

    def find_best_task_to_run(self, task_queue, is_verbose=False):
        DECAY_FACTOR = 0.40
        task_outcomes = []
        candidate_tasks = task_queue[:CHOICES_TO_SIMULATE]

        for i, candidate_task in enumerate(candidate_tasks):
            initial_sim_state = copy.deepcopy(self.arduino_state)
            task_cost = self.task_profiles.get(candidate_task['name'], {})
            initial_sim_state['cpu_load'] += task_cost.get('cpu_cost', 0)
            initial_sim_state['mem_load'] += task_cost.get('mem_cost', 0)
            initial_sim_state['cpu_load'] *= (1 - DECAY_FACTOR)
            initial_sim_state['mem_load'] *= (1 - DECAY_FACTOR)
            simulation_queue = copy.deepcopy(task_queue)
            simulation_queue.pop(i)
            for task in simulation_queue: task['time_in_queue'] += 1
            future_cost = self._simulate_rollout(initial_sim_state, simulation_queue, SIMULATION_DEPTH - 1)
            task_outcomes.append({'choice': candidate_task, 'cost': future_cost})
            if is_verbose:
                # <-- FIX #1: Corrected the print statement
                print(f"  - Simulating '{candidate_task['name']}'... leads to future cost: {future_cost:.2f}")

        valid_task_outcomes = [o for o in task_outcomes if o['cost'] != float('inf')]

        if not valid_task_outcomes:
            if is_verbose: print("  - EXPLAIN: All task paths predict overload. Activating crisis protocol.")
            if candidate_tasks:
                task_to_drop = min(candidate_tasks, key=lambda task: task['priority'])
                return ("DROP", task_to_drop)
            return None

        # --- HYBRID LOGIC ---
        EMERGENCY_PRIORITY_THRESHOLD = 9
        is_emergency = candidate_tasks and all(task['priority'] >= EMERGENCY_PRIORITY_THRESHOLD for task in candidate_tasks)

        best_task_outcome = min(valid_task_outcomes, key=lambda o: o['cost'])

        if is_emergency:
            if is_verbose: print("  - EXPLAIN: Emergency detected (all tasks are high-priority). Acting aggressively.")
            return best_task_outcome['choice']
        else:
            idle_sim_state = copy.deepcopy(self.arduino_state)
            idle_sim_state['cpu_load'] *= (1 - DECAY_FACTOR)
            idle_sim_state['mem_load'] *= (1 - DECAY_FACTOR)
            idle_sim_queue = copy.deepcopy(task_queue)
            for task in idle_sim_queue: task['time_in_queue'] += 1
            idle_cost_components = self._calculate_cost(idle_sim_state, idle_sim_queue, return_components=True)
            idle_future_cost = idle_cost_components['total']
            
            if is_verbose:
                print(f"  - Simulating 'IDLE'... leads to future cost: {idle_future_cost:.2f} (Load: {idle_cost_components['load']:.2f}, Wait: {idle_cost_components['wait']:.2f})")

            if idle_future_cost < best_task_outcome['cost']:
                if is_verbose: print(f"  - EXPLAIN: Cost to IDLE ({idle_future_cost:.2f}) is less than cost to act ({best_task_outcome['cost']:.2f}). Choosing patience.")
                return "IDLE"
            else:
                if is_verbose: print(f"  - EXPLAIN: Cost to act ({best_task_outcome['cost']:.2f}) is less than/equal to cost to IDLE. Taking action.")
                return best_task_outcome['choice']

    def execute_task(self, task_to_execute, task_queue):
        task_cost = self.task_profiles.get(task_to_execute['name'], {})
        self.arduino_state['cpu_load'] += task_cost.get('cpu_cost', 0)
        self.arduino_state['mem_load'] += task_cost.get('mem_cost', 0)
        self.arduino_state['cpu_load'] *= (1 - 0.40)
        self.arduino_state['mem_load'] *= (1 - 0.40)
        task_queue.remove(task_to_execute)
        for task in task_queue:
            task['time_in_queue'] += 1

# --- HELPER FUNCTIONS ---
def find_round_robin_task(task_queue):
    return task_queue[0] if task_queue else None

def find_strict_priority_task(task_queue):
    if not task_queue: return None
    return sorted(task_queue, key=lambda t: (t['priority'], t['time_in_queue']), reverse=True)[0]
    
def generate_random_task_queue(task_pool, length, priorities):
    task_names = random.choices(task_pool, k=length)
    return [{'name': name, 'priority': priorities.get(name, 1), 'time_in_queue': 0} for name in task_names]

def run_simulation(scheduler_type, task_queue_orig, profiles, priorities):
    task_queue = copy.deepcopy(task_queue_orig)
    scheduler = TaskScheduler(profiles, priorities)
    peak_cpu, peak_mem, overloads, tasks_dropped = 0, 0, 0, 0
    high_priority_waits = []
    DECAY_FACTOR = 0.40

    while task_queue:
        peak_cpu = max(peak_cpu, scheduler.arduino_state['cpu_load'])
        peak_mem = max(peak_mem, scheduler.arduino_state['mem_load'])

        if scheduler_type == "Intelligent":
            best_choice = scheduler.find_best_task_to_run(task_queue, is_verbose=False)
        elif scheduler_type == "Strict Priority":
            best_choice = find_strict_priority_task(task_queue)
        else: # Round Robin
            best_choice = find_round_robin_task(task_queue)
            
        if isinstance(best_choice, tuple) and best_choice[0] == "DROP":
            task_to_drop = best_choice[1]
            task_queue.remove(task_to_drop)
            tasks_dropped += 1
        elif best_choice == "IDLE":
            scheduler.arduino_state['cpu_load'] *= (1 - DECAY_FACTOR)
            scheduler.arduino_state['mem_load'] *= (1 - DECAY_FACTOR)
            for task in task_queue: task['time_in_queue'] += 1
        elif best_choice:
            if best_choice['priority'] >= 9:
                high_priority_waits.append(best_choice['time_in_queue'])
            scheduler.execute_task(best_choice, task_queue)
            if scheduler.arduino_state['cpu_load'] > 100:
                overloads += 1
        else:
            break
            
    avg_wait_high_prio = np.mean(high_priority_waits) if high_priority_waits else 0
    
    return {
        "Peak CPU": f"{peak_cpu:.2f}%",
        "Peak Memory": f"{peak_mem:.2f} bytes",
        "Overloads": overloads,
        "Tasks Dropped": tasks_dropped,
        "Avg Wait (Prio >= 9)": f"{avg_wait_high_prio:.2f} steps"
    }

def main():
    """Main function to run scenarios, compare schedulers, and show explainability."""
    global TASK_PROFILES
    TASK_PROFILES = {
        "MONITOR_WATER_LEVEL": {"cpu_cost": 8.5, "mem_cost": 120.0},
        "MONITOR_NUTRIENT_LEVEL": {"cpu_cost": 8.5, "mem_cost": 120.0},
        "READ_AMBIENT_TEMP_HUMIDITY": {"cpu_cost": 18.0, "mem_cost": 250.0},
        "CHECK_WATER_PH": {"cpu_cost": 35.0, "mem_cost": 310.0},
        "CAPTURE_TIMELAPSE_IMAGE": {"cpu_cost": 95.0, "mem_cost": 950.0}
    }
    full_sensor_pool = list(TASK_PROFILES.keys())
    scenarios = {
        "Scenario 1: Routine Day": {"pool": full_sensor_pool, "length": 20},
        "Scenario 2: Drought Alert": {"pool": ['MONITOR_WATER_LEVEL', 'CHECK_WATER_PH', 'MONITOR_NUTRIENT_LEVEL'], "length": 15},
        "Scenario 3: The Camera Trap": {"pool": ['READ_AMBIENT_TEMP_HUMIDITY', 'CAPTURE_TIMELAPSE_IMAGE'], "length": 10},
    }

    # --- PART 1: RUN THE COMPARISON (SILENTLY) ---
    for name, params in scenarios.items():
        print("\n" + "#"*100)
        print(f"### SCENARIO: {name.upper()} ###")
        print("#"*100)

        task_queue_for_comparison = generate_random_task_queue(params['pool'], params['length'], TASK_PRIORITIES)
        
        print("Analyzing performance of all three schedulers...")
        rr_results = run_simulation("Round Robin", task_queue_for_comparison, TASK_PROFILES, TASK_PRIORITIES)
        priority_results = run_simulation("Strict Priority", task_queue_for_comparison, TASK_PROFILES, TASK_PRIORITIES)
        intelligent_results = run_simulation("Intelligent", task_queue_for_comparison, TASK_PROFILES, TASK_PRIORITIES)

        print("\n" + "="*100)
        print(f"--- COMPARISON FOR: {name} ---")
        print(f"{'Metric':<25} | {'Round Robin (FCFS)':<25} | {'Strict Priority (Greedy)':<25} | {'Intelligent (Predictive)':<25}")
        print("-"*100)
        for key in rr_results:
            print(f"{key:<25} | {rr_results[key]:<25} | {priority_results[key]:<25} | {intelligent_results[key]:<25}")
        print("="*100)
    
    # --- PART 2: RUN THE EXPLAINABILITY LOG FOR THE MOST INTERESTING SCENARIO ---
    print("\n" + "#"*100)
    print("### EXPLAINABILITY DEMO: STEP-BY-STEP OF 'ROUTINE DAY' ###")
    print("#"*100)

    random.seed(42)
    task_queue_for_demo = generate_random_task_queue(
        scenarios["Scenario 1: Routine Day"]['pool'],
        scenarios["Scenario 1: Routine Day"]['length'],
        TASK_PRIORITIES
    )
    
    scheduler = TaskScheduler(TASK_PROFILES, TASK_PRIORITIES)
    step_counter = 0
    DECAY_FACTOR = 0.40

    while task_queue_for_demo:
        step_counter += 1
        print("\n" + "="*50)
        print(f"--- Step {step_counter} ---")
        print(f"Current State: CPU: {scheduler.arduino_state['cpu_load']:.2f}%, Mem: {scheduler.arduino_state['mem_load']:.2f} bytes")
        print("Tasks waiting (first 5):")
        for task in task_queue_for_demo[:5]:
            print(f"  - {task['name']} (P:{task['priority']}, W:{task['time_in_queue']})")
        print("-" * 20)
        
        best_choice = scheduler.find_best_task_to_run(task_queue_for_demo, is_verbose=True)
        
        if isinstance(best_choice, tuple) and best_choice[0] == "DROP":
            task_to_drop = best_choice[1]
            print(f"\n>>> Decision: LOAD SHEDDING. Dropping '{task_to_drop['name']}'.")
            task_queue_for_demo.remove(task_to_drop)
        elif best_choice == "IDLE":
            print("\n>>> Decision: IDLE.")
            scheduler.arduino_state['cpu_load'] *= (1 - DECAY_FACTOR)
            scheduler.arduino_state['mem_load'] *= (1 - DECAY_FACTOR)
            for task in task_queue_for_demo: task['time_in_queue'] += 1
        elif best_choice:
            print(f"\n>>> Decision: Executing '{best_choice['name']}'.")
            scheduler.execute_task(best_choice, task_queue_for_demo)
        else:
            break
        
    print("\n" + "="*50)
    print("EXPLAINABILITY DEMO FINISHED.")

if __name__ == "__main__":
    main()