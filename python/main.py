import json
import logging
import os
import sys

import traci
import argparse
import re
from common.Arguments import Arguments, PreProcessorType
from common.CloudLogger import CloudLogger
from preprocessors.CumulativeOccupancyHeuristic import CumulativeOccupancyHeuristicPreProcessor
from preprocessors.DensityHeuristic import DensityHeuristicPreProcessor
from preprocessors.Dijkstra import DijkstraPreProcessor
from preprocessors.Plain import PlainPreprocessor
from preprocessors.Random import RandomPreProcessor
from preprocessors.ASP import ASPPreProcessor
from preprocessors.ComputeMostCongestEdges import ComputeMostCongestedEdges
from common.LocalLogger import LocalLogger
from common.constants import *
# from preprocessors.MyPreProcessor import PreProcessor
from preprocessors.PreProcessor import PreProcessor
from emissions.EdgeEmissionSimulator import SEPARATOR_EMISSIONRISK
conf_path = os.getcwd()
sys.path.append(conf_path)
import subprocess

startingDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(startingDir)

regexMap = r".*\/(?P<map>.*?)\."


def create_argparser():
    parser = argparse.ArgumentParser(description="Traffic Distribution Preprocessor")
    parser.add_argument("--experiment", type=str, default="exp", help="Name of the experiment")

    parser.add_argument("--inputFile", type=str, default="maps/bologna/acosta/run/run-1.sumocfg", help="Path to the SUMO configuration file")
    # parser.add_argument("--inputFile", type=str, default="maps/LuSTScenario/scenario/subnet/run.sumocfg", help="Path to the SUMO configuration file")
   
    parser.add_argument("--networkFile", type=str, default="maps/bologna/acosta/netedit/acosta_buslanes.net.xml", help="Path to the network file")
    # parser.add_argument("--networkFile", type=str, default="maps/LuSTScenario/scenario/subnet/subnetLust.net.xml", help="Path to the network file")
    
    
    parser.add_argument("--checkpointFile", type=str, default="", help="Path to the checkpoint file")
    
    parser.add_argument("--watchedStreets", type=float, default=0.8, help="Threshold for selecting  watched streets")

    # parser.add_argument("--rules", type=str, default="v1", help="Version of the rules")
    parser.add_argument("--rules", type=str, default="v2-sec", help="Version of the rules")
    
    # parser.add_argument("--startToRoute", type=int, default=sys.maxsize, help="After how many steps you should start to route")
    parser.add_argument("--startToRoute", type=int, default=0, help="After how many steps you should start to route")

    parser.add_argument("--preprocessor", type=PreProcessorType, default=PreProcessorType.ASP, help="Type of preprocessor to use")
    parser.add_argument("--hasGUI", action='store_true', help="Enable GUI mode")
    parser.add_argument("--cloud", action='store_true', help="Enable cloud logging")
    parser.add_argument("--experimentSession", action='store_true', help="Enable experiment session")
    parser.add_argument("--loggerDisabled", action='store_true', help="Disable logger")
    parser.add_argument("--HORIZON", type=int, default=None, help="Horizon for the simulation")
    parser.add_argument("--nameEmissionRisk", type=str, default=None, help="Name of the emission map file")
    parser.add_argument("--messageLog", type=str, default="noMessageLog", help="Message log for the experiment")
    parser.add_argument("--probabilityControlVehicle", type=float, default=1.0, help="Probability of controlling a vehicle")
    parser.add_argument("--runName", type=str, default="", help="Additional name to the run")
    parser.add_argument("--secondary_street_risk", action="store_true", help="Computing Secondary Street Risk")
    parser.add_argument("--one_way_street_risk", action="store_true", help="Computing One Way Street Risk")
    parser.add_argument("--keepOriginalInCaseUNSAT", action="store_true", help="Weather to keep the original route in case of unsat instance")
    parser.add_argument("--occupancyTH", type=float, default=0.05, help="Threshold to deactivate routing")

    return parser


def main():

    args = create_argparser().parse_args()
    # args.HORIZON = 1
    mapName = re.search(regexMap, args.networkFile).group("map")
    inputFileName = os.path.basename(args.inputFile).replace(".sumocfg", "")
    
    scenario = inputFileName.split("-")[1]
    runName = f"{args.runName}{delim}" if args.runName else ""
    strout = args.startToRoute if args.startToRoute != sys.maxsize else "inf"
    args.run_name = f"{runName}s={scenario}{delim}mn={mapName}{delim}v={args.rules}{delim}pcv={args.probabilityControlVehicle}{delim}str={strout}{delim}oth={args.occupancyTH}{delim}wth={args.watchedStreets}"
    message = args.messageLog if args.messageLog else ""
    args.messageLog = f"probability: {args.probabilityControlVehicle} {args.run_name} , version rules {args.rules}, HORIZON {args.HORIZON}, emission risk {args.nameEmissionRisk}, preprocessor {args.preprocessor} \n{message}"

    logger = CloudLogger(args.experiment) if args.cloud else LocalLogger(args.experiment, args)

    logger.log(f"input file: {args.inputFile}", logging.INFO)
    logger.log(f"network file: {args.networkFile}", logging.INFO)
    logger.log(f"message: {args.messageLog}", logging.INFO)
    logger.log(f"Arguments: {args}")

    dirname = os.path.dirname(args.inputFile)
    emissionRisk = None
    if args.nameEmissionRisk and re.search(r"v2",args.rules):
        with open(os.path.join(dirname, args.nameEmissionRisk), "r") as mapFile:
            emissionRiskWithStringKeys = json.load(mapFile)
            emissionRisk = dict()
            for key in emissionRiskWithStringKeys:
                tupleKey = tuple(key.split(SEPARATOR_EMISSIONRISK))
                assert len(tupleKey) == 4, f"Emission risk key {key} is not a tuple of 4 elements"
                emissionRisk[tupleKey] = float(emissionRiskWithStringKeys[key])
            logger.log(f"Emission awareness enabled")
    else:
        logger.log(f"Emission awareness not enabled")

    if args.preprocessor == PreProcessorType.ASP:
        preprocessor = ASPPreProcessor(args.networkFile, args.inputFile, args.hasGUI, logger, args, checkPointFile=args.checkpointFile, emissionRisk=emissionRisk, exp=args.experimentSession)
    elif args.preprocessor == PreProcessorType.RANDOM:
        preprocessor = RandomPreProcessor(args.networkFile, args.inputFile, args.hasGUI, logger)
    elif args.preprocessor == PreProcessorType.CUMULATIVE:
        preprocessor = CumulativeOccupancyHeuristicPreProcessor(args.networkFile, args.inputFile, args.hasGUI, logger)
    elif args.preprocessor == PreProcessorType.DENSITY:
        preprocessor = DensityHeuristicPreProcessor(args.networkFile, args.inputFile, args.hasGUI, logger)
    elif args.preprocessor == PreProcessorType.DIJKSTRA:
        preprocessor = DijkstraPreProcessor(args.networkFile, args.inputFile, args.hasGUI, logger)
    elif args.preprocessor == PreProcessorType.PLAIN:
        preprocessor = PlainPreprocessor(args.networkFile, args.inputFile, args.hasGUI, logger)
    elif args.preprocessor == PreProcessorType.ComputeMostCongestedEdges:
        preprocessor = ComputeMostCongestedEdges(args.networkFile, args.inputFile, args.hasGUI, logger, args, exp=args.experimentSession)
    else:
        raise Exception(f"Preprocessor {args.preprocessor} was not found")

    preprocessor.solve()

if __name__ == '__main__':
    main()
