const express = require('express')  
var bodyParser = require('body-parser');
var fileUpload = require('express-fileupload')
var request = require('request')
var ip = require('ip');
var os = require('os');
var Memcached = require('memcached');

const app = express()  
app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({ extended: true })); // support encoded bodies
app.use(fileUpload())

const port = process.env.MICRO_MASTER_PORT || process.env.PORT || 9003;

var dbEndpoint
var storageEndpoint

kvEndpoint = require('./common').getKeyvaluestoreEndpoint();
if (!kvEndpoint){
	console.log("Usage: node master.js <KEYVALUESTORE_ENDOPOINT>")
	console.log("Alternatively, specify MICRO_KEYVALUESTORE_ENDPOINT env variable.")
	process.exit()
}
var memcached = new Memcached(kvEndpoint);

// Get Master IP and try to report it to the key-value registry
setTimeout(registerService, 0, 'masterendpoint', ip.address())

function registerService(service, address) {
	// POST the address to the registry
	memcached.set(service, address + ':' + port, 0, function (err) {
		if(err){
			console.log("Key-value store is not available");
			console.log(err);
			setTimeout(registerService, 1000, service, address);
		}
		else{
			console.log("Master endpoint registered");
			getServiceEndpoints();
		}
	});
}

app.post('/task', (req, res) => {
	// Make a new task.
	request.post({uri: dbEndpoint + '/task'}, (dbError, dbResponse, dbBody) => {
		if (!dbError && dbResponse.statusCode == 200) {
			// If the task was successful, we should also store the image in storage.
			taskId = dbBody

			var formData = {
				image: req.files.image.data
			}

			var postImage = {
				uri: storageEndpoint + '/upload/' + taskId,
				formData: formData
			}

			request.post(postImage, (storageError, storageResponse, storageBody) => {
				if (!storageError && storageResponse.statusCode == 200) {
					// Since we have the confirmation that the requested image is successfully
					// stored, we can change the status of the task to "ready"
					request.post({uri: dbEndpoint + '/task/' + taskId + '/ready'})
					res.send()
				} else {
					res.status(500).send("Error uploading image: " + storageError)
				}
			})
		} else {
			res.status(500).send("Error creating task: " + dbError)
		}
	})
})

app.get('/task/next', (req, res) => {
	request.get({uri: dbEndpoint + '/task/next'}).pipe(res)
})

app.get('/task/:taskId/download', (req, res) => {
	var taskId = req.params.taskId

	// Request a download from the storage.
	request.get({uri: storageEndpoint + '/download/' + taskId}).pipe(res)
})

app.post('/task/:taskId/finish', (req, res) => {
	var taskId = req.params.taskId

	request.post({uri: dbEndpoint + '/task/' + taskId + '/finish'}).pipe(res)
})

app.get('/task/:taskId/ready', (req, res) => {
	var taskId = req.params.taskId

	request.get({uri: dbEndpoint + '/task/' + taskId}, (dbError, dbStatus, dbBody) => {
		if (!dbError && dbStatus.statusCode == 200) {
			data = JSON.parse(dbBody)
			res.send(data.state == 2)
		} else {
			res.status(dbStatus.statusCode).send(dbError)
		}
	})
})

function getServiceEndpoints() {
	if (!dbEndpoint) {
		memcached.get('dbendpoint', function (err, data) {
			if(err){
				console.log("Error getting Database service.")
				console.log(err);
			}
			else{
				dbEndpoint = 'http://' + data
			}
		});
	}

	if (!storageEndpoint) {
		memcached.get('storageendpoint', function (err, data) {
			if(err){
				console.log("Error getting Storage service.")
				console.log(err);
			}
			else{
				storageEndpoint = 'http://' + data
			}
		});
	}

	if (dbEndpoint && storageEndpoint) {
		startService()
	} else {
		setTimeout(getServiceEndpoints, 1000)
	}
}

function startService() {
	app.listen(port, (err) => {
		if (err) {
			return console.log('something bad happened', err)
		}

		console.log(`Master is listening on ${port}`)
	})
}

console.log("Running master on port: ", port);
console.log("Using keyvaluestore endpoint: ", kvEndpoint);
