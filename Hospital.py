from fractions import Fraction

from Patient import Patient
from Facility import Facility
import simpy
import random

ONE = 1
ZERO = 0
HALF = 0.5


class Hospital:
    def __init__(self, env, num_preparation_rooms, num_recovery_rooms):
        self.env = env
        self.preparationRooms = Facility(env, num_preparation_rooms, "Preparation Rooms")
        self.surgery = Facility(env, ONE, "Surgery Room")
        self.recovery = Facility(env, num_recovery_rooms, "Recovery Rooms")
        self.patients = []
        self.total_patients = 0
        self.blocked_surgeries = 0
        self.departed_patients = 0

    def patient_life_time(self, patient):
        arrival_time = self.env.now

        patient.status = "Preparing"
        with self.preparationRooms.resource.request(priority=patient.priority) as request:
            yield request
            yield self.env.timeout(patient.service_times["preparation"])

        patient.status = "Surgery"
        with self.surgery.resource.request(priority=patient.priority) as request:
            if len(self.surgery.resource.queue) > ZERO:
                self.blocked_surgeries += ONE
            yield request
            yield self.env.timeout(patient.service_times["surgery"])

        patient.status = "Recovery"
        with self.recovery.resource.request(priority=patient.priority) as request:
            yield request
            yield self.env.timeout(patient.service_times["recovery"])

        patient.status = "Departed"
        patient.total_time = self.env.now - arrival_time
        self.departed_patients += ONE

    def patient_arrival(self, time_between_patients, service_times_ranges):
        while True:
            yield self.env.timeout(random.expovariate(ONE/time_between_patients))

            illness = random.choice(["normal","dangereous"])

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