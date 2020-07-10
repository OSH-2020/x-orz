#!/bin/bash

# Usage: 
#
# ./bin/upload_batch.sh KEYVALUE_ENDPOINT IMAGE_PATH N_REPETITIONS
#

MASTER_ENDPOINT=$1

echo "Uploading to $MASTER_ENDPOINT"

for i in $(seq 1 $3)
do 
	curl -X POST -F "image=@$2" http://$MASTER_ENDPOINT/task
done
