import math
import re
from typing import Dict, List

import traci
from traffic.Route import Route
from traffic.Street import Street
from traffic.CityNetwork import CityNetwork


class Simulation:

    def __init__(self, network, args = None):
        self.network: CityNetwork = network
        self.args = args

        
    def compute_score_secondary_streets_combined(self,s1: Street, s2: Street) -> int:
        
        edge_s1 = s1.getOriginalLastStreet().id
        edge_s2 = s2.getOriginalFirstStreet().id

        toCrossS1 = s1.getToCross()
        toCrossS2 = s2.getToCross()
        lanes_s1 = self.network.edge_2_lane[edge_s1]

        lane_id_s1 = lanes_s1[0]
        links = traci.lane.getLinks(lane_id_s1, extended=True)  
        has_priority = False
        for link in links:
            lane_out = link[0]
            edge = traci.lane.getEdgeID(lane_out)
            if edge == edge_s2:
                has_priority = link[1]
                break

        one_way = self.is_one_way(s1)
        noSecondary = has_priority or len(lanes_s1) > 1 or (not one_way and (s1.isRoundabout or s2.isRoundabout \
        or toCrossS1.type == "traffic_light" \
        or toCrossS2.type == "traffic_light" ))

        # if re.search("218", s1.id):
        #     lanes_s1 = self.network.edge_2_lane[edge_s1]

        if noSecondary : return 0

        assert len(lanes_s1) == 1

        risk_one_way =  self.compute_score_oneway_street(s1)
        
        return risk_one_way
    
    
    def is_one_way(self, s: Street) -> bool:
        toCross = s.getToCross()
        fromCross = s.getFromCross()
        streets = toCross.getOutgoingStreets()
        for out in streets:
            toCrossOut = out.getToCross()
            if fromCross.id == toCrossOut.id:
                return False
        return True
    
    def compute_score_oneway_street(self, s: Street) -> int:
        risk = 0
        if self.is_one_way(s):
            length = s.getLength()
            score = int(math.exp(length * 0.1))
            risk =  min(1000,score)
        return risk
    
    def order_routes_using_score_secondary_street_combined(self, routes: List[Route], v) -> None:
        
        isV2 = re.search(r"v2",self.args.rules)
        sec = re.search(r"sec",self.args.rules)
        if v.is_electric() or not isV2 or not sec: 
            return

        def route_cost(route: Route) -> float:
            streets = route.getStreets()
            cost = sum(self.compute_score_secondary_streets_combined(streets[i], streets[i+1]) for i in range(len(streets)-1))
            # print(f"{route} -> cost: {cost} ")
            return cost
        
        routes.sort(key=lambda x: route_cost(x)) 




    

    
