function urlB64ToUint8Array(base64String){
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i){
	   outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

self.addEventListener('message', function(e){
  if(e.data.p == '1'){
    setTimeout(reg, 100)
  }
});

function postPushReg(sub){
  var rawKey = sub.getKey ? sub.getKey('p256dh') : '';
  var key = rawKey ? btoa(String.fromCharCode.apply(null, new Uint8Array(rawKey))) : '';
  var rawAuthSecret = sub.getKey ? sub.getKey('auth') : '';
  var authSecret = rawAuthSecret ? btoa(String.fromCharCode.apply(null, new Uint8Array(rawAuthSecret))) : '';
  var endpoint = sub.endpoint;
  fetch('/dashboard/registration', {
    method: 'post',
    headers: {'Content-type': 'application/json'},
    body: JSON.stringify({endpoint: sub.endpoint, key: key, authSecret: authSecret}),
  });
}

self.addEventListener('push', function(event){
  var payload = event.data ? JSON.parse(event.data.text()) : {"title": "New Agent!", "body": "A new agent is available"};
  self.registration.showNotification(payload.title, {body: payload.body});
});

function reg(){
  self.registration.pushManager.getSubscription()
  .then(function(sub){
	  if(sub) 
      return;
	  return self.registration.pushManager.subscribe({
      userVisibleOnly: true,
		  applicationServerKey: urlB64ToUint8Array('{{vapidPub}}')}
    ).then(function(sub){
		   postPushReg(sub);
		});
 });
}