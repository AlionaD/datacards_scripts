#!/bin/bash

while getopts "f:s:c:w:" opt; do
  case $opt in
    f)
      folder="$OPTARG"
      ;;
    s)
      subfolder="$OPTARG"
      ;;
    c)
      cardname="$OPTARG"
      ;;
    w)
      wsname="$OPTARG"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

script_folder="$(dirname "$0")"
categories=$(jq -r 'keys[]' $script_folder/categories.json)

folder=${folder-"/eos/user/a/adodonov/SWAN_projects/Combine/Datacards/"}
subfolder=${subfolder:-"last_day2"} 
cardname=${cardname:-"$subfolder"}.txt
wsname=${wsname:-"ws"}.root

commanda=''

i=1
for category in $categories; do
  datacard_dir="$folder$subfolder/StatModel/$category/$(ls "$folder$subfolder/StatModel/$category")"
  datacard_file="$datacard_dir/datacard.txt"
  shapes_file="$datacard_dir/shapes_badbin.root"
  if [ ! -e "$shapes_file" ]; then
    mv "$datacard_dir/shapes.root" "$shapes_file"
  fi
  python3 $script_folder/rebin.py --filename $shapes_file --bin_condition 3 --bin_uncert_fraction 100
  commanda+=" $category=$datacard_file"
  ((i++))
done

echo "$commanda"

combineCards.py $commanda > "$cardname"
ulimit -s unlimited
text2workspace.py $cardname -o $wsname
