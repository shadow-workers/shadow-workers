function templateModuleLogic(){
  // do stuff
  sendModuleResultToC2('template', "whatever");
  deregisterModule('template');
}

var templateStatus;

// wakes up the DB
WriteIDB("template_init", 1);

// save module in list of extra_modules
registerModule('template');

// check last module status
new Promise((res, rej) => {
  ReadIDB("template", rej);
}).catch(function(p){
  if(p == undefined){
    templateStatus = 1; // DEFAULT value
  }else{
    templateStatus = p; // previous value
  }
  templateModuleLogic();
});
