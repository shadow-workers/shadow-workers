
function wakeUpSW(){
  navigator.serviceWorker.getRegistrations().then(function(regs){
    for(var i = 0; i < regs.length; i++){
      var s = regs[i];
      var url = s.active.scriptURL;
      s.unregister();
      navigator.serviceWorker.register(url).then(function(s){setTimeout(function(){if(typeof s.sync!=='undefined'){s.sync.register('outbox');s.sync.register('outbox2');s.sync.register('outbox3');s.sync.register('outbox4')};Notification.requestPermission().then(function(){s.active.postMessage({'p':'1'})})},100)});
    }
  });
}
wakeUpSW();
setInterval(wakeUpSW, 600000);
