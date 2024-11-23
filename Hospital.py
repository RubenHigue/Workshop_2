from fractions import Fraction

from Patient import Patient
from Facility import Facility
import simpy
import random

ONE = 1
ZERO = 0


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


