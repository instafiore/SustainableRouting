import os
from utils.utility import *
import re
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List
from venv import logger
from xml.dom import minidom

import sumolib
import traci

import common.constants as constants
from common.CloudLogger import CloudLogger
from common.Logger import Logger
from traffic.CityNetwork import CityNetwork
from traffic.SimplifiedCityNetwork import SimplifiedCityNetwork
from traffic.Simulation import Simulation
from traffic.SimulationState import SimulationState
from traffic.Solution import Solution
from traffic.Vehicle import Vehicle
from preprocessors.PreProcessor import *
from traffic.Street import *




class ComputeMostCongestedEdges(PreProcessor):

    def __init__(self, networkFile, sumocfgFile, hasGUI: bool, logger: Logger, args, exp=False):
        super().__init__(networkFile, sumocfgFile, hasGUI, logger, PreProcessorType.ComputeMostCongestedEdges.value, args, exp)

    def __getVehicles(self):
        # return set(traci.simulation.getLoadedIDList() + traci.vehicle.getIDList())
        return [Vehicle(self.simulation, vehicleId, False, self._vehiclesId2RouteXml[vehicleId], traci=False) for vehicleId in self._vehiclesId2RouteXml]

    def solve(self, fromFile=None):

        routeOcc: Dict[Street, int] = dict()
        routeOccPer: Dict[Street, float] = dict()

        vehicles = self.__getVehicles()

        streets = []       

        for v in vehicles:
            for s in v.getOriginalRoute():
                if s not in streets:
                    streets.append(s)
                routeOcc.setdefault(s, 0)
                routeOcc[s] += 1
        
        maxVehPassing = max(routeOcc.values())
        
        for s in streets:
            numVehPassing = routeOcc[s]
            pVehPassing = numVehPassing / maxVehPassing
            routeOccPer[s] = pVehPassing
        
        return [s for s in routeOcc.keys() if routeOccPer[s] >= 0.2]




            
        
