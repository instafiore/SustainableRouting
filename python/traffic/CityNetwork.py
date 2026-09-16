import math
from queue import PriorityQueue
from typing import Dict, List, Set

import sumolib.net
from sumolib.net.edge import Edge

import common.constants as constants
from traffic.Cross import Cross
from traffic.Roundabout import Roundabout
from traffic.Route import Route
from traffic.Street import Street

import traci 

BLACKLISTED = {"125"}


class CityNetwork:

    def __init__(self, sumoNetwork: sumolib.net.Net, isV2):
        
        self.isV2 = isV2
        self.edge_2_lane : Dict[str, str] = dict()
        for lane_id in traci.lane.getIDList():
            edge_id = traci.lane.getEdgeID(laneID=lane_id)
            self.edge_2_lane.setdefault(edge_id, [])
            self.edge_2_lane[edge_id].append(lane_id)

        self.streets: Dict[str, Street] = dict()
        self.crosses: Dict[str, Cross] = dict()
        self.isSimplified = False
        self.sumoNetwork: sumolib.net.Net = sumoNetwork

        self.cachedMostDifferentRoutes: Dict[(str, str, str), List[Route]] = dict()
        
        edge: Edge
        for edge in sumoNetwork.getEdges():

            if edge.getID() in BLACKLISTED:
                continue

            fromCross = edge.getFromNode().getID()
            toCross = edge.getToNode().getID()
            self.crosses[fromCross] = Cross(edge.getFromNode()) if fromCross not in self.crosses else self.crosses[
                fromCross]
            self.crosses[toCross] = Cross(edge.getToNode()) if toCross not in self.crosses else self.crosses[toCross]

            street = Street(edge.getID(), self.crosses[fromCross], self.crosses[toCross], edge.getLength(),
                            edge.getLaneNumber())
            self.crosses[fromCross].addOutgoingStreet(street)
            self.crosses[toCross].addIngoingStreet(street)
            self.streets[street.id] = street
       
        fromEdge: Edge
        toEdge: Edge
        for fromEdge in sumoNetwork.getEdges():
            id = fromEdge.getID()
            outgoing = fromEdge.getOutgoing()
            for toEdge in outgoing:
                if fromEdge.getID() in BLACKLISTED or toEdge.getID() in BLACKLISTED:
                    continue
                fromStreet: Street = self.streets[fromEdge.getID()]
                toStreet: Street = self.streets[toEdge.getID()]
                fromStreet.addTurn(toStreet)
        
        self.roundabouts = [Roundabout(r, self) for r in sumoNetwork.getRoundabouts()]
        
    
    def is_bus_only_edge(self, edge_id):
        try:                
            lanes = self.edge_2_lane[edge_id]

            for lane in lanes:
                allowed = traci.lane.getAllowed(lane)
                if len(allowed) != 1 or allowed[0] != "bus":
                    return False
            
            return True
        
        
        except traci.TraCIException as e:
            # This might happen if the edge_id is invalid for some reason.
            print(f"Could not get permissions for edge '{edge_id}': {e}")
        
    @staticmethod
    def simplifyRoute(route: Route):
        raise NotImplemented("Cannot simplify route in CityNetwork (can be done in SimplifiedCityNetwork)")

    def getRoundabouts(self):
        return self.roundabouts

    def getStreet(self, streetId: str):
        return self.streets[streetId]

    def getCross(self, crossId: str):
        return self.crosses[crossId]

    def getCrosses(self):
        return self.crosses.values()

    def addStreet(self, street: Street):
        self.streets[street.id] = street

    def findShortestRoute(self, fromCrossId: str, toCrossId: str, vehicle=None) -> Route:
        return self.findAllRoutes(fromCrossId, toCrossId, vehicle=vehicle, maxRoutes=1)[0]

    def findMostDifferentRoutes(self, fromCrossId: str, toCrossId: str, vehicle=None):

        fromId = fromCrossId if not vehicle else vehicle.getFirstStreet()
        if (fromId, toCrossId, vehicle.type) in self.cachedMostDifferentRoutes:
            return [r.copy() for r in self.cachedMostDifferentRoutes[(fromId, toCrossId, vehicle.type)]]
        routes: [Route] = self.findAllRoutes(fromCrossId, toCrossId, vehicle=vehicle, maxRoutes=50, limited=True)

        buckets = list()
        usedRoutes = set()
        for bestRoute in routes:
            if bestRoute in usedRoutes:
                continue
            bucket = list([bestRoute])
            usedRoutes.add(bestRoute)
            for subRoute in routes:
                if subRoute in usedRoutes:
                    continue
                (similitude, equalStreets) = bestRoute.compare(subRoute)
                if similitude > constants.SIMILITUDE_THRESHOLD:
                    bucket.append(subRoute)
                    usedRoutes.add(subRoute)
            if bucket:
                buckets.append(bucket)

        mostDifferentRoutes = list()
        bucketId = 0
        listId = 0
        nOfBuckets = len(buckets)
        for i in range(0, min(constants.MAXIMUM_NUMBER_OF_ROUTES, len(routes))):
            while len(buckets[bucketId]) == 0:
                bucketId = (bucketId + 1) % nOfBuckets
            mostDifferentRoutes.append(buckets[bucketId][listId])
            del buckets[bucketId][listId]
            bucketId = (bucketId + 1) % nOfBuckets

        self.cachedMostDifferentRoutes[(fromId, toCrossId, vehicle.type)] = mostDifferentRoutes
        return mostDifferentRoutes

    def findAllRoutes(self, fromCrossId: str, toCrossId: str, vehicle=None, maxRoutes=None,
                      limited=True) -> [Route]:
        initCross: Cross = self.crosses[fromCrossId]
        targetCross: Cross = self.crosses[toCrossId]
        allRoutes = list()

        bfsQueue: List[Route] = list()

        bestRouteMetric = 0
        routesFound = 0

        # added
        # beam = maxRoutes * 10
        initialBeam = maxRoutes * 3
        beam = max(initialBeam, 100)
        #

        # added
        targetStreets = targetCross.getIngoingStreets()
        minLengthRoute = None
        #

        initStreets = initCross.getOutgoingStreets() if not vehicle else [vehicle.getFirstStreet()]

        for neighbourEdge in initStreets:
            r = Route()
            if vehicle and not vehicle.canGo(neighbourEdge):
                continue
            r.addStreet(neighbourEdge)
            # added
            # nEdge = neighbourEdge.getOriginalFirstStreet()
            # for targetStreet in targetStreets:
            #     targetEdge = targetStreet.getOriginalFirstStreet()
            #     res = traci.simulation.findRoute(nEdge.id, targetEdge.id)
            #     l = res.length
            #     if  l > 0 and (minLengthRoute is None or l < minLengthRoute.length):
            #         minLengthRoute = res
            #
            bfsQueue.append(r)

        trace = list()

        i = 1
        while len(bfsQueue) > 0:
            newCandidateRoutes: List[Route] = list()
            for route in bfsQueue:
                lastStreet: Street = route.getLastStreet()
                lastCross: Cross = lastStreet.getToCross()

                trace.append(route.copy())

                if lastCross.id == targetCross.id:
                    routesFound += 1
                    # print(f"{routesFound}° route. Metric of the route {route.getLength()} with {len(route.getStreets())} streets {route}")
                    allRoutes.append(route)
                    if bestRouteMetric == 0:
                        bestRouteMetric = route.getMetric()
                    if maxRoutes and routesFound > maxRoutes:
                        # print(f"Found {len(allRoutes)} routes. minLengthRoute length: {minLengthRoute.length} and {len(minLengthRoute.edges)} edges. Best metric: {bestRouteMetric}")
                        return allRoutes
                    continue

                for turnStreet in lastStreet.getTurns():
                    addedRoute = route.copy()
                    if vehicle and not vehicle.canGo(turnStreet):
                        continue
                    addedRoute.addStreet(turnStreet)

                    
                    if not addedRoute.hasCycles() and (
                            not limited or not bestRouteMetric or addedRoute.getMetric() < bestRouteMetric * constants.MAXIMUM_ROUTE_LENGTH_FROM_SHORTEST):
                            # added
                            # not limited or not minLengthRoute or addedRoute.getMetric() < minLengthRoute.length * constants.MAXIMUM_ROUTE_LENGTH_FROM_SHORTEST):
                            #
                        
                        # newCandidateRoutes.append((addedRoute, self.heuristic1(addedRoute)))
                        newCandidateRoutes.append((addedRoute, self.heuristic2(addedRoute, targetStreets=targetStreets)))

            newCandidateRoutes = sorted(newCandidateRoutes, key=lambda x: x[1])
            newCandidateRoutes = newCandidateRoutes[:beam] if len(newCandidateRoutes) >= beam else newCandidateRoutes
            bfsQueue.clear()
            for newRoute, _ in newCandidateRoutes:
                bfsQueue.append(newRoute)

            # print(f"size: {len(bfsQueue)} beam: {beam} i: {i} routesFound: {routesFound} bestRouteMetric: {bestRouteMetric}")
            i += 1
                

        # added
        # print(f"found route from {initCross.id} to {targetCross.id} with {len(allRoutes)} routes")
        # TODO: remove
        # print(f"Found {len(allRoutes)} routes. minLengthRoute with length: {minLengthRoute.length} and {len(minLengthRoute.edges)} edges. Best metric: {bestRouteMetric}")
        #
        if len(allRoutes) == 0:
            allRoutes = [vehicle.getOriginalRoute()]
        return allRoutes
    
    def heuristic1(self, route: Route) -> float:
        """
        Heuristic function to estimate the cost of a route.
        """
        firstStreet: Street = route.getFirstStreet()
        lastStreet: Street = route.getLastStreet()
        firstEdge = firstStreet.getOriginalFirstStreet().id
        lastEdge  = lastStreet.getOriginalFirstStreet().id
        ground_truth = traci.simulation.findRoute(firstEdge, lastEdge)
        assert ground_truth.length > 0, f"Ground truth length is zero for route {route}"
        return route.getLength() / ground_truth.length 
    
    def heuristic2(self, route: Route, targetStreets) -> float:
        """
        Heuristic function to estimate the cost of a route.
        """
        n = len(targetStreets)
        firstStreet: Street = route.getFirstStreet()
        lastStreet: Street = route.getLastStreet()
        firstEdge = firstStreet.getOriginalFirstStreet().id
        lastEdge  = lastStreet.getOriginalFirstStreet().id
        s = 0 
        for targetStreet in targetStreets:
            targetEdge = targetStreet.getOriginalLastStreet().id
            if targetEdge == lastEdge:
                return 0
            try:
                ground_truth = traci.simulation.findRoute(lastEdge, targetEdge)
            except Exception as e:
                print(f"Error finding route from {lastEdge} to {targetEdge}: {e}")
                continue
            if len(ground_truth.edges) == 0:
                continue
            s += ground_truth.length
        return s / n 
