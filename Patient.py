class Patient:
    def __init__(self,id,illness,service_times):
        self.id = id
        self.illness = illness
        self.priority = 1 if illness == "dangereous" else 2
        self.service_times = service_times
        self.status = "arrived"
        self.total_time = 0

