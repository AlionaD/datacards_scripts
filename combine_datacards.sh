#!/bin/bash

script_folder="$(dirname "$0")"
categories=$(jq -r 'keys[]' $script_folder/categories.json)

folder=${3-"/eos/user/a/adodonov/SWAN_projects/Combine/Datacards/"}
subfolder=${1-"last_day2"} 
cardname=${2-"$subfolder"}.txt

commanda=''

i=1
for category in $categories; do
  datacard_dir="$folder$subfolder/StatModel/$category/$(ls "$folder$subfolder/StatModel/$category")"
  datacard_file="$datacard_dir/datacard.txt"
 # commanda+=" Name$i=$datacard_file"
  commanda+=" $category=$datacard_file"
  ((i++))
done

echo "$commanda"
combineCards.py $commanda > "$cardname"
