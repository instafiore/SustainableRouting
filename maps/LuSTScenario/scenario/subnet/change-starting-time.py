


import re
import sys
from xml.dom import minidom


inc = 0.3
max_vehicles = 10**4


def changeStartingTime(file):
    count = 0
    start = 0.0
    subvehicles = []
    xmldoc = minidom.parse(file)
    for v in xmldoc.getElementsByTagName("vehicle"):
        start = round(start, 2)
        v.setAttribute("depart", str(start))
        start += inc
        count += 1
        subvehicles.append(v)
        if count >= max_vehicles:
            break
        
    
    out = re.sub(r".rou.xml", "-inc0.3.rou.xml", file)

    document = minidom.Document()

    routesXML = document.createElement("routes")

    # xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd"
    routesXML.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    routesXML.setAttribute("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/routes_file.xsd")


    for v in subvehicles:
        routesXML.appendChild(v)

    document.appendChild(routesXML)

    with open(out, "w") as f:
        f.write(document.toxml())


if __name__ == "__main__":
    changeStartingTime(sys.argv[1])