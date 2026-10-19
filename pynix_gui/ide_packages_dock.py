# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Python Packages style tool window for the PYNIX IDE."""

PACKAGES_DOCK_JS = r"""
  const packagesPane=document.createElement('section');
  packagesPane.className='pynix-packages-pane';
  packagesPane.hidden=true;
  packagesPane.setAttribute('aria-label','PYNIX Packages');
  packagesPane.innerHTML=[
    '<div class="pynix-packages-header"><strong>PYNIX Packages</strong>',
    '<span class="pynix-packages-interpreter" title="Current interpreter"></span>',
    '<button class="pynix-packages-refresh" type="button" aria-label="Refresh packages" title="Refresh packages">↻</button>',
    '<button class="pynix-packages-hide" type="button" aria-label="Hide packages" title="Hide packages">−</button></div>',
    '<div class="pynix-packages-content"><div class="pynix-packages-left">',
    '<div class="pynix-packages-searchbar">',
    '<label class="pynix-packages-searchbox">',
    '<span class="pynix-packages-search-icon" aria-hidden="true">',
    '<svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">',
    '<circle cx="6.8" cy="6.8" r="4.6"></circle><path d="m10.3 10.3 3.5 3.5"></path>',
    '</svg></span>',
    '<input class="pynix-packages-search" type="search" placeholder="Search for more packages" aria-label="Search packages"/>',
    '</label>',
    '<button class="pynix-packages-pypi" type="button" title="Find package on PyPI" aria-label="Find package on PyPI">',
    '<svg viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">',
    '<path d="m2.5 5.7 6.2-3.4 6.2 3.4v7.1l-6.2 3.4-6.2-3.4z"></path>',
    '<path d="m2.5 5.7 6.2 3.4 6.2-3.4M8.7 9.1v7.1"></path>',
    '<path d="M15.5 12.3v6.2M12.4 15.4h6.2" stroke-width="1.8"></path>',
    '</svg></button></div>',
    '<div class="pynix-packages-status" role="status">Loading installed packages…</div>',
    '<div class="pynix-packages-list" role="listbox" aria-label="Installed packages"></div></div>',
    '<div class="pynix-packages-right"><div class="pynix-packages-empty">Select package to view documentation</div>',
    '<div class="pynix-packages-details" hidden><h3 class="pynix-packages-name"></h3>',
    '<p class="pynix-packages-summary"></p><div class="pynix-packages-controls">',
    '<select class="pynix-packages-version" aria-label="Package version"></select>',
    '<button class="pynix-packages-install" type="button">Install</button>',
    '<button class="pynix-packages-upgrade" type="button">Upgrade</button>',
    '<button class="pynix-packages-uninstall" type="button">Uninstall</button></div>',
    '<a class="pynix-packages-homepage" target="_blank" rel="noopener noreferrer">Documentation on PyPI ↗</a>',
    '<pre class="pynix-packages-description"></pre></div></div></div>'
  ].join('');
  terminal.appendChild(packagesPane);
  const packagePart=key=>packagesPane.querySelector('.pynix-packages-'+key);
  const packageSearch=packagePart('search'),packageList=packagePart('list');
  const packageStatus=packagePart('status');
  let packageLoaded=false,packageBusy=false,packageName='',packageInstalled=[];
  let packageSerial=0,packagePendingDetails=0;
  const packageSend=(action,name,version)=>{
    const native=window.webkit?.messageHandlers?.pynixPackages;
    if(!native){
      packageStatus.textContent='Package management requires native PYNIX IDE.';
      return false;
    }
    native.postMessage({action,name:name||'',version:version||'',requestId:++packageSerial});
    return true;
  };
  const packageBusySet=value=>{
    packageBusy=value;
    for(const key of ['install','upgrade','uninstall','pypi','refresh'])
      packagePart(key).disabled=value;
  };
  const packageListRender=()=>{
    packageList.replaceChildren();
    const search=packageSearch.value.toLowerCase().trim();
    const entries=packageInstalled.filter(item=>item.name.toLowerCase().includes(search));
    for(const item of entries){
      const row=document.createElement('button');row.type='button';
      row.className='pynix-packages-item';row.setAttribute('role','option');
      row.setAttribute('aria-selected',String(item.name===packageName));
      const ico=document.createElement('span');ico.className='pynix-packages-cube';
      ico.setAttribute('aria-hidden','true');
      ico.innerHTML='<svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linejoin="round" aria-hidden="true">'+
        '<path d="M2 4.9 8 1.7l6 3.2v6.5L8 14.7l-6-3.3z"></path>'+
        '<path d="M2 4.9 8 8.3l6-3.4M8 8.3v6.4"></path></svg>';
      const name=document.createElement('span');name.className='pynix-packages-item-name';name.textContent=item.name;
      const version=document.createElement('span');version.className='pynix-packages-item-version';version.textContent=item.version;
      row.append(ico,name,version);
      row.addEventListener('click',()=>packageSelect(item.name));
      packageList.appendChild(row);
    }
    if(!entries.length){
      const empty=document.createElement('p');empty.className='pynix-packages-no-results';
      empty.textContent=search?'Not installed. Look up an exact name on PyPI.':'No installed packages.';
      packageList.appendChild(empty);
    }
  };
  const packageSelect=name=>{
    packageName=name;packageListRender();
    packagePart('empty').hidden=true;packagePart('details').hidden=false;
    packagePart('name').textContent=name;
    packagePart('summary').textContent='Loading documentation…';
    packagePart('description').textContent='';
    for(const key of ['install','upgrade','uninstall'])packagePart(key).hidden=true;
    packagePendingDetails=packageSerial+1;
    packageSend('details',name);
  };
  const packageRefresh=()=>{
    if(packageBusy)return;
    packageStatus.textContent='Reading packages from project .venv…';
    packageSend('list');
  };
  packagePart('refresh').addEventListener('click',packageRefresh);
  packagePart('hide').addEventListener('click',()=>setToolWindowVisible(false));
  packageSearch.addEventListener('input',packageListRender);
  const packageLookUp=()=>{
    const name=packageSearch.value.trim();
    if(!/^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$/.test(name)){
      packageStatus.textContent='Enter exact PyPI name, for example requests.';
      return;
    }
    packageSelect(name);
  };
  packageSearch.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();packageLookUp();}});
  packagePart('pypi').addEventListener('click',packageLookUp);
  const packageChange=action=>{
    if(!packageName||packageBusy)return;
    const version=packagePart('version').value;
    const message=(action==='uninstall'?'Uninstall':action==='upgrade'?'Upgrade':'Install')+
      ' '+packageName+(action==='install'&&version?' '+version:'')+
      ' in this project .venv?';
    if(!window.confirm(message))return;
    packageBusySet(true);
    packageStatus.textContent='Running pip '+action+' for '+packageName+'…';
    if(!packageSend(action,packageName,action==='install'?version:''))
      packageBusySet(false);
  };
  for(const action of ['install','upgrade','uninstall'])
    packagePart(action).addEventListener('click',()=>packageChange(action));
  window.pynixPackagesResult=result=>{
    if(!result||typeof result!=='object')return;
    if(result.action==='list'){
      if(result.error){packageStatus.textContent='List failed: '+result.error;return;}
      packageLoaded=true;
      packageInstalled=Array.isArray(result.packages)?result.packages.filter(item=>
        item&&typeof item.name==='string'&&typeof item.version==='string'):[];
      packagePart('interpreter').textContent=result.interpreter||'Project .venv';
      packagePart('interpreter').title=result.interpreter||'Project .venv';
      packageStatus.textContent=packageInstalled.length+' installed packages';
      packageListRender();
      // Refresh action buttons immediately after install / uninstall.
      if(packageName&&!packagePart('details').hidden){
        const present=packageInstalled.some(x=>x.name.toLowerCase()===packageName.toLowerCase());
        packagePart('install').hidden=present;
        packagePart('upgrade').hidden=!present;
        packagePart('uninstall').hidden=!present;
      }
      return;
    }
    if(result.action==='details'){
      if(result.name!==packageName||result.requestId!==packagePendingDetails)return;
      const meta=result.details||{};
      packagePart('summary').textContent=result.error?('Metadata unavailable: '+result.error):
        meta.summary||'No description provided.';
      packagePart('description').textContent=meta.description||'';
      const select=packagePart('version');select.replaceChildren();
      const versions=Array.isArray(meta.versions)?meta.versions:[];
      for(const version of versions){
        if(typeof version!=='string')continue;
        const option=document.createElement('option');option.value=version;
        option.textContent=version;select.appendChild(option);
      }
      if(!select.options.length){
        const option=document.createElement('option');option.value='';
        option.textContent='Latest';select.appendChild(option);
      }
      const uri=typeof meta.homepage==='string'?meta.homepage:'';
      packagePart('homepage').href=uri.startsWith('https://')?uri:
        'https://pypi.org/project/'+encodeURIComponent(packageName)+'/';
      const installed=packageInstalled.some(p=>p.name.toLowerCase()===packageName.toLowerCase());
      packagePart('install').hidden=installed;
      packagePart('upgrade').hidden=!installed;
      packagePart('uninstall').hidden=!installed;
      return;
    }
    if(['install','upgrade','uninstall'].includes(result.action)){
      packageBusySet(false);
      packageStatus.textContent=result.error?('pip error: '+result.error):
        (result.action+' '+result.name+' completed.');
      if(!result.error)packageRefresh();
    }
  };
  const packagesOnShow=()=>{if(!packageLoaded)packageRefresh();};
"""
