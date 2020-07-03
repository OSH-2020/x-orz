module.exports = {
	getKeyvaluestoreEndpoint: function(){
		if (process.argv.length == 3) {	    
		    return process.argv[2];
		} else if (process.env.MICRO_KEYVALUESTORE_ENDPOINT) {
		    return process.env.MICRO_KEYVALUESTORE_ENDPOINT;
		}
		return false;
	}
};
