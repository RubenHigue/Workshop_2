from fractions import Fraction

from Patient import Patient
from Facility import Facility
import simpy
import random

ONE = 1
ZERO = 0
HALF = 0.5
HUNDRED = 100


class Hospital:
    def __init__(self, env, num_preparation_rooms, num_recovery_rooms):
        self.env = env
        self.preparationRooms = Facility(env, num_preparation_rooms, "Preparation Rooms")
        self.surgery = Facility(env, ONE, "Surgery Room")
        self.recoveryRooms = Facility(env, num_recovery_rooms, "Recovery Rooms")
        self.patients = []
        self.total_patients = 0
        self.blocked_surgeries = 0
        self.departed_patients = 0
        self.total_patient_time = 0
        self.num_surgeries = 0

        # Monitoring variables
        self.preparation_queue_lengths = []
        self.blocking_probabilities = []
        self.recovery_room_busy_probabilities = []

    # Patients lifetime cycle, main process for the patients.
    def patient_life_time(self, patient):
        arrival_time = self.env.now

        patient.status = "Preparing"
        print(f"{patient.id} is {patient.status}")
        with self.preparationRooms.resource.request(priority=patient.priority) as request:
            yield request
            self.preparation_queue_lengths.append(len(self.preparationRooms.resource.queue))
            yield self.env.timeout(patient.service_times["preparation"])

        patient.status = "Surgery"
        print(f"{patient.id} is in {patient.status}")
        with self.surgery.resource.request(priority=patient.priority) as request:
            if len(self.surgery.resource.queue) > ZERO:
                self.blocked_surgeries += ONE
            yield request
            yield self.env.timeout(patient.service_times["surgery"])
            self.num_surgeries += ONE

        patient.status = "Recovery"
        print(f"{patient.id} is in {patient.status}")
        with self.recoveryRooms.resource.request(priority=patient.priority) as request:
            yield request
            yield self.env.timeout(patient.service_times["recovery"])

        patient.status = "Departed"
        print(f"{patient.id} is {patient.status}")
        patient.total_time = self.env.now - arrival_time
        self.total_patient_time += patient.total_time
        self.departed_patients += ONE
        print(f"{patient.id} has been departed in {patient.total_time: .2f} seconds----")

    # Patient generator, responsible for generating patients.
    def patient_arrival(self, time_between_patients, service_times_ranges):
        while True:
            yield self.env.timeout(random.expovariate(ONE / time_between_patients))

            illness = random.choice(["normal", "dangereous"])

            service_times = {
                "preparation": random.uniform(*service_times_ranges["preparation"]),
                "surgery": random.uniform(*service_times_ranges["surgery"]),
                "recovery": random.uniform(*service_times_ranges["recovery"])
            }

            if illness == "normal":
                service_times["preparation"] = service_times["preparation"] * HALF
                service_times["surgery"] = service_times["surgery"] * HALF
                service_times["recovery"] = service_times["recovery"] * HALF

            patient = Patient(self.total_patients, self.env, illness, service_times)
            self.patients.append(patient)
            self.total_patients += ONE
            self.env.process(self.patient_life_time(patient))

    # Method that clears monitoring data after warm-up.
    def reset_monitoring(self):
        self.preparation_queue_lengths.clear()
        self.blocking_probabilities.clear()
        self.recovery_room_busy_probabilities.clear()

    # Monitors the system at regular intervals.
    def monitor_system(self, sampling_interval):
        while True:
            self.preparation_queue_lengths.append(len(self.preparationRooms.resource.queue))
            recovery_busy = len(self.recoveryRooms.resource.users) == self.recoveryRooms.resource.capacity
            self.recovery_room_busy_probabilities.append(ONE if recovery_busy else ZERO)
            yield self.env.timeout(sampling_interval)

    # Calculates results from the simulation.
    def get_results(self):
        avg_preparation_queue = sum(self.preparation_queue_lengths) / max(len(self.preparation_queue_lengths), ONE)
        blocking_rate = self.blocked_surgeries / max(self.num_surgeries, ONE)
        recovery_busy_probability = (sum(self.recovery_room_busy_probabilities) /
                                     max(len(self.recovery_room_busy_probabilities), ONE))

        return {
            "avg_preparation_queue": avg_preparation_queue,
            "blocking_rate": blocking_rate,
            "recovery_busy_probability": recovery_busy_probability,
            "utilization_surgery": (self.num_surgeries / self.total_patients)*HUNDRED
        }

    # Runs the hospital simulation.
    def run(self, runtime):
        self.env.process(self.monitor_system(ONE))
        self.env.run(until=runtime)
