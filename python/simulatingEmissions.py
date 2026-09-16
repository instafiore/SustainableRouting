import argparse
import json
import os
import re
import sys

from common.Arguments import Arguments
from common.CloudLogger import CloudLogger
from emissions.EdgeEmissionSimulator import EdgeEmissionSimulator
from common.LocalLogger import LocalLogger

conf_path = os.getcwd()
sys.path.append(conf_path)
startingDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(startingDir)


def create_argparser():
    parser = argparse.ArgumentParser(description="Traffic Distribution Preprocessor")
    parser.add_argument("--experiment", type=str, default="exp", help="Name of the experiment")

    # parser.add_argument("--inputFile", type=str, default="maps/bologna/acosta/run/run.sumocfg", help="Path to the SUMO configuration file")
    parser.add_argument("--inputFile", type=str, default="maps/LuSTScenario/scenario/subnet/run.sumocfg", help="Path to the SUMO configuration file")
   
    # parser.add_argument("--networkFile", type=str, default="maps/bologna/acosta/netedit/acosta_buslanes.net.xml", help="Path to the network file")
    parser.add_argument("--networkFile", type=str, default="maps/LuSTScenario/scenario/subnet/subnetLust.net.xml", help="Path to the network file")
    

    parser.add_argument("--hasGUI", action='store_true', help="Enable GUI mode")
    parser.add_argument("--cloud", action='store_true', help="Enable cloud logging")
    parser.add_argument("--experimentSession", action='store_true', help="Enable experiment session")
    parser.add_argument("--loggerDisabled", action='store_true', help="Disable logger")
    parser.add_argument("--nameEmissionRisk", type=str, default="emissionRisk", help="Name of the emission map file")
    parser.add_argument("--messageLog", type=str, default="noMessageLog", help="Message log for the experiment")
    parser.add_argument("--runName", type=str, default="", help="Additional name to the run")

    return parser


regexMap = r".*\/(?P<map>.*?)\."
def main():
    args = create_argparser().parse_args()
    mapName = re.search(regexMap, args.networkFile).group("map")
    inputFileName = os.path.basename(args.inputFile).replace(".sumocfg", "")
    runName = f"{args.runName}-" if args.runName else ""
    args.run_name = f"{runName}{inputFileName}-{mapName}-{args.nameEmissionRisk}"
    logger = CloudLogger(args.experiment) if args.cloud else LocalLogger(args.experiment, args)

    dirname = os.path.dirname(args.inputFile)
    edgeEmissionSimulator = EdgeEmissionSimulator(args.networkFile, args.inputFile, args.hasGUI, logger, "EdgeEmissionSimulator", dirname)
    emissionRisk = edgeEmissionSimulator.createEdgeEmissionRisk()
    with open(os.path.join(dirname, args.nameEmissionRisk), "w") as mapFile:
        json.dump(emissionRisk, mapFile)

if __name__ == '__main__':
    main()
