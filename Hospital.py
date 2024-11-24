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

    def patient_life_time(self, patient):
        arrival_time = self.env.now

        patient.status = "Preparing"
        print(f"{patient.id} is {patient.status}")
        with self.preparationRooms.resource.request(priority=patient.priority) as request:
            yield request
            yield self.env.timeout(patient.service_times["preparation"])

        patient.status = "Surgery"
        print(f"{patient.id} is {patient.status}")
        with self.surgery.resource.request(priority=patient.priority) as request:
            if len(self.surgery.resource.queue) > ZERO:
                self.blocked_surgeries += ONE
            yield request
            yield self.env.timeout(patient.service_times["surgery"])
            self.num_surgeries += ONE

        patient.status = "Recovery"
        print(f"{patient.id} is {patient.status}")
        with self.recoveryRooms.resource.request(priority=patient.priority) as request:
            yield request
            yield self.env.timeout(patient.service_times["recovery"])

        patient.status = "Departed"
        print(f"{patient.id} is {patient.status}")
        patient.total_time = self.env.now - arrival_time
        self.total_patient_time += patient.total_time
        self.departed_patients += ONE
        print(f"{patient.id} has been departed in {patient.total_time} seconds")

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

    def monitor_resources(self):
        self.env.process(self.preparationRooms.monitor())
        self.env.process(self.preparationRooms.monitor())
        self.env.process(self.recoveryRooms.monitor())

    def run(self, runtime):
        self.monitor_resources()
        self.env.run(runtime)

    def results(self):
        print("SIMULATION RESULTS")
        print(f"Total patients cured: {self.departed_patients}")
        print(f"Average time for patient to depart the hospital cured: {self.total_patient_time / self.departed_patients:.2f} seconds")
        print(f"Total time of the operation theatre blocked: {self.blocked_surgeries}")

        def avg(list):
            return sum(list) / len(list) if list else ZERO

        print(f"Average queue length:")
        print(f" Preparation: {avg(self.preparationRooms.queue_size):.2f}")
        print(f" Recovery: {avg(self.recoveryRooms.queue_size):.2f}")
        print(f"Average utilization:")
        print(f" Preparation: {avg(self.preparationRooms.utilization) * HUNDRED:.2f}%")
        print(f" Surgery: {self.num_surgeries/self.total_patients * HUNDRED: .2f}%")
        print(f" Recovery: {avg(self.recoveryRooms.utilization) * HUNDRED:.2f}%")
