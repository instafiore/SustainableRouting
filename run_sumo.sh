sumo_cfg=$1 # sumo config file
basename_file=$(basename "$sumo_cfg")
dirname_dir=$(dirname "$sumo_cfg")
version=$(echo $basename_file | cut -d'-' -f2)
version=${version%.sumocfg}
name=$(cat $sumo_cfg | grep route-files | grep -o 'solutions/asp-.*/[^/]*'  | cut -d'/' -f3)
echo "$version $sumo_cfg $name"
if [ -z $name ]; then 
    name="$version"
fi
sumo -c $sumo_cfg --device.emissions.probability 1.0
python python/tripInfoReport.py "$dirname_dir/tripinfos-$version.xml" "$name"