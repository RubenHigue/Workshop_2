import random
from Hospital import Hospital
import simpy

NUM_PREPARATION_ROOMS = 3
NUM_RECOVERY_ROOMS = 3
TIME_INTERARRIVAL = 25

random.seed(33)
env = simpy.Environment()
service_time_ranges = {
    "preparation": (30, 50),
    "surgery": (15, 30),
    "recovery": (30, 50)
}
runtime = 300

hospital = Hospital(env, NUM_PREPARATION_ROOMS, NUM_RECOVERY_ROOMS)
hospital.env.process(hospital.patient_arrival(TIME_INTERARRIVAL, service_time_ranges))
hospital.run(runtime)
hospital.results()

