#!/bin/bash

categories_data=$(jq -r 'keys[]' categories.json)

folder="/eos/user/a/adodonov/SWAN_projects/Combine/Datacards/"
subfolder="${1:-last_day2}"

for category_key in $categories_data; do
    category=$(jq -r ".\"$category_key\"" categories.json)
    pt_region=$(echo "$category" | jq -r '.pt_region')
    region=$(echo "$category" | jq -r '.region')

    datacard_dir="$folder$subfolder/StatModel/$category_key/$(ls "$folder$subfolder/StatModel/$category_key")"
    datacard_file="$datacard_dir/datacard.txt"

    if [ "$pt_region" == "low" ]; then
        line1="SF_LOW_"
    elif [ "$pt_region" == "high" ]; then
        line1="SF_HIGH_"
    fi

    if [ "$region" == "CR_zhf" ] || [ "$region" == "CR_zlf" ]; then
        line1+="DY_Zll_2017      rateParam  *          dy         1 [0,5]"
	sed -i -e "\$i $line1" "$datacard_file"
    elif [ "$region" == "CR_tt_bar" ]; then
        line1+="TT_Zll_2017      rateParam  *          tt         1 [0,5]"
	sed -i -e "\$i $line1" "$datacard_file"
    elif [ "$region" == "Signal" ]; then
        line1+="DY_Zll_2017      rateParam  *          dy         1 [0,5]"
        line2="${line1/DY/TT}"
        line2="${line2//dy/tt}"
        sed -i -e "\$i $line2" -e "\$i $line1" "$datacard_file"
    fi
done

