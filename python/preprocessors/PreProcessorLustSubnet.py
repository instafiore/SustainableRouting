import os
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


class PreProcessorLustSubnet:

    def __init__(self, networkFile, sumocfgFile, logger: Logger, name: str, args, exp=False):
        
        self.exp = exp
        self.__sumoCmd = [constants.SUMO_HOME, "-c", sumocfgFile, "--start", "--no-warnings"]
        self.__name = name
        self.logger: Logger = logger


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

        # self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")

        self.vehiclesXML = minidom.parse(args.routesFile) \
            .getElementsByTagName('vehicle')


    def __getVehicles(self):
        # return set(traci.simulation.getLoadedIDList() + traci.vehicle.getIDList())
        return set(traci.vehicle.getIDList())

    def start(self):
        self.logger.log(f"Starting {self.__name} with command: {' '.join(self.__sumoCmd)}")
        traci.start(self.__sumoCmd)

    def createSubnetRoutes(self):
        
        subvehicles = []
        count = 0
        for v in self.vehiclesXML:
            
            id = v.getAttribute("id")
          
            route = v.getElementsByTagName("route")[0]
            v_edges = route.getAttribute("edges").split()

            max_subroute = []
            current_subroute = []
            edges = traci.edge.getIDList()

            for i in range(len(v_edges)):
                

                if v_edges[i] in edges:
                    current_subroute.append(v_edges[i])
            
                if  len(current_subroute) > 0 and (i == len(v_edges)-1 or v_edges[i] not in edges) :    
                    if len(current_subroute) > len(max_subroute):
                        max_subroute = current_subroute
                    current_subroute = []

            
            if len(max_subroute) <= 15:
                continue

            # print(f"Vehicle {v.getAttribute('id')} with route length {len(v_edges)}")
            v.setAttribute("type", "TD")
            route.setAttribute("edges", " ".join(max_subroute))

            assert all(edge in edges for edge in max_subroute)

            subvehicles.append(v)
            count += 1
            # if count >= 10:
            #     break
            
                    
        print(f"Original number of vehicles: {len(self.vehiclesXML)}")
        print(f"Number of vehicles in the subnet: {len(subvehicles)}")


        traci.close()

        document = minidom.Document()

        routesXML = document.createElement("routes")

        # xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd"
        routesXML.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        routesXML.setAttribute("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/routes_file.xsd")

    
        for v in subvehicles:
            routesXML.appendChild(v)

        document.appendChild(routesXML)

        return document.toxml()
 
