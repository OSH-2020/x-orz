const express = require('express')  
var bodyParser = require('body-parser');
var request = require('request')
var os = require('os');
var ip = require('ip');
var Memcached = require('memcached');

const app = express()  
app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({ extended: true })); // support encoded bodies

const port = process.env.MICRO_DB_PORT || process.env.PORT || 9001;

var dataStore = {}
var oldestNotFinishedTask = 0

kvEndpoint = require('./common').getKeyvaluestoreEndpoint();
if (!kvEndpoint){
	console.log("Usage: node db.js <KEYVALUESTORE_ENDOPOINT>")
	console.log("Alternatively, specify MICRO_KEYVALUESTORE_ENDPOINT env variable.")
	process.exit()
}
var memcached = new Memcached(kvEndpoint);

// Get DB IP and try to report it to the key-value registry
setTimeout(registerService, 0, 'dbendpoint', ip.address())

function registerService(service, address) {
	// POST the address to the registry
	memcached.set(service, address + ':' + port, 0, function (err) {
		if(err){
			console.log("Key-value store is not available");
			console.log(err);
			setTimeout(registerService, 1000, service, address);
		}
		else{
			console.log("Database endpoint registered");
			startService();
		}
	});
}

app.post('/task', (req, res) => {  
	var taskId = dataStoreSize()
	dataStore[taskId] = {
		"id": taskId,
		state: -1
	}

	res.send("" + taskId)
})

app.get('/task/next', (req, res) =>{
	for (var i = 0; i < dataStoreSize(); i++) {
		var state = dataStore[i]['state']
		if (state != 0) {
			continue
		}

		// Ensure tasks are processed on time. In case after 20s the status is not finished.
		// reset it to "ready".
		setTimeout(() => {
			if (dataStore[i]['state'] != 2) {
				dataStore[i]['state'] = 0
			}
		}, 20000)

		dataStore[i]['state'] = 1
		res.send(dataStore[i])
		return
	}

	res.status(404).send({'id': -1, 'state': 0})
})

app.get('/task/:taskId', (req, res) => {
	var taskId = req.params.taskId

	if (taskId in dataStore) {
		res.send(dataStore[taskId])
	} else {
		res.status(404).send("Task not found")
	}
})

app.post('/task/:taskId/ready', (req, res) => {
	var taskId = req.params.taskId
	updateTaskState(taskId, 0, res)
})

app.post('/task/:taskId/finish', (req, res) => {
	var taskId = req.params.taskId
	updateTaskState(taskId, 2, res)
})

function updateTaskState(taskId, state, res) {
	if (taskId in dataStore) {
		dataStore[taskId]['state'] = state
		res.send()
	} else {
		res.status(404).send("Task not found")
	}
}

function dataStoreSize() {
	return Object.keys(dataStore).length
}

function startService() {
	app.listen(port, (err) => {
		if (err) {
			return console.log('something bad happened', err)
		}

		console.log(`Database is listening on ${port}`)
	})
}

console.log("Running db on port: ", port);
console.log("Using keyvaluestore endpoint: ", kvEndpoint);
