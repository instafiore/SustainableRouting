dir=$1
out=${2:-"results_summarised"}
echo "Reading from $dir, writing results in $out"
for f in $dir/*.csv;do
    res=$(python python/statisticTripInfoCsv.py $f);
    echo "$f -> $res"
done > $out.out

python create_table_current_results.py $dir $out.res