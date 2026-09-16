import sys
import pandas as pd

out = sys.argv[1]
dfFinal = None

while True:
    line = sys.stdin.readline().strip()
    if line == "":
        break
    field = line.split()
    file = field[0]
    vtype = field[1] if len(field) > 1 else ""
    print(vtype)
    df = pd.read_csv(file)
    df["version"] = file.replace(".csv","")
    if vtype:  df["type"] = vtype 
    if df is None:
        dfFinal = df
    else:
        dfFinal = pd.concat([dfFinal, df], axis=0)

with open(f"{out}.csv", 'w') as f:
    dfFinal.to_csv(f, index=False)

