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

const port = process.env.MICRO_STORAGE_PORT || process.env.PORT || 9002;

kvEndpoint = require('./common').getKeyvaluestoreEndpoint();
if (!kvEndpoint){
	console.log("Usage: node storage.js <KEYVALUESTORE_ENDOPOINT>")
	console.log("Alternatively, specify MICRO_KEYVALUESTORE_ENDPOINT env variable.")
	process.exit()
}
var memcached = new Memcached(kvEndpoint);

// Get DB IP and try to report it to the key-value registry
setTimeout(registerService, 0, 'storageendpoint', ip.address())

function registerService(service, address) {
	// POST the address to the registry
	memcached.set(service, address + ':' + port, 0, function (err) {
		if(err){
			console.log("Key-value store is not available");
			console.log(err);
			setTimeout(registerService, 1000, service, address);
		}
		else{
			console.log("Storage endpoint registered");
			startService();
		}
	});
}


app.post('/upload/:taskId', (req, res) => {
	var taskId = req.params.taskId

	if (!req.files) {
		res.status(400).send("Image not found")
		return
	}

	var image = req.files.image
	image.mv(imagePath(taskId), (err) => {
		if (err) {
			res.status(500).send(err)
		} else {
			res.send()
		}
	})
})

app.get('/download/:taskId', (req, res) => {
	var taskId = req.params.taskId
	var path = imagePath(taskId)

	res.download(path)
})

function imagePath(taskId) {
	path = __dirname + '/data/storage/' + taskId + '.png'
	return path.replace("//", "/"); // if _dirname is /, then we get //storage/1.png
}

function startService() {
	app.listen(port, (err) => {
		if (err) {
			return console.log('something bad happened', err)
		}

		console.log(`Storage is listening on ${port}`)
	})
}

console.log("Running storage on port: ", port);
console.log("Using keyvaluestore endpoint: ", kvEndpoint);
