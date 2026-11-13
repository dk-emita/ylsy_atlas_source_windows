'use strict';
/* Google account screen and Drive status for YLSY Atlas 4.0.0.
   Keep the publisher OAuth client and existing authorization flow. */
(() => {
  const TOKEN = new URL(location.href).searchParams.get('token') || '';
  const ROOT = document.getElementById('account-root');
  const escapeHTML = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let info=null, lastChange=-1, view='home', folderStack=[{name:'Drive ana klasörü',id:'root'}];
  let busy=false, awaitingLogin=false, folderPrompted=false;
  const http=async (path, method='GET', body) => {
    const init={method, headers:{'X-Atlas-Token':TOKEN}};
    if(body!==undefined){init.headers['Content-Type']='application/json';init.body=JSON.stringify(body)}
    const response=await fetch('/api/cloud/'+path,init);
    const result=await response.json();
    if(!response.ok) throw new Error(result.error || 'Drive işlemi başarısız');
    return result;
  };
  const message=(text,bad=false)=>{
    const msg=document.getElementById('cloud-message');
    if(msg){msg.textContent=text;msg.classList.toggle('cloud-error',bad)}
  };
  const panel=(title,body)=>{
    ROOT.innerHTML=`<div class="cloud-shade" role="presentation"><section class="cloud-panel" role="dialog" aria-modal="true" aria-label="${escapeHTML(title)}"><header class="cloud-panel-head"><div class="cloud-brand"><span class="cloud-brand-mark">A</span><div><span>YLSY ATLAS · GOOGLE DRIVE</span><h2>${escapeHTML(title)}</h2></div></div><button type="button" data-cloud="close" class="cloud-close" aria-label="Kapat">×</button></header><div class="cloud-panel-body">${body}<p id="cloud-message" class="cloud-message" role="status"></p></div></section></div>`;
  };
  function home(startup=false){
    view='home';
    const summary=info?.status || 'Google hesabı bağlı değil';
    const step=info?.connected?3:info?.authorization_ready?2:1;
    const steps=`<div class="cloud-stepper" aria-label="Bağlantı adımları"><span class="${step>=1?'is-current':''}"><i>1</i> Hesap</span><b></b><span class="${step>=2?'is-current':''}"><i>2</i> Klasör</span><b></b><span class="${step>=3?'is-current':''}"><i>3</i> Otomatik yedekleme</span></div>`;
    let status=`<div class="cloud-status-card ${info?.connected?'is-connected':''}"><span class="cloud-status-icon">${info?.connected?'✓':'↗'}</span><div><strong>${escapeHTML(info?.connected?'Otomatik Drive yedeklemesi açık':summary)}</strong><small>${info?.connected?'Değişiklikler anında gönderilir; çevrimdışı kayıtlar bağlantı gelince aktarılır':info?.authorization_ready?'Google hesabı bağlandı. Bir Drive konumu seçerek kurulumu tamamla.':'Google hesabı henüz bağlanmadı'}</small></div></div>`;
    const firstSetup = startup && !info?.connected;
    const explain = firstSetup ? '<p class="cloud-intro">Google hesabını bağla; Atlas değişikliklerini Drive’a otomatik yedeklesin. İnternet yokken kayıtların bu cihazda güvenle bekler.</p>' : '<p class="cloud-intro">Google hesabı ve yedekleme konumunu buradan yönet. Eşitleme arka planda otomatik çalışır.</p>';
    panel(firstSetup?'Çalışmalarını nasıl kaydedelim?':'Google Drive ve hesap',explain+status+steps+
     `<button data-cloud="connect" class="cloud-button primary" ${info?.configured && info?.status!=='Google giriş sayfası açılıyor' ? '' : 'disabled'}>${info?.status==='Google giriş sayfası açılıyor' ? 'Google hesabı bekleniyor…' : info?.authorization_ready ? 'Google hesabını değiştir' : 'Google hesabını bağla'}</button>
      ${info?.authorization_ready?'<button data-cloud="folders" class="cloud-button primary">Google Drive klasörü seç</button>':''}
      ${info?.connected?'<button data-cloud="folders" class="cloud-button quiet">Yedekleme klasörünü değiştir</button><button data-cloud="disconnect" class="cloud-button quiet">Hesabın bağlantısını kaldır</button>':''}
      ${firstSetup?'<button data-cloud="skip" class="cloud-button quiet">Google hesabını bağlamadan devam et</button>':''}`+
      `<p class="cloud-note">${/Android/i.test(navigator.userAgent)?'Google hesabın güvenli sistem tarayıcısında açılır.':'Google hesabın varsayılan tarayıcıda güvenli Google giriş sayfasında açılır.'} Atlas parolanı istemez; bağlantı resmi Google OAuth akışını kullanır.</p>`);
    if(info?.error) message(info.error,true);
    else if(info && !info.configured) message('Google OAuth yapılandırması bulunamadı. Program yöneticisine bildirin.',true);
  }
  async function folders(){
    view='folders';
    const where=folderStack.at(-1);
    panel('Google Drive klasörü seç',`<p>${escapeHTML(folderStack.map(x=>x.name).join(' / '))}</p><div class="cloud-folder-list" id="cloud-folder-list">Klasörler alınıyor…</div><button data-cloud="back" class="cloud-button quiet" ${folderStack.length===1?'disabled':''}>Üst klasöre dön</button><button data-cloud="choose" class="cloud-button primary" disabled>Burada “YLSY Atlas” klasörü oluştur veya kullan</button>`);
    try{
      let items=await http('folders?parent='+encodeURIComponent(where.id));
      if(view!=='folders'||folderStack.at(-1).id!==where.id)return;
      document.getElementById('cloud-folder-list').innerHTML=items.length?items.map(x=>`<button class="cloud-folder" data-cloud="enter" data-id="${escapeHTML(x.id)}" data-label="${escapeHTML(x.name)}">📁 ${escapeHTML(x.name)}</button>`).join(''):'<span class="cloud-note">Bu konumda alt klasör yok.</span>';
      ROOT.querySelector('[data-cloud="choose"]').disabled=false;
    }catch(e){
      if(view!=='folders')return;
      document.getElementById('cloud-folder-list').innerHTML='<button data-cloud="retry-folders" class="cloud-button">Klasörleri yeniden yükle</button>';
      message(e.message,true);
    }
  }
  async function refresh(){
    try{
      const newest=await http('status');
      const old=info;
      info=newest;
      // A completed Drive setup is an acknowledged first-run choice.
      // Never reopen the account window on every launch for connected users.
      if(info.connected && !info.startup_shown) info=await http('skip','POST');
      const label=document.getElementById('cloud-status-label');
      if(label){const base=info.mode==='oauth'?(info.synchronized?'Google Drive ile eşitlendi':info.status):info.authorization_ready?'Google hesabı doğrulandı · klasör seç':'Yerel çalışma';label.textContent=info.pending_changes?`${base} · ${info.pending_changes} değişiklik sırada`:base;}
      const profile=document.getElementById('profile-button');
      if(profile){profile.classList.toggle('cloud-connected',info.connected);profile.title=info.status;}
      if(old && info.change_number!==lastChange && view==='home' && !busy && ROOT.childElementCount){
        const wasStartup=ROOT.getAttribute('data-startup')==='true';
        home(wasStartup);
      }
      lastChange=info.change_number;
      if(!old && !info.startup_shown){
        home(true);
        ROOT.setAttribute('data-startup','true');
      }
      // The OAuth callback only confirms that Google returned to localhost.
      // Wait for the actual token exchange and open the native Atlas folder picker.
      if(!busy && info.authorization_ready && !info.connected && !info.error && view!=='folders' &&
         (awaitingLogin || (info.status.includes('Drive klasörü seçiniz') && !folderPrompted))){
        awaitingLogin=false;
        folderPrompted=true;
        folderStack=[{name:'Drive ana klasörü',id:'root'}];
        await folders();
        return;
      }
      if(awaitingLogin && info.error){
        awaitingLogin=false;
        home(ROOT.getAttribute('data-startup')==='true');
        message('Google bağlantısı tamamlanamadı: '+info.error,true);
      }
      if(info.status.includes('alındı') && old && newest.change_number!==old.change_number && !document.getElementById('doc-editor')){
        // Reload only once per status revision, so a newly downloaded remote snapshot is rendered.
        const key=`atlas-cloud-refreshed-${newest.change_number}`;
        if(!sessionStorage.getItem(key)){sessionStorage.setItem(key,'1');location.reload();}
      }
    }catch(e){
      const label=document.getElementById('cloud-status-label');if(label)label.textContent='Yerel çalışma';
    }
  }
  async function go(action,button){
    if(busy)return;
    busy=true; if(button)button.disabled=true;
    try{
      if(action==='close') {if(ROOT.getAttribute('data-startup')==='true') info=await http('skip','POST');ROOT.replaceChildren();view='closed';}
      if(action==='skip') {info=await http('skip','POST'); ROOT.replaceChildren();view='closed';}
      if(action==='connect') {
        if(!info.configured){ message('Google bağlantısı bu paket içinde yapılandırılmamış.',true); return;}
        if(ROOT.getAttribute('data-startup')==='true') info=await http('skip','POST');
        awaitingLogin=true;
        folderPrompted=false;
        info=await http('connect','POST');home();
        message('Google hesabını varsayılan tarayıcında seç. Giriş tamamlandığında Drive klasörleri burada otomatik açılacak.');
      }
      if(action==='folders'){folderPrompted=true;folderStack=[{name:'Drive ana klasörü',id:'root'}];await folders();}
      if(action==='retry-folders'){await folders();}
      if(action==='disconnect'){if(!confirm('Google Drive bağlantısı ayrılsın mı? Kaydedilmemiş yerel veriler silinmez.'))return;info=await http('disconnect','POST');home();}
      if(action==='back') {if(folderStack.length>1)folderStack.pop();await folders();}
      if(action==='enter') {folderStack.push({id:button.dataset.id,name:button.dataset.label});await folders();}
      if(action==='choose') {info=await http('select-folder','POST',{parent:folderStack.at(-1).id});info=await http('skip','POST');awaitingLogin=false;folderPrompted=true;home();message('Yedekleme konumu kaydedildi. Otomatik Drive yedeklemesi açık.')}
    }catch(e){message(e.message,true)}
    finally{busy=false;if(button?.isConnected)button.disabled=false;}
  }
  ROOT.addEventListener('click',e=>{
    const b=e.target.closest('[data-cloud]');
    if(b)go(b.dataset.cloud,b);
    else if(e.target.classList.contains('cloud-shade')){ROOT.replaceChildren();view='closed';}
  });
  document.getElementById('profile-button').addEventListener('click',()=>{ROOT.setAttribute('data-startup','false');home(false)});
  window.addEventListener('keydown',e=>{if(e.key==='Escape'&&ROOT.childElementCount){ROOT.replaceChildren();view='closed';}});
  let lastActive=null;
  async function editHeartbeat(){
    const active=!!document.querySelector('#doc-editor, #modal-root form');
    if(active || lastActive!==active){
      lastActive=active;
      try{await http('editor-active','POST',{active})}catch{}
    }
  }
  document.addEventListener('input',()=>{if(document.querySelector('#doc-editor, #modal-root form')) editHeartbeat()});
  editHeartbeat();setInterval(editHeartbeat,3000);
  refresh();setInterval(refresh,1400);
})();
