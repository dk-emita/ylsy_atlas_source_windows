'use strict';
/* A desktop workbench following Atlas Android 4's color, typography and page language. */
(() => {
  const escHTML = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const dayStamp = () => new Intl.DateTimeFormat('tr-TR',{day:'numeric',month:'long',year:'numeric',weekday:'long'}).format(new Date());
  function compactDate(value){
    if(!value)return '—';
    const d=new Date(String(value).slice(0,10)+'T12:00:00');
    return Number.isNaN(+d)?String(value):new Intl.DateTimeFormat('tr-TR',{day:'2-digit',month:'short'}).format(d);
  }
  function metric(label,value,foot,ico,action){
    const tag=action?'button':'div';
    return `<${tag} class="desk-metric" ${action?`data-act="${action}"`:''}><span class="desk-metric-icon">${icon(ico,20)}</span><span class="desk-metric-copy"><span>${escHTML(label)}</span><strong>${escHTML(value)}</strong><small>${escHTML(foot)}</small></span></${tag}>`;
  }
  function panelHead(title,ico,action=''){
    return `<div class="desk-panel-head"><h2>${icon(ico,19)}${escHTML(title)}</h2>${action}</div>`;
  }
  function dashboard(){
    const o=state.overview||{}, tasks=state.cache.tasks||[], today=new Date().toISOString().slice(0,10);
    const open=tasks.filter(t=>t.status!=='done').sort((a,b)=>(a.due_date||'9999').localeCompare(b.due_date||'9999')).slice(0,5);
    const dates=(typeof upcoming==='function'?upcoming():[]).filter(x=>x.date>=today).slice(0,4);
    const pct=Math.max(0,Math.min(100,Number(o.completion)||0));
    const taskRows=open.length?open.map(x=>`<div class="desk-task"><button class="check-box ${x.status==='done'?'done':''}" data-act="toggle-task" data-id="${x.id}" title="Görevi tamamla">${icon('check',13)}</button><div><strong>${escHTML(x.title)}</strong><small>${escHTML([x.track,x.group_name,x.due_date?`Son tarih ${compactDate(x.due_date)}`:''].filter(Boolean).join(' · ')||'Görev')}</small></div><button class="round-btn" data-edit="tasks" data-id="${x.id}" title="Görevi düzenle">${icon('right',14)}</button></div>`).join(''):'<div class="desk-empty">Açık görev yok. Yol haritandan sıradaki adımı ekleyebilirsin.</div>';
    const dateRows=dates.length?dates.map(x=>`<div class="desk-deadline"><span class="desk-deadline-date">${compactDate(x.date)}</span><span><strong>${escHTML(x.title)}</strong><small>${Math.max(0,daysTo(x.date)||0)} gün kaldı</small></span></div>`).join(''):'<div class="desk-empty">Takip edilen yaklaşan tarih yok.</div>';
    const focus=(state.settings.research_focus||'').trim();
    const cloudConnected=($('#cloud-status-label')?.textContent||'').toLocaleLowerCase('tr-TR').includes('drive');
    return `<section class="desk-dashboard">
      <header class="desk-welcome"><div><span class="eyebrow">YLSY BAŞVURU TAKİBİ</span><h1>Başvuru kontrol paneli</h1><p>Üniversitelerini, görevlerini ve hazırlık ilerlemeni buradan takip et.</p></div><div class="desk-date">${icon('calendar',18)}${dayStamp()}</div></header>
      <div class="desk-metrics">${metric('Üniversite',o.university_count||0,'Kayıtlı kurum','school','add-university')}${metric('Başvuru',o.submitted||0,'Gönderilen program','briefcase','goto-applications')}${metric('Kabul',o.accepted||0,'Olumlu sonuç','check','goto-applications')}${metric('Görev',`${o.done||0} / ${o.total||0}`,'Tamamlanan görev','task','open-roadmap')}</div>
      <div class="desk-work-grid"><section class="desk-panel">${panelHead('Görev takibi','task',`<button class="text-action" data-nav="roadmap">Tüm görevler ${icon('right',14)}</button>`)}<div class="desk-progress-summary"><strong>%${pct}</strong><div class="desk-progress-track"><i style="width:${pct}%"></i></div><span>${o.done||0} / ${o.total||0} görev tamamlandı</span></div><div class="desk-task-list">${taskRows}</div></section>
      <section class="desk-panel">${panelHead('Yaklaşan tarihler','calendar',`<button class="text-action" data-nav="calendar">Takvim ${icon('right',14)}</button>`)}<div class="desk-date-list">${dateRows}</div><button class="btn btn-primary" data-act="add-event" style="width:100%;margin-top:13px">${icon('plus',15)} Etkinlik ekle</button></section></div>
      <section class="desk-panel">${panelHead('Hızlı erişim','sparkle')}<div class="desk-shortcuts"><button class="desk-shortcut" data-act="add-task">${icon('plus',19)} Yeni görev</button><button class="desk-shortcut" data-act="add-university">${icon('school',19)} Üniversite ekle</button><button class="desk-shortcut" data-act="add-advisor">${icon('users',19)} Danışman ekle</button><button class="desk-shortcut" data-act="choose-template">${icon('file',19)} Belge oluştur</button><button class="desk-shortcut" data-act="goto-ielts">${icon('language',19)} İngilizce çalış</button></div></section>
      <div class="desk-lower-grid"><section class="desk-panel"><div class="desk-focus"><span class="desk-focus-mark">${icon('sparkle',21)}</span><span class="desk-focus-copy"><small>ARAŞTIRMA ODAĞIN</small><strong>${escHTML(focus||'Araştırma odağını belirle')}</strong></span><button class="btn btn-small" data-act="set-focus">${icon(focus?'edit':'plus',15)} ${focus?'Düzenle':'Ekle'}</button></div></section><button class="desk-panel desk-drive" data-act="cloud-settings"><span class="desk-drive-icon">${icon('cloud',19)}</span><span class="desk-drive-copy"><strong>${cloudConnected?'Google Drive bağlı':'Yedekleme ayarları'}</strong><small>Otomatik yedekleme durumunu görüntüle</small></span>${icon('right',15)}</button></div>
    </section>`;
  }
  function render(){
    const p=state.nav;
    const views={dashboard,roadmap,guide:guideView,universities,advisors,applications,documents,ielts,vocabulary,administration,calendar,files,notes,resources,settings};
    $('#main').innerHTML=`<div class="page desk-page">${(views[p]||dashboard)()}</div>`;
    document.querySelectorAll('.nav-link').forEach(b=>b.classList.toggle('is-active',b.dataset.nav===p));
    const crumb=$('#breadcrumbs'); if(crumb)crumb.innerHTML=`<span>YLSY ATLAS</span>${icon('chevron')}<b>${escHTML(names[p]||names.dashboard)}</b>`;
  }
  window.dashboard=dashboard;
  window.render=render;
})();
