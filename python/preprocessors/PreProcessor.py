import os

from utils.utility import *
import re
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Set
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
# from preprocessors.ComputeMostCongestEdges import ComputeMostCongestedEdges
from traffic.Street import Street

def bitset(bitset_bin: str):
    bitset_bin = bitset_bin[::-1]
    n = len(bitset_bin)
    return sum([(2**i) * int(bitset_bin[i]) for i in range(n)])


class PreProcessorType(Enum):
    ASP = "asp"
    DIJKSTRA = "dijkstra"
    CUMULATIVE = "cumulative"
    DENSITY = "density"
    RANDOM = "random"
    PLAIN = "plain"
    ComputeMostCongestedEdges = "ComputeMostCongestedRoutes"


class PreProcessor:

    def __init__(self, networkFile, sumocfgFile, hasGUI: bool, logger: Logger, name: str, args, exp=False):
        
        self.exp = exp
        self.__sumoCmd = [constants.SUMO_HOME, "-c", sumocfgFile, "--start", "--no-warnings"]
        self.__name = name
        self.logger: Logger = logger

        self.controlledVehicles = 0 
        self.noAnswerVehicles = 0 
        self.orginalRouteVehicles = 0
        self.probabilityControlVehicle = args.probabilityControlVehicle if args and args.probabilityControlVehicle else 1.0
        self.processedVehicles = 0
        self.args = args
        self.isV2 = re.search(r"v2",self.args.rules)
        self.watchedThreshold = self.args.watchedStreets

        print(networkFile)
        net = sumolib.net.readNet(networkFile)
        self.start()
      

        apiVersion, sumoVersionString = traci.getVersion()

        messageapiVersion = f"TraCI API Version: {apiVersion}"
        messagesumoVersionString = f"SUMO Version String: {sumoVersionString}"
        print(messageapiVersion)
        self.logger.log(messageapiVersion)
        print(messagesumoVersionString)
        self.logger.log(messagesumoVersionString)
        self.START_TO_ROUTE = 3000

        self.__completeNetwork = CityNetwork(net, self.isV2)
        self.__network = SimplifiedCityNetwork(net, self.isV2)
        self.simulation = Simulation(self.__network, args)
        self.__HORIZON = args.HORIZON
        self.dir = "/".join(sumocfgFile.split("/")[0:-1] + ["solutions", self.__name]) if exp else None
        os.makedirs(self.dir, exist_ok=True) if exp else None
        # self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        self.experimentRadix = f"{self.dir}/{self.logger.timestamp}"
        self.__xmlPath = f"{self.experimentRadix}-unfinished.rou.xml"
        self.__vehiclesTeleported = set()
        self._vehiclesId2RouteXml = dict()

        self.statsTraffic = {}

        routeFiles = minidom.parse(sumocfgFile) \
            .getElementsByTagName('input')[0] \
            .getElementsByTagName('route-files')[0] \
            .getAttribute("value") \
            .split(",")

        self.__vehicleDepartTimes: Dict[str, int] = dict()
        self.__departTimesVehicles: Dict[int, List[str]] = dict()

        for f in routeFiles:
            path = "/".join(sumocfgFile.split("/")[0:-1] + [f])
            vehicles = minidom.parse(path).getElementsByTagName("routes")[0].getElementsByTagName("vehicle")
            for v in vehicles:
                id = v.getAttribute("id")
                routeVeh = v.getElementsByTagName("route")[0]
                edgesVeh = routeVeh.getAttribute("edges").split(" ")
                self._vehiclesId2RouteXml[id] = edgesVeh
                depart = int(float(v.getAttribute("depart")))
                self.__vehicleDepartTimes[id] = depart
                self.__departTimesVehicles[depart] = self.__departTimesVehicles.get(depart, [])
                self.__departTimesVehicles[depart].append(id)
        pass

    def getMostImportantRoutes(self):
        vehicles =  [Vehicle(self.simulation, vehicleId, False, self._vehiclesId2RouteXml[vehicleId], useTraci=False) for vehicleId in self._vehiclesId2RouteXml]

        routeOcc: Dict[Street, int] = dict()
        routeOccPer: Dict[Street, float] = dict()

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
        
        return [s for s in routeOcc.keys() if routeOccPer[s] >= self.watchedThreshold]

    def updateDepartTime(self, vehicle: Vehicle, depart):
        self.__vehicleDepartTimes[vehicle.id] = depart

    def onTick(self, step: int, vehicleInside: [Vehicle], newVehicles: [Vehicle], previousSolution: Solution) -> (Dict[str, List[str]], Solution):
        raise NotImplementedError()

    def __getVehicles(self):
        # return set(traci.simulation.getLoadedIDList() + traci.vehicle.getIDList())
        return set(traci.vehicle.getIDList())

    def start(self):
        self.logger.log(f"Starting {self.__name} with command: {' '.join(self.__sumoCmd)}")
        traci.start(self.__sumoCmd)
        self.step = 0

    def solve(self, fromFile=None):

        vehiclesMap = dict()
        vehiclesInside = set()

        self.step = 0
        previousSolution: Solution or None = None

        solutionRoutes = dict()

        xmlStr = ""
        emissions = 0

        self.watchedStreets = set(self.getMostImportantRoutes())

        capacityStreetsWatched = 0
        for s in self.watchedStreets:
            capacityStreetsWatched += s.capacity

        capacityStreets = 0
        for k, s in self.__network.streets.items():
            capacityStreets += s.capacity

        self.logger.log(f"Capacity Streets: {capacityStreets}")
        self.logger.log(f"Watched Capacity Streets: {capacityStreetsWatched} for {len(self.watchedStreets)} streets")

        while (not self.__HORIZON or self.step <= self.__HORIZON):

            traci.simulationStep(self.step)

            traciVehicles = self.__getVehicles()
            lenTraciVehicles = len(traciVehicles)

            if self.step > 100 and lenTraciVehicles == 0:
                break
            
        
            keysStatsTraffic = ["TimeLoss", "DepartDelay", "AccumulatedWaitingTime"]
            for k in keysStatsTraffic:
                self.statsTraffic[k] = 0
            for vehicleId in traciVehicles:
                vehiclesMap[vehicleId] = Vehicle(self.simulation, vehicleId) if vehicleId not in vehiclesMap else vehiclesMap[vehicleId]
                self.statsTraffic["TimeLoss"] += traci.vehicle.getTimeLoss(vehID=vehicleId)
                self.statsTraffic["DepartDelay"] += traci.vehicle.getDepartDelay(vehID=vehicleId)
                self.statsTraffic["AccumulatedWaitingTime"] += traci.vehicle.getAccumulatedWaitingTime(vehID=vehicleId)

            
            self.statsTraffic["#Vehicles"] = lenTraciVehicles
            if lenTraciVehicles > 0:
                for k in keysStatsTraffic: 
                    self.statsTraffic[k] = round(self.statsTraffic[k]/lenTraciVehicles, 4)
            
            self.statsTraffic["Occupancy"] = self.statsTraffic["#Vehicles"] / capacityStreets

            vehicles = set([vehiclesMap[vehicleId] for vehicleId in traciVehicles])
            newVehicles = vehicles.difference(vehiclesInside)



            teleported = set([vehiclesMap[vehicleId] for vehicleId in traci.simulation.getStartingTeleportIDList()])
            self.__vehiclesTeleported = self.__vehiclesTeleported.union(teleported)

            vehiclesNotOnMap = vehiclesInside - vehicles
            vehiclesOutside = set()
            vehiclesInside: Set[Vehicle] = vehiclesInside - vehiclesNotOnMap

            vehiclesInMapMap = dict([(vId, True) for vId in traci.vehicle.getIDList()])
            for vehicle in newVehicles:
                if traci.vehicle.getRouteIndex(vehicle.id) != 0:
                    vehiclesOutside.add(vehicle)
                else:
                    vehicle.setDepartTime(self.step)
                    if self.isV2: self.updateDepartTime(vehicle, self.step)

            self.statsTraffic["OccupancyWatched"] = 0
            for v in vehiclesInside:
                v.updateVehiclePosition()
                if v.route.isEmpty() or v.id not in vehiclesInMapMap:
                    vehiclesOutside.add(v)
                else:
                    s = v.route.getFirstStreet()
                    if s in self.watchedStreets:
                        self.statsTraffic["OccupancyWatched"] += 1
            self.statsTraffic["OccupancyWatched"] /= capacityStreetsWatched

            vehiclesInside = vehiclesInside - vehiclesOutside - self.__vehiclesTeleported
            newVehicles = newVehicles - vehiclesOutside - self.__vehiclesTeleported

            if not vehiclesInside and not newVehicles:
                exit()

            self.logger.log(
                f"- Step {self.step} - #Vehicles: {len(vehicles)} = {len(newVehicles)} new + {len(vehiclesInside)} inside = {len(newVehicles) + len(vehiclesInside)}. {len(vehiclesOutside)} left. {len(self.__vehiclesTeleported)} teleported - orginalRoute: {self.orginalRouteVehicles} - NoAnswer: {self.noAnswerVehicles} - Controlled: {self.controlledVehicles} Processed: {self.processedVehicles} Percentage: {self.controlledVehicles/self.processedVehicles if self.processedVehicles>0 else 0:.2f}")
            if newVehicles:
                solution = self.onTick(self.step, vehiclesInside, newVehicles, previousSolution)
                solutionRoutes.update(dict([(v, v.route.getEdgesList()) for v in newVehicles]))
                previousSolution = solution

            if previousSolution:
                routeXml = SimulationState(solutionRoutes, self.__vehicleDepartTimes)
                xmlStr = routeXml.getXMLString()
                self.logger.cleanDirectory("solutions", deleteDir=False)
                self.logger.uploadFile(f"solutions/{format(self.step, '04d')}.xml", xmlStr)


            for v in self.__getVehicles():
                emissions += traci.vehicle.getCO2Emission(v) * 10**(-6)

            self.logger.log(f"Emissions: {emissions} Kg")
            
            vehiclesInside = vehicles
            self.step += constants.TRACI_STEP

        traci.close()
        self.logger.log(f"Final emissions: {emissions} Kg")
        self.logger.log(f"orginalRoute: {self.orginalRouteVehicles} NoAnswer: {self.noAnswerVehicles} - Controlled: {self.controlledVehicles} - Processed: {self.processedVehicles} Percentage: {self.controlledVehicles/self.processedVehicles if self.processedVehicles>0 else 0:.2f}")

        
        if xmlStr != "" and self.exp:
            with open(f"{self.experimentRadix}/solution.xml", "w") as f:
                f.write(xmlStr)
            self.logger.cleanDirectory("solutions")
            self.logger.cleanDirectory("encodings")
            self.logger.cleanDirectory("checkpoints")
            
        
