import os
import random
import re
from datetime import time
from typing import Dict, Set, Tuple

import traci

from common.Arguments import Arguments
from common.CloudLogger import CloudLogger
from emissions.EdgeEmissionSimulator import EdgeEmissionSimulator
from preprocessors.PreProcessor import PreProcessor
from traffic.CheckPoint import CheckPoint
from traffic.Problem import Problem, ProblemType
from traffic.Route import Route
from traffic.SimulationStats import SimulationStats
from traffic.Solution import Solution
from traffic.Vehicle import Vehicle
from common.constants import *

IMPROVE = False
ONE_VEHICLE_AT_TIME = True
print(f"SEED RESETTING")
random.seed(42)
import time


def startTimer():
    return time.time()

def elapsedTime(start):
    return time.time() - start

class ASPPreProcessor(PreProcessor):

    def __init__(self, networkFile, sumocfgFile, hasGUI, logger: CloudLogger, args: Arguments, checkPointFile=None, emissionRisk: Dict[Tuple[str], float]=dict(), exp=False):
        version = "v2" if emissionRisk else "v1"
        print(f"ASP PreProcessor version: {version}")
        super(ASPPreProcessor, self).__init__(networkFile, sumocfgFile, hasGUI, logger, "asp-" + version, args, exp=exp)
        self.checkpointStepsFolder = self.experimentRadix + "/"
        self.emissionRisk: Dict[Tuple[str], float] = emissionRisk
        os.makedirs(self.checkpointStepsFolder, exist_ok=True) if exp else None
        self.inputCheckpointFile = checkPointFile
        self.inputCheckpoint = None
        self.allVehicles: [Vehicle] = set()
        self.stats: SimulationStats = SimulationStats()

        # for dirEntry in  os.scandir("asp"):
        #     if dirEntry.is_file():
        #         os.remove(dirEntry.path)

        with open(f"asp/rules/{self.args.rules}.lp", "r") as f:
            self.rules = [l for l in f.read().split("\n") if l.strip() != ""]
        # print(f"rules: {self.rules}")
        if checkPointFile:
            self.inputCheckpoint: CheckPoint = CheckPoint.fromFile(self.inputCheckpointFile, self.simulation.network)
            self.stats: SimulationStats = self.inputCheckpoint.stats

        pass

    def __writeEncoding(self, problem: Problem, name: str):
        filename = f"asp/last_{self.args.run_name}.lp"
        asp = problem.getASPCode()
        with open(filename, "w") as f:
            f.write(asp)
        # self.logger.uploadFile(f"encodings/{name}.lp", asp)

    def __updateRoutes(self, vehicles: Set[Vehicle], routesMap: Dict[str, Route]):
        for vehicle in vehicles:
            if vehicle.id not in routesMap:
                self.logger.error(f"ERROR: Vehicle {vehicle.id} was not on checkpoint")
                continue
            route: Route = routesMap[vehicle.id]
            edges = route.getEdgesList()
            # if "189[1][1]" in edges:
            #     assert False
            traci.vehicle.setRoute(vehicle.id, edges)
            vehicle.setRoute(route)

    def findSolution(self, step: int, j: int, vehiclesInside: Set[Vehicle], newVehicles: Set[Vehicle],
                     previousSolution: Solution):

        newVehiclesStr = "-".join([str(v) for v in newVehicles])
        stepStr = format(step, '04d') + "-" + format(j, '02d')
        solutionOpt: Solution or bool = False
        if IMPROVE:
            problemOpt = Problem(self.simulation, vehiclesInside, newVehicles, previousSolution,
                                problemType=ProblemType.COMPUTE_OPTIMUM, emissionRisk=self.emissionRisk, logger=self.logger, step=step,
                                args=self.args)
            self.__writeEncoding(problemOpt, f"{stepStr}-{newVehiclesStr}-{ProblemType.COMPUTE_OPTIMUM.value}")
            solutionOpt = problemOpt.solve(self.rules, self.logger)

        problemBest = Problem(self.simulation, vehiclesInside, newVehicles, previousSolution,
                              problemType=ProblemType.FIND_BEST, emissionRisk=self.emissionRisk, logger=self.logger, step=step, args=self.args)
        self.__writeEncoding(problemBest, f"{stepStr}-{newVehiclesStr}-{ProblemType.FIND_BEST.value}", )
        solutionBest: Solution = problemBest.solve(self.rules, self.logger)
        if not solutionBest.hasAnswer and not solutionBest.isArtificial:
            self.logger.error(f"WARNING: Could't find a solution at step {stepStr} for {newVehicles}")
            solutionBest = Solution(None, )

        if solutionOpt and solutionOpt.hasAnswer:
            answerStat = solutionOpt.getAnswer().getStats()
            answerStat.setNOfVehicles(len(vehiclesInside) + 1)
            self.stats.addStats(step, ProblemType.COMPUTE_OPTIMUM, answerStat, j)

        if solutionBest and solutionBest.hasAnswer:
            answerStat = solutionBest.getAnswer().getStats()
            answerStat.setNOfVehicles(len(vehiclesInside) + 1)
            self.stats.addStats(step, ProblemType.FIND_BEST, answerStat, j)

        solution = solutionBest if not solutionOpt or (
                solutionBest.hasAnswer and solutionBest.getOptimum() < solutionOpt.getOptimum()) else solutionOpt

        return solution

    def onTick(self, step: int, vehiclesInside: Set[Vehicle], newVehicles: Set[Vehicle],
               previousSolution: Solution) -> Solution:
        
        
        start = startTimer()

        self.allVehicles = self.allVehicles.union(newVehicles)
        finalSolution: Solution | None = None

        if self.inputCheckpoint and step <= self.inputCheckpoint.step:
            self.__updateRoutes(newVehicles, self.inputCheckpoint.routesByVehicle)
            return self.inputCheckpoint.solution if self.inputCheckpoint.step == step else None

        
        if ONE_VEHICLE_AT_TIME:
            j = 1 
            for vehicle in newVehicles:
                # routingEnabled = self.statsTraffic["Occupancy"] <= self.args.occupancyTH and self.step >= self.args.startToRoute
                routingEnabled = self.statsTraffic["OccupancyWatched"] <= self.args.occupancyTH and self.step >= self.args.startToRoute
                x = random.random()
                controlVehicle =  x <= self.probabilityControlVehicle and routingEnabled
                vehicle.setControlled(controlled=controlVehicle)

                solution = self.findSolution(step, j, vehiclesInside, {vehicle}, previousSolution)
                self.controlledVehicles += 1 if vehicle.controlled else 0
                self.noAnswerVehicles += 1 if vehicle.noAnswer else 0
                self.orginalRouteVehicles += 1 if vehicle.usingOrginalRoute else 0
                self.processedVehicles += 1
                self.logger.log(f"Step {step}-{j} - Vehicle {vehicle} - Controlled: {vehicle.controlled} - Original Route: {vehicle.usingOrginalRoute} - NoAnswer: {vehicle.noAnswer} - p: {self.probabilityControlVehicle} sampled: {x} - stats: {self.statsTraffic}")
                if not finalSolution or (not finalSolution.hasAnswer and not finalSolution.isArtificial):
                    finalSolution = solution
                else:
                    finalSolution = finalSolution.merge(solution)
                j += 1
        else:
            finalSolution = self.findSolution(step, 1, vehiclesInside, newVehicles, previousSolution)

        # assert len(finalSolution.getSolutionRoutes().items()) == len(newVehicles.union(vehiclesInside))

        routesMap: Dict[str, Route] = finalSolution.getVehiclesUnTimedRouteMap(newVehicles)
        self.__updateRoutes(newVehicles, routesMap)

        elasped = elapsedTime(start)
        self.logger.log(f"Step {step} - Elapsed time: {elasped}")

        outputCheckpoint = CheckPoint(step, finalSolution, self.allVehicles, self.stats)
        checkpointJSON = outputCheckpoint.getJSON()

        # if step % 10 == 0:
        #     self.logger.uploadFile(f"checkpoints/{format(step, '04d')}.json", checkpointJSON)

        return finalSolution
