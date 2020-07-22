#!/bin/bash

curl -X POST 127.0.0.1:6666/vm/run \
-d '{
"image_name": "msdemo",
"cmdline": "libnode.so keyvaluestore.js",
"read_only": false
}'

curl -X POST 127.0.0.1:6666/vm/run \
-d '{   
"image_name": "msdemo",
"cmdline": "libnode.so db.js 172.17.0.2:9000",
"read_only": false
}'

curl -X POST 127.0.0.1:6666/vm/run \
-d '{   
"image_name": "msdemo",
"cmdline": "libnode.so storage.js 172.17.0.2:9000",
"read_only": false
}'

curl -X POST 127.0.0.1:6666/vm/run \
-d '{   
"image_name": "msdemo",
"cmdline": "libnode.so master.js 172.17.0.2:9000",
"read_only": false
}'

curl -X POST 127.0.0.1:6666/vm/run \
-d '{   
"image_name": "msdemo",
"cmdline": "libnode.so worker.js 172.17.0.2:9000",
"read_only": false
}'
