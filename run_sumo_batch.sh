# sumocfg=/Users/salvatore/git/traffic-distribution/maps/bologna/acosta/run/run-v2.sumocfg
# sumocfg=/Users/salvatore/git/traffic-distribution/maps/MK-sim/run-v2.sumocfg
sumocfg=/Users/salvatore/git/traffic-distribution/maps/LuSTScenario/scenario/subnet/run-v2.sumocfg

# for fPath in maps/bologna/acosta/run/solutions/asp-v2/2026_03_20_*;do
# for fPath in maps/MK-sim/solutions/asp-v2/2026_03_20*;do
for fPath in maps/LuSTScenario/scenario/subnet/solutions/asp-v2/2026_03_20*;do
    f=$(basename $fPath)
    echo $f;
    sed -i "" "s|solutions/asp-v2/.*/solution.xml|solutions/asp-v2/$f/solution.xml|" $sumocfg
    bash run_sumo.sh $sumocfg
done