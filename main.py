import random
import numpy as np
import simpy
from scipy.stats import t, linregress
from itertools import product
from Hospital import Hospital

# Configuration for the experiment
distributions = {
    "interarrival": {
        "exp_25": lambda: random.expovariate(1 / 25),
        "exp_22_5": lambda: random.expovariate(1 / 22.5),
        "unif_20_30": lambda: random.uniform(20, 30),
        "unif_20_25": lambda: random.uniform(20, 25)
    },
    "preparation": {
        "exp_40": lambda: random.expovariate(1 / 40),
        "unif_30_50": lambda: random.uniform(30, 50)
    },
    "recovery": {
        "exp_40": lambda: random.expovariate(1 / 40),
        "unif_30_50": lambda: random.uniform(30, 50)
    }
}

# Factor levels
factors = {
    "interarrival": ["exp_25", "unif_20_30"],
    "preparation": ["exp_40", "unif_30_50"],
    "recovery": ["exp_40", "unif_30_50"],
    "prep_units": [4, 5],
    "recovery_units": [4, 5]
}


# Experiment design (2^(6-3))
def fractional_factorial_design():
    full_factorial = list(product(*factors.values()))
    reduced_design = full_factorial[::8]  # Simplified fractional factorial
    return reduced_design


# Simulation parameters
RUNTIME = 1000
NUM_SAMPLES = 10
SEED = 33


# Analyze serial correlation
def analyze_serial_correlation(data, sample_interval):
    series = [data[i::sample_interval] for i in range(sample_interval)]
    correlations = []
    for s in series:
        if len(s) > 1:
            corr = np.corrcoef(s[:-1], s[1:])[0, 1]
            correlations.append(corr)
    return np.mean(correlations)


# Run a single simulation for a configuration
def run_simulation(config, seed):
    random.seed(seed)
    np.random.seed(seed)
    env = simpy.Environment()

    # Extract configuration details
    interarrival = distributions["interarrival"][config[0]]
    preparation = distributions["preparation"][config[1]]
    recovery = distributions["recovery"][config[2]]
    prep_units = config[3]
    recovery_units = config[4]

    # Create hospital instance
    hospital = Hospital(env, prep_units, recovery_units)

    # Start patient arrival process
    env.process(hospital.patient_arrival(interarrival, {
        "preparation": preparation,
        "surgery": lambda: random.expovariate(1 / 20),
        "recovery": recovery
    }))

    # Run simulation
    hospital.run(RUNTIME)

    # Get results
    return hospital.get_results()


# Run the experiment
def run_experiment():
    design = fractional_factorial_design()
    results = {}

    for i, config in enumerate(design):
        config_name = f"Config_{i + 1}"
        results[config_name] = []

        for sample in range(NUM_SAMPLES):
            seed = SEED + sample
            result = run_simulation(config, seed)
            results[config_name].append(result)

    return results


# Analyze results and build regression model
def calculate_regression_for_config(config_results, metric):
    avg_metric = np.mean([r[metric] for r in config_results])
    x_values = range(len(config_results))
    y_values = [r[metric] for r in config_results]

    slope, intercept, r_value, p_value, std_err = linregress(x_values, y_values)
    print(f"Regression model for {metric}:")
    print(f"Slope: {slope:.4f}, Intercept: {intercept:.4f}, R-squared: {r_value ** 2:.4f}")
    return avg_metric, slope, intercept, r_value ** 2, p_value, std_err


# Function to get the Global Regresion
def analyze_results(results):
    metrics = ['avg_preparation_queue', 'blocking_rate', 'recovery_busy_probability', 'utilization_surgery']

    for metric in metrics:
        print(f"\n\nPerforming regression for {metric}:")
        for config_name, config_results in results.items():
            print(f"\n{config_name}:")
            avg_metric, slope, intercept, r_squared, p_value, std_err = calculate_regression_for_config(config_results,
                                                                                                        metric)
            print(f"Avg {metric}: {avg_metric:.2f}")
            print(f"R-squared for {config_name} ({metric}): {r_squared:.4f}")
            print(f"P-value: {p_value:.4f}\n")

    print("\n\nGlobal regression:")
    for metric in metrics:
        avg_metric_values = []
        for config_name, config_results in results.items():
            avg_metric_values.append(np.mean([r[metric] for r in config_results]))

        slope, intercept, r_value, p_value, std_err = linregress(range(len(avg_metric_values)), avg_metric_values)
        print(f"\nGlobal regression for {metric}:")
        print(f"Slope: {slope:.4f}, Intercept: {intercept:.4f}, R-squared: {r_value ** 2:.4f}")
        print(f"P-value: {p_value:.4f}\n")


if __name__ == "__main__":
    experiment_results = run_experiment()
    analyze_results(experiment_results)
