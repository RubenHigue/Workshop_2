class Patient:
    def __init__(self,id,env,illness,service_times):
        self.id = id
        self.env = env
        self.illness = illness
        self.priority = 1 if illness == "dangereous" else 2
        self.service_times = service_times
        self.status = "arrived"
        self.total_time = 0

