from src.Status import STATUS


class Process:
    def __init__(self, t_list, num):
        self.id = num
        # Reverse the list so we can pop for next timing
        self.timing_list = list(reversed(t_list))
        self.current_timer = self.timing_list.pop()
        # First time is always cpu
        self.status = STATUS.New
        self.waiting_time = 0
        self.turnaround_time = 0
        self.entrance_time = None
        self.response_time = 0
        # All processes arrive at t = 0
        self.arrival_time = 0
        self.exit_time = None
        # MLFQ variables
        self.quantum = 0
        self.priority = 2

    def update(self, has_cpu):
        self.turnaround_time += 1

        if has_cpu:
            self.status = STATUS.Running
            self.quantum += 1
        elif self.status == STATUS.New:
            self.response_time += 1

        if self.status == STATUS.Running or self.status == STATUS.Waiting:
            self.current_timer -= 1
        elif self.status == STATUS.Ready or self.status == STATUS.New:
            self.waiting_time += 1

        if self.current_timer == 0:
            if len(self.timing_list) == 0:
                self.status = STATUS.Terminated
                return

            if self.status == STATUS.Running:
                # print("waiting")
                self.status = STATUS.Waiting  # Go to IO

            elif self.status == STATUS.Waiting:
                self.status = STATUS.Ready
                #print("ready")

            self.current_timer = self.timing_list.pop()
            self.quantum = 0

