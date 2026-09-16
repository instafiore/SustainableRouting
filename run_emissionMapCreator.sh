# bologna
screen -dmS bologna-emissionRiskFunction bash -c "conda activate sustainableRouting;\
    python python/simulatingEmissions.py --experimentSession \
    --inputFile=maps/bologna/acosta/run/run-1.sumocfg \
    --networkFile=maps/bologna/acosta/netedit/acosta_buslanes.net.xml \
    --messageLog=\"creating emission risk function\" \
    --nameEmissionRisk=emissionRiskFunction \
    --runName=\"bologna-emissioriskf\" \
    &> bologna-emissionRiskFunction.log; exit"
# mk 
screen -dmS mk-emissionRiskFunction bash -c "conda activate sustainableRouting;\
    python python/simulatingEmissions.py --experimentSession \
    --inputFile=maps/MK-sim/run-1.sumocfg \
    --networkFile=maps/MK-sim/net.net.xml \
    --messageLog=\"creating emission risk function\" \
    --nameEmissionRisk=emissionRiskFunction \
    --runName=\"mk-emissioriskf\" \
    &> mk-emissionRiskFunction.log; exit"
# lux
screen -dmS lux-emissionRiskFunction bash -c "conda activate sustainableRouting;\
    python python/simulatingEmissions.py --experimentSession \
    --inputFile=maps/LuSTScenario/scenario/subnet/run-1.sumocfg \
    --networkFile=maps/LuSTScenario/scenario/subnet/subnetLust.net.xml \
    --messageLog=\"creating emission risk function\" \
    --nameEmissionRisk=emissionRiskFunction \
    --runName=\"lux-emissioriskf\" \
    &> lux-emissionRiskFunction.log; exit"
echo "Ran"