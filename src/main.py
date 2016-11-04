from collections import defaultdict
import logging
import sys
from src.Process import Process
from src.Status import STATUS

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


class FeedbackQueue(list):
    def __init__(self, tq, new_list):
        super(FeedbackQueue, self).__init__(new_list)
        self._time_quantum = tq

    @property
    def time_quantum(self):
        return self._time_quantum


class CPU_Scheduler:
    def __repr__(self):
        return "Cpu_Scheduler()"

    def __str__(self):
        return "Cpu_Scheduler()"

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
        self.print_cs_stats(time)
        while work_to_do:
            if self.current_process is None:
                # No process is ready for CPU
                self.update_io_processes()

                # Check ready queue for any ready
                if self.ready_queue:
                    self.current_process = self.get_next_context()
                    self.print_cs_stats(time)

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
                        logging.debug("Process {} added to ready at t = {}".format(p.id, time))

            if self.current_process.status == STATUS.Terminated:
                # Finished one process
                logging.debug("Process {} finished at t = {}".format(self.current_process.id, time))
                self.current_process.exit_time = time
                work_to_do -= 1

            if self.current_process.status == STATUS.Waiting or self.current_process.status == STATUS.Terminated:
                # Switch context
                if self.ready_queue:
                    self.current_process = self.get_next_context()
                    #logging.debug("Switched to {} at t = {}".format(self.current_process.id, time))
                    self.print_cs_stats(time)

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

    def print_cs_stats(self, t):
        result = ""
        result += " /Context Switch TIME={}\n".format(t)
        result += "| Running process: P{}\n".format(self.current_process.id)
        queue_print = ""
        for i in self.ready_queue:
            proc = self.processes[i]
            queue_print += "[P{}, Burst: {}]".format(proc.id, proc.current_timer)
        result += "| Ready Queue: {}\n".format(queue_print)
        io_print = ""
        comp_print = ""
        for i in self.processes:
            proc = i
            if proc.status == STATUS.Waiting:
                io_print += "[P{}, Remain: {}]".format(proc.id, proc.current_timer)
            elif proc.status == STATUS.Terminated:
                comp_print += "[P{}]".format(proc.id)

        result += "| IO Status: {}\n".format(io_print)
        result += "| Processes completed: {}\n".format(comp_print)
        print(result)

    def analyze(self):
        avg_wait = 0.0
        avg_tr = 0.0
        avg_r = 0.0
        p_to_times_list = []
        for p in self.processes:
            avg_tr += p.turnaround_time
            avg_wait += p.waiting_time
            avg_r += p.response_time
            p_to_times_list.append({'id': p.id, 'wt': p.waiting_time, 'tt': p.turnaround_time, 'rt': p.response_time})
            #self.stats[p.id]['t'] = p.turnaround_time - p.waiting_time
            #print("P{} {} {} {}".format(p.id, p.waiting_time, p.response_time, p.turnaround_time))

        n = len(self.processes)
        print("{}: Ucpu: {}, WT: {}, TT: {}, RT: {}, T_total: {}".format(self, self.used_time / self.total_time, avg_wait / n, avg_tr / n, avg_r / n, self.total_time))
        for p in p_to_times_list:
            print(p)
        print("-----------------------------------------\n")

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
    def __repr__(self):
        return "FCFS()"

    def __str__(self):
        return "FCFS()"


class SJF(CPU_Scheduler):
    def __repr__(self):
        return "SJF()"

    def __str__(self):
        return "SJF()"

    def get_next_context(self):
        min_sf = 99999999
        index_to_pop = None

        for id in self.ready_queue:
            job_len = self.processes[id].current_timer
            if job_len < min_sf:
                min_sf = job_len
                index_to_pop = self.ready_queue.index(id)
        return self.processes[self.ready_queue.pop(index_to_pop)]


