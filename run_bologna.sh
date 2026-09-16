name="t=ea"
for i in real green;do
    for o in 0.5 0.7;do
        for v in v2 v2_sec;do
            for w in 0.8; do

                if [[ $i == "green" && $v == "v2_sec" && $o == "0.5" ]]; then
                    continue
                fi

                emissionMap=""
                if [[ "$v" == v2* ]]; then
                    emissionMap="--nameEmissionRisk=emissionRiskFunction"
                fi

                flag1=""
                if [[ "$v" == *sec* ]]; then
                    flag1="--secondary_street_risk"
                fi
                # flag2="--keepOriginalInCaseUNSAT"
                
                expName="$name-mn=bologna-v=$v-s=$i-oth=$o-wth=$w"
                echo "expName: $expName version: $v emissionMap:$emissionMap scenario: $i flag1: $flag1 flag2: $flag2 occ: $o watched:$w ";
                screen -dmS $expName bash -c "conda activate sustainableRouting; \
                    python python/main.py $flag1 $flag2 --probabilityControlVehicle=1 --inputFile=maps/bologna/acosta/run/run-$i.sumocfg \
                    --networkFile=maps/bologna/acosta/netedit/acosta_buslanes.net.xml --rules=$v --messageLog=\"test version $v with scenario $i bologna map\" \
                    --experimentSession $emissionMap --runName=$name --watchedStreets=$w --occupancyTH=$o &> $expName.log; exit"
                sleep 1;
            done
        done
    done
done

