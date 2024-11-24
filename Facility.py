import simpy


class Facility:
    def __init__(self, env, capacity, name):
        self.env = env
        self.resource = simpy.PriorityResource(env, capacity)
        self.name = name
        self.queue_size = []
        self.utilization = []

    # Method for monitoring the sizes of the priority queue and the utilization of the facilities.
    def monitor(self):
        while True:
            self.queue_size.append(len(self.resource.queue))
            self.utilization.append(len(self.resource.users) / self.resource.capacity)
            yield self.env.timeout(1)
