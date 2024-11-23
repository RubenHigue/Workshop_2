from fractions import Fraction

from Patient import Patient
from Facility import Facility
import simpy
import random

ONE = 1


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
