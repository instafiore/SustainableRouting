
from typing import Dict
import sys

class Stat:

    def __init__(self):
        self.sum = 0
        self.min = sys.maxsize
        self.max = 0
        self.count = 0 

    def __add__(self, value: float):
        self.sum += value
        if value < self.min: self.min = value
        if value > self.max: self.max = value
        self.count += 1

    def __str__(self):
        out = {
            "min": self.min,
            "max": self.max,
            "sum": self.sum,
            "count": self.count,
            "avg": round(self.sum / self.count,4) if self.count > 0 else 0,
        }
        return str(out)
    
    def __repr__(self):
        return str(self)


class Stats:

    def __init__(self):
        self.stats : Dict[Stat]  =  dict()
    

    def addValue(self, name: str, value: float):
        self.stats.setdefault(name, Stat())
        s = self.stats[name]
        s += value

    def __str__(self):
        return str(self.stats)

