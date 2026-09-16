import json
import math
import os
import sys
import pytest

from common.Arguments import Arguments
from common.CloudLogger import CloudLogger
from emissions.EdgeEmissionSimulator import EdgeEmissionSimulator
from common.LocalLogger import LocalLogger

conf_path = os.getcwd()
sys.path.append(conf_path)
startingDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(startingDir)


@pytest.fixture(scope='module')
def edgeEmissionSimulator():
    args = Arguments()
    args.experimentSession = False
    logger = CloudLogger(args.experiment) if args.cloud else LocalLogger(args.experiment, args)

    args.inputFile = "maps/MK-sim/MK_sim.sumocfg"
    args.networkFile = "maps/MK-sim/net.net.xml"

    dirname = os.path.dirname(os.path.abspath(__file__))
    e = EdgeEmissionSimulator(args.networkFile, args.inputFile, args.hasGUI, logger,
                                                  "EdgeEmissionSimulator", dirname)
    return e


@pytest.mark.parametrize("s1, s2",[
    ("137", "138"),
    ("25", "26"),
    ("133", "134b"),
])
def test_check_connection_false(edgeEmissionSimulator, s1, s2):
    street1 = edgeEmissionSimulator.streets[s1]
    street2 = edgeEmissionSimulator.streets[s2]
    assert not edgeEmissionSimulator.checkConnection(street1, street2, "gasoline_euro4")

@pytest.mark.parametrize("edgesTraci, emissionClass",[
    (["185"], "gasoline_euro4"),
])
def test_is_allowed_false(edgeEmissionSimulator, edgesTraci, emissionClass):
    assert not edgeEmissionSimulator.isAllowed(edgesTraci, emissionClass)


@pytest.mark.parametrize("s1, s2",[
    ("58[1]", "197"),
])
def test_check_connection_true(edgeEmissionSimulator, s1, s2):
    street1 = edgeEmissionSimulator.streets[s1]
    street2 = edgeEmissionSimulator.streets[s2]
    assert edgeEmissionSimulator.checkConnection(street1, street2, "gasoline_euro4")


@pytest.mark.parametrize("streetId,emissionClass",[
    # ("173", "gasoline_euro4"),
    # ("133", "gasoline_euro4"),
    # ("[13|104]", "gasoline_euro4"),
    # ("103", "gasoline_euro4"),
    # ("1", "gasoline_euro4"),
    # ("204a[0]", "gasoline_euro4"),
    # ("189[1][1]", "gasoline_euro4"),
    # ("120", "gasoline_euro4"),
    # ("33", "gasoline_euro4"),
    # ("72[0]", "gasoline_euro4"),
    # ("122", "gasoline_euro4"),
    # ("85", "gasoline_euro4"),
    # ("35", "gasoline_euro4"),
    # ("188", "gasoline_euro4"),
    # ("153", "gasoline_euro4"),


    ("[449|450]", "gasoline_euro4"),
    ("[468|460|461]", "gasoline_euro4"),
])
def test_simulation(edgeEmissionSimulator, streetId, emissionClass):
    edgeEmissionSimulator.logger.log(f"Testing {streetId}: {emissionClass}")
    print()
    light = None
    heavy = None

    street = edgeEmissionSimulator.streets[streetId]
    streetsTo = edgeEmissionSimulator.validOutgoingOfToCross(street, emissionClass)
    for streetTo in streetsTo + [None]:
        # print(f"testing {street} {streetTo}")
        light = edgeEmissionSimulator.simulateEmissions(street=street, streetTo=streetTo, congestion="LIGHT", emissionClass=emissionClass)
        heavy = edgeEmissionSimulator.simulateEmissions(street=street, streetTo=streetTo, congestion="HEAVY", emissionClass=emissionClass)
        # assert light <= heavy
        print(f"street {street} {streetTo} light: {light} log: {math.log(light)} heavy: {heavy} heavy: {math.log(heavy)}")



def test_creation_map(edgeEmissionSimulator):
    emissionRisk = edgeEmissionSimulator.createEdgeEmissionRisk()
    print(emissionRisk)



