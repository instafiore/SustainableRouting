import argparse
import json
import os
import re
import sys

from common.Arguments import Arguments
from common.CloudLogger import CloudLogger
from emissions.EdgeEmissionSimulator import EdgeEmissionSimulator
from common.LocalLogger import LocalLogger
from preprocessors.PreProcessorLustSubnet import PreProcessorLustSubnet

conf_path = os.getcwd()
sys.path.append(conf_path)
startingDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(startingDir)
regexMap = r".*\/(?P<map>.*?)\."

def create_argparser():
    parser = argparse.ArgumentParser(description="Traffic Distribution Preprocessor Routes Lust")
    parser.add_argument("--experiment", type=str, default="exp", help="Name of the experiment")

    parser.add_argument("--routesFile", type=str, default="maps/LuSTScenario/scenario/DUARoutes/local.0.rou.xml", help="Path to the route file")
   
    # parser.add_argument("--inputFile", type=str, default="maps/bologna/acosta/run/run.sumocfg", help="Path to the SUMO configuration file")
    parser.add_argument("--inputFile", type=str, default="maps/LuSTScenario/scenario/subnet/run-1.sumocfg", help="Path to the SUMO configuration file")
   
    # parser.add_argument("--networkFile", type=str, default="maps/bologna/acosta/netedit/acosta_buslanes.net.xml", help="Path to the network file")
    parser.add_argument("--networkFile", type=str, default="maps/LuSTScenario/scenario/subnet/subnetLust.net.xml", help="Path to the network file")


    parser.add_argument("--subnetRoutes", type=str, default="subnet-real.rou.xml", help="Path to the network file")
    
    parser.add_argument("--experimentSession", action='store_true', help="Enable experiment session")
    parser.add_argument("--loggerDisabled", action='store_true', help="Disable logger")

    parser.add_argument("--messageLog", type=str, default="noMessageLog", help="Message log for the experiment")

    return parser

def main():
    args = create_argparser().parse_args()

    mapName = re.search(regexMap, args.networkFile).group("map")
    inputFileName = os.path.basename(args.inputFile).replace(".sumocfg", "")
    args.run_name = f"{inputFileName}-{mapName}-{args.routesFile}"

    logger = LocalLogger(args.experiment, args)

    dirname = os.path.dirname(args.inputFile)
    preprocessor = PreProcessorLustSubnet(args.networkFile, args.inputFile, logger, "PreProcessorLustSubnet", args=args)
    newRoutes = preprocessor.createSubnetRoutes()
    with open(os.path.join(dirname, args.subnetRoutes), "w") as routeFile:
        routeFile.write(newRoutes)

if __name__ == '__main__':
    main()
