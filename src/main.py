from collections import defaultdict
from enum import Enum


class STATUS(Enum):
    New = 0
    Ready = 1
    Running = 2
    Waiting = 3
    Terminated = 4


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

    def update(self, has_cpu):
        self.turnaround_time += 1

        if has_cpu:
            self.status = STATUS.Running
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


class CPU_Scheduler:
    def __init__(self, list_process_times):
        self.processes = []
        count = 0
        for l in list_process_times:
            temp = Process(l, count)
            self.processes.append(temp)
            count += 1

        self.current_process = None
        self.ready_queue = []
        self.total_time = 0.0
        self.used_time = 0.0
        self.stats = defaultdict(dict)

    def simulate(self):
        # All processes start at t = 0, we dump process list into ready queue as id's
        self.ready_queue = [i.id for i in self.processes]

        self.current_process = self.get_next_context()
        work_to_do = len(self.processes)
        time = 0
        while work_to_do:
            if self.current_process is None:
                # No process is ready for CPU
                self.update_io_processes()

                # Check ready queue for any ready
                if self.ready_queue:
                    self.current_process = self.get_next_context()

                time += 1
                continue

            # Process is ready for CPU
            if self.current_process.entrance_time is None:
                self.current_process.entrance_time = time

            self.update_all_processes()

            time += 1
            self.used_time += 1

            for p in self.processes:
                if p.status == STATUS.Ready:
                    if p.id not in self.ready_queue:
                        self.ready_queue.append(p.id)
                        print("Process {} added to ready at t = {}".format(p.id, time))

            if self.current_process.status == STATUS.Terminated:
                # Finished one process
                print("Process {} finished at t = {}".format(self.current_process.id, time))
                self.current_process.exit_time = time
                work_to_do -= 1

            if self.current_process.status == STATUS.Waiting or self.current_process.status == STATUS.Terminated:
                # Switch context
                if self.ready_queue:
                    self.current_process = self.get_next_context()
                    print("Switched to {} at t = {}".format(self.current_process.id, time))
                else:
                    self.current_process = None

        self.total_time = float(time)

    def get_next_context(self):
        """
        Override this to change cpu scheduler
        Returns
        -------

        """
        return self.processes[self.ready_queue.pop(0)]

    def analyze(self):
        avg_wait = 0.0
        avg_tr = 0.0
        avg_r = 0.0
        for p in self.processes:
            avg_tr += p.turnaround_time
            avg_wait += p.waiting_time
            avg_r += p.response_time
            #self.stats[p.id]['t'] = p.turnaround_time - p.waiting_time
            #print("P{} {} {} {}".format(p.id, p.waiting_time, p.response_time, p.turnaround_time))

        n = len(self.processes)
        print("Ucpu: {}, WT: {}, TT: {}, RT: {}".format(self.used_time / self.total_time, avg_wait / n, avg_tr / n, avg_r / n))

    def update_all_processes(self):
        self.current_process.update(True)
        for p in self.processes:
            if p.status == STATUS.Terminated:
                continue
            if p.id != self.current_process.id:
                p.update(False)

    def update_io_processes(self):
        for p in self.processes:
            if p.status == STATUS.Terminated:
                continue

            p.update(False)
            if p.status == STATUS.Ready:
                self.ready_queue.append(p.id)


class FCFS(CPU_Scheduler):
    pass


def main():
    list_process_to_times = [[4,24,5,73,3,31,5,27,4,33,6,43,4,64,5,19,2],
                             [18,31,19,35,11,42,18,43,19,47,18,43,17,51,19,32,10],
                             [6,18,4,21,7,19,4,16,5,29,7,21,8,22,6,24,5],
                             [17,42,19,55,20,54,17,52,15,67,12,72,15,66,14],
                             [5,81,4,82,5,71,3,61,5,62,4,51,3,77,4,61,3,42,5],
                             [10,35,12,41,14,33,11,32,15,41,13,29,11],
                             [21,51,23,53,24,61,22,31,21,43,20],
                             [11,52,14,42,15,31,17,21,16,43,12,31,13,32,15]]

    fcfs = FCFS(list_process_to_times)
    fcfs.simulate()
    fcfs.analyze()

if __name__ == '__main__':
    main()
