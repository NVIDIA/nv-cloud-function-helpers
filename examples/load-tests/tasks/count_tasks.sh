#! /bin/bash
set -e

# take in one command argument for the org id
ORG_ID=$1

# check to see if the org id is provided
if [ -z "$ORG_ID" ]; then
    echo "org id is required"
    exit
fi

# check to see if the ngc cli is installed
if ! command -v ngc &> /dev/null
then
    echo "ngc cli could not be found - please install it from https://org.ngc.nvidia.com/setup/installers/cli"
    exit
fi

# get the number of tasks in the org in json format
echo "Getting tasks for org $ORG_ID"
TASKS=$(ngc cf task ls --org $ORG_ID --format_type json)

# print the number of tasks
echo "Total number of tasks in org $ORG_ID: $(echo "$TASKS" | jq '. | length')"

# print the number of tasks in each status
echo "Number of tasks in each status:" 
echo "$TASKS" | jq -r '. | group_by(.status) | map({status: .[0].status, count: length})[] | "> \(.status): \(.count)"'
