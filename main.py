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
def analyze_results(results):
    avg_queue_lengths = []
    blocking_rates = []
    recovery_busy_probabilities = []
    utilization_surgeries = []
    config_names = []

    # Recorrer los resultados de la simulación
    for config_name, config_results in results.items():
        avg_queue_length = np.mean([r["avg_preparation_queue"] for r in config_results])
        blocking_rate = np.mean([r["blocking_rate"] for r in config_results])
        recovery_busy_probability = np.mean([r["recovery_busy_probability"] for r in config_results])
        utilization_surgery = np.mean([r["utilization_surgery"] for r in config_results])

        avg_queue_lengths.append(avg_queue_length)
        blocking_rates.append(blocking_rate)
        recovery_busy_probabilities.append(recovery_busy_probability)
        utilization_surgeries.append(utilization_surgery)
        config_names.append(config_name)

    # Imprimir modelo de regresión para la longitud de la cola de preparación
    slope, intercept, r_value, p_value, std_err = linregress(range(len(avg_queue_lengths)), avg_queue_lengths)
    print("Regression model (Avg Queue Length):")
    print(f"Slope: {slope:.4f}, Intercept: {intercept:.4f}, R-squared: {r_value ** 2:.4f}")

    # Imprimir modelo de regresión para el blocking_rate
    slope, intercept, r_value, p_value, std_err = linregress(range(len(blocking_rates)), blocking_rates)
    print("Regression model (Blocking Rate):")
    print(f"Slope: {slope:.4f}, Intercept: {intercept:.4f}, R-squared: {r_value ** 2:.4f}")

    # Imprimir modelo de regresión para la probabilidad de ocupación de la sala de recuperación
    slope, intercept, r_value, p_value, std_err = linregress(range(len(recovery_busy_probabilities)), recovery_busy_probabilities)
    print("Regression model (Recovery Room Busy Probability):")
    print(f"Slope: {slope:.4f}, Intercept: {intercept:.4f}, R-squared: {r_value ** 2:.4f}")

    # Imprimir modelo de regresión para la utilización de la sala de operaciones
    slope, intercept, r_value, p_value, std_err = linregress(range(len(utilization_surgeries)), utilization_surgeries)
    print("Regression model (Surgery Room Utilization):")
    print(f"Slope: {slope:.4f}, Intercept: {intercept:.4f}, R-squared: {r_value ** 2:.4f}")

    # Retornar todas las métricas
    return {
        "avg_queue_lengths": avg_queue_lengths,
        "blocking_rates": blocking_rates,
        "recovery_busy_probabilities": recovery_busy_probabilities,
        "utilization_surgeries": utilization_surgeries,
        "config_names": config_names
    }



if __name__ == "__main__":
    # Ejecutar el experimento
    experiment_results = run_experiment()

    # Analizar los resultados obtenidos
    analysis_results = analyze_results(experiment_results)

    # Imprimir los resultados de cada configuración
    for config_name, avg_queue_length, blocking_rate, recovery_busy_prob, utilization_surgery in zip(
        analysis_results["config_names"],
        analysis_results["avg_queue_lengths"],
        analysis_results["blocking_rates"],
        analysis_results["recovery_busy_probabilities"],
        analysis_results["utilization_surgeries"]
    ):
        print(f"{config_name}:")
        print(f"  Avg Preparation Queue Length = {avg_queue_length:.2f}")
        print(f"  Blocking Rate = {blocking_rate:.2f}")
        print(f"  Recovery Room Busy Probability = {recovery_busy_prob:.2f}%")
        print(f"  Surgery Room Utilization = {utilization_surgery:.2f}%")