class ML_FQ(CPU_Scheduler):
    def __init__(self, list_process_times):
        CPU_Scheduler.__init__(self, list_process_times)
        self.ready_queue = FeedbackQueue(2, [])
        self.second_queue = FeedbackQueue(3, [])
        self.third_queue = []

    def __repr__(self):
        return "ML_FQ()"

    def __str__(self):
        return "ML_FQ()"

    def print_cs_stats(self, t):
        result = ""
        result += " /Context Switch TIME={}\n".format(t)
        result += "| Running process: P{}\n".format(self.current_process.id)
        queue_print = ""
        for i in self.ready_queue:
            proc = self.processes[i]
            queue_print += "[P{}, Burst: {}]".format(proc.id, proc.current_timer)
        result += "| RR Queue 1: {}\n".format(queue_print)

        for i in self.second_queue:
            proc = self.processes[i]
            queue_print += "[P{}, Burst: {}]".format(proc.id, proc.current_timer)
        result += "| RR Queue 2: {}\n".format(queue_print)

        for i in self.third_queue:
            proc = self.processes[i]
            queue_print += "[P{}, Burst: {}]".format(proc.id, proc.current_timer)
        result += "| FCFS Queue 3: {}\n".format(queue_print)

        io_print = ""
        comp_print = ""
        for i in self.processes:
            proc = i
            if proc.status == STATUS.Waiting:
                io_print += "[P{}, Remain: {}]".format(proc.id, proc.current_timer)
            elif proc.status == STATUS.Terminated:
                comp_print += "[P{}]".format(proc.id)

        result += "| IO Status: {}\n".format(io_print)
        result += "| Processes completed: {}\n".format(comp_print)
        print(result)


    def get_next_context(self):
        if self.ready_queue:
            return self.processes[self.ready_queue.pop(0)]
        elif self.second_queue:
            return self.processes[self.second_queue.pop(0)]
        elif self.third_queue:
            return self.processes[self.third_queue.pop(0)]
        else:
            return None

    def scan_next_context(self):
        if self.ready_queue:
            return self.processes[self.ready_queue[0]]
        elif self.second_queue:
            return self.processes[self.second_queue[0]]
        elif self.third_queue:
            return self.processes[self.third_queue[0]]
        else:
            return None

    def simulate(self):
        # All processes start at t = 0, we dump process list into ready queue as id's
        self.ready_queue = FeedbackQueue(2, [i.id for i in self.processes])

        self.current_process = self.get_next_context()
        work_to_do = len(self.processes)
        time = 0
        self.print_cs_stats(time)
        while work_to_do:
            if self.current_process is None:
                # No process is ready for CPU
                self.update_io_processes()

                # Check ready queue for any ready
                if self.ready_queue:
                    self.current_process = self.get_next_context()
                    self.print_cs_stats(time)

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
                    if p.id not in self.ready_queue and p.id not in self.second_queue and p.id not in self.third_queue:
                        # Newly finished processes go immediately to top queue
                        self.ready_queue.append(p.id)
                        p.priority = 2
                        logging.debug("Process {} added to queue 0 at t = {}".format(p.id, time))

            if self.current_process.status == STATUS.Terminated:
                # Finished one process
                logging.debug("Process {} finished at t = {}".format(self.current_process.id, time))
                self.current_process.exit_time = time
                work_to_do -= 1

            self.refresh_context(time)

        self.total_time = float(time)

    def refresh_context(self, time):
        if self.current_process.status == STATUS.Waiting or self.current_process.status == STATUS.Terminated:
            # Switch context
            self.current_process = self.get_next_context()
            if self.current_process is None:
                return
            #logging.debug("Switched to {} at t = {}".format(self.current_process.id, time))
            self.print_cs_stats(time)
        elif self.current_process.status == STATUS.Running:
            # Enforce time quauntum first

            if self.current_process.priority == 2:
                queue_tq = self.ready_queue.time_quantum
                parent_queue = self.ready_queue
                downgrade_queue = self.second_queue
            elif self.current_process == 1:
                queue_tq = self.second_queue.time_quantum
                parent_queue = self.second_queue
                downgrade_queue = self.third_queue
            else:
                queue_tq = None
                parent_queue = self.third_queue
                downgrade_queue = self.third_queue

            if queue_tq is not None and self.current_process.quantum == queue_tq:
                # Process has reached its allowed quantum, downgrade it, mark ready, and reset quantum.
                downgrade_queue.append(self.current_process.id)
                self.current_process.priority -= 1
                self.current_process.status = STATUS.Ready
                self.current_process.quantum = 0

                self.current_process = self.get_next_context()
                #logging.debug("Switched to {} at t = {}".format(self.current_process.id, time))
                self.print_cs_stats(time)

            else:
                # time-quantum not met (or process was lowest priority), but enforce preemptive nature
                new_proc = self.scan_next_context()
                if new_proc is None:
                    return
                if new_proc.priority > self.current_process.priority:
                    # A better process is found. Reset quauntum, mark, ready, and send back to parent queue
                    self.current_process.quantum = 0
                    self.current_process.status = STATUS.Ready
                    parent_queue.append(self.current_process.id)

                    self.current_process = self.get_next_context()
                    self.print_cs_stats(time)
                    #logging.debug("Switched to {} at t = {}".format(self.current_process.id, time))


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

    sjf = SJF(list_process_to_times)
    sjf.simulate()
    sjf.analyze()

    mlfq = ML_FQ(list_process_to_times)
    mlfq.simulate()
    mlfq.analyze()

if __name__ == '__main__':
    main()
