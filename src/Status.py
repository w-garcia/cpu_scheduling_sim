from enum import Enum


class STATUS(Enum):
    New = 0
    Ready = 1
    Running = 2
    Waiting = 3
    Terminated = 4
