import os.path
import sys
import xml.etree.ElementTree as ET
import statistics
import csv

emissionPath = sys.argv[1]
outputPath = sys.argv[2]
tree = ET.parse(emissionPath)
root = tree.getroot()

# Collect data
data = []
vehicles = set()
for timestep in root.findall("timestep"):
    time = float(timestep.attrib["time"])
    for vehicle in timestep.findall("vehicle"):
        vehicles.add(vehicle.attrib["id"])
        co2 = float(vehicle.attrib.get("CO2", 0))
        entry = {
            "time": time,
            "id": vehicle.attrib["id"],
            "vType": vehicle.attrib["type"],
            "watingTime": vehicle.attrib["waiting"],
            "CO2": co2,
            # "CO": float(vehicle.attrib.get("CO", 0)),
            # "NOx": float(vehicle.attrib.get("NOx", 0)),
            # "PMx": float(vehicle.attrib.get("PMx", 0)),
            # "fuel": float(vehicle.attrib.get("fuel", 0)),
        }
        if co2 > 0:
            data.append(entry)

# Helper to summarize a single metric
def summarize(name, values, vehicles):
    if not values:
        return f"{name}: No data"
    valuesKg = [v * 10 ** (-6) for v in values]
    meanPerVehicle = sum(valuesKg) / len(vehicles)
    return (
        f"{name}:\n"
        f"  Total: {sum(valuesKg):.2f}Kg\n"
        f"  Mean: {sum(values) / len(values):.2f}mg\n"
        f"  MeanPerVehicle: {meanPerVehicle:.2f}Kg\n"
        f"  Max: {max(values):.2f}mg\n"
        f"  Min: {min(values):.2f}mg\n"
        f"  Std Dev: {statistics.stdev(values):.2f}mg\n"
        f"  Median: {statistics.median(values):.2f}mg\n"
        f"  Number of vehicles: {len(vehicles)}\n"
    )

# Extract lists
CO2_vals = [d["CO2"] for d in data]
# NOx_vals = [d["NOx"] for d in data]
# fuel_vals = [d["fuel"] for d in data]
# CO_vals = [d["CO"] for d in data]
# PMx_vals = [d["PMx"] for d in data]

# Print summaries
print(summarize("CO2 (mg)", CO2_vals, vehicles))
# print(summarize("NOx (mg)", NOx_vals))
# print(summarize("CO (mg)", CO_vals))
# print(summarize("PMx (mg)", PMx_vals))
# print(summarize("Fuel (ml)", fuel_vals))

# Optional: write detailed raw data to CSV
basename = os.path.basename(emissionPath)
with open(f"{outputPath}.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
