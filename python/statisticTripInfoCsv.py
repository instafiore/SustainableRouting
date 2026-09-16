import pandas as pd
import sys

path = sys.argv[1]

csv = pd.read_csv(path)

c02 = csv["CO2_abs"]


print(f"total: {c02.sum()*10**-6} mean: {c02.mean()*10**-6} max: {c02.max()*10**-6} min: {c02.min()*10**-6} median: {c02.median()*10**-6} std: {c02.std()*10**-6}")