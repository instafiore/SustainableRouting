# Sustainable Routing
This is the repo used in the paper: Sustainable Routing

The default settings are the same used for the related results achieved in the paper.

The default map is acosta (Bologna)
Results can be found at: [results](https://docs.google.com/spreadsheets/d/1aTKYOtQ8xg2es-Ua_JuZ8gjT3_2_r7Or/edit?usp=sharing&ouid=116244935530004337059&rtpof=true&sd=true)

## Dependencies
1. ```conda 23.7.2```
2. ```clingo 5.7.0```
3. ```Eclipse SUMO sumo 1.11.0```

## How to install

```
conda create --name sustainableRouting
conda activate sustainableRouting
conda config --append channels conda-forge
conda env update --file environment.yaml
```

### Bologna
The map can be found in `maps/bologna/acosta`

```
export NETWORK_FILE=maps/bologna/acosta/acosta_buslanes.net.xml;
export SUMOCFG_FILE=maps/bologna/acosta/run.sumocfg
export SUMO_PATH=path/to/sumo
export CLINGO_HOME=path/to/clingo
```

### Running
```bash
conda activate sustainableRouting
python python/main.py
```

