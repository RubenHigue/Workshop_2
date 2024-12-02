import random
import numpy as np
import simpy
from scipy.stats import t
from Hospital import Hospital

# Configuration
CONFIGS = {
    "3p4r": {"preparation_rooms": 3, "recovery_rooms": 4},
    "3p5r": {"preparation_rooms": 3, "recovery_rooms": 5},
    "4p5r": {"preparation_rooms": 4, "recovery_rooms": 5},
}
INTERARRIVAL_TIME = 25
SERVICE_TIME_RANGES = {
    "preparation": (30, 50),
    "surgery": (15, 30),
    "recovery": (30, 50)
}

WARM_UP_TIME = 100
RUNTIME = 1000
NUM_SAMPLES = 20
CONFIDENCE_LEVEL = 0.95
SEED = 33
ONE = 1
TWO = 2


# Calculate mean and confidence interval for a dataset.
def confidence_interval(data, confidence=CONFIDENCE_LEVEL):
    mean = np.mean(data)
    sem = np.std(data, ddof=ONE) / np.sqrt(len(data))
    margin = sem * t.ppf((ONE + confidence) / TWO, df=len(data) - ONE)
    return mean, margin


# Run a single simulation for a given configuration and seed.
def run_simulation(config, seed):
    random.seed(seed)
    env = simpy.Environment()
    hospital = Hospital(env, config["preparation_rooms"], config["recovery_rooms"])
    hospital.env.process(hospital.patient_arrival(INTERARRIVAL_TIME, SERVICE_TIME_RANGES))
    hospital.run(runtime=WARM_UP_TIME + RUNTIME)
    hospital_results=hospital.get_results()
    hospital.reset_monitoring()
    return hospital_results


# Compare two sets of results and return mean difference and margin of error.
def compare_pairwise(results1, results2):
    if len(results1) != len(results2):
        raise ValueError("The result lists must have the same length for comparison")

    differences = [r1 - r2 for r1, r2 in zip(results1, results2)]
    mean_diff = np.mean(differences)
    margin_of_error = 1.96 * np.std(differences) / np.sqrt(len(differences))
    return mean_diff, margin_of_error


# Run simulations for all configurations and store results

results = {config: [] for config in CONFIGS}
for config_name, config in CONFIGS.items():
    for sample in range(NUM_SAMPLES):
        seed = SEED + sample
        result = run_simulation(config, seed)
        results[config_name].append(result)

print("\nSimulation Results:")
for config_name, config_results in results.items():
    data = [result["avg_preparation_queue"] for result in config_results]
    mean, margin = confidence_interval(data)
    print(f"Configuration: {config_name}")
    print(f"Average Preparation queue mean = {mean:.2f}, CI = {mean:.2f} ± {margin:.2f}")
    data2 = [result["blocking_rate"] for result in config_results]
    mean2, margin2 = confidence_interval(data2)
    print(f"Average blocking rate mean = {mean2:.2f}, CI = {mean2:.2f} ± {margin2:.2f}")
    data3 = [result["recovery_busy_probability"] for result in config_results]
    mean3, margin3 = confidence_interval(data3)
    print(f"Average recovery busy probability mean = {mean3: .3f}%, CI = {mean3: .3f} ± {margin3: .3f}")
    data4 = [result["utilization_surgery"] for result in config_results]
    mean4, margin4 = confidence_interval(data4)
    print(f"Surgery utilization mean = {mean4:.2f}%, CI = {mean4:.2f} ± {margin4:.2f}")
    print("\n")

print("\nPairwise Comparisons:")
for config1, config2 in [("3p4r", "3p5r"), ("3p5r", "4p5r"), ("3p4r", "4p5r")]:
    results1 = [result["avg_preparation_queue"] for result in results[config1]]
    results2 = [result["avg_preparation_queue"] for result in results[config2]]
    results3 = [result["utilization_surgery"] for result in results[config1]]
    results4 = [result["utilization_surgery"] for result in results[config2]]

    ci = compare_pairwise(results1, results2)
    ci2 = compare_pairwise(results3, results4)
    print(f"{config1} vs {config2}")
    print(f"Average Preparation queue mean Diff = {ci[0]:.2f}, CI = {ci[0]:.2f} ± {ci[1]:.2f}")
    print(f"Surgery utilization mean Diff = {ci2[1]:.2f}, CI = {ci2[1]:.2f} ± {ci2[0]:.2f}")
    print("\n")



