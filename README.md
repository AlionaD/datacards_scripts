1. File `categories.json` consist of analysis categories
2. File `add_sf.sh` adds background SF. Todo: add case $opt 
   <code>
   ./add_sf.sh subfolder folder_name  
   </code>
4. File `combine_datacards.sh` creates a combination of datacards and a workspace
   <code>
   ./combine_datacards.sh -f folder_name -s subfolder -c out_datacard_name -w wokspace_name
   ./combine_datacards.sh -s "november6/card_three_data" -c "card_three_data" -w "masked_ws_three"  
   </code>
