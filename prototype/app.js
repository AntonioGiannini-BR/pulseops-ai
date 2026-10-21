/* PulseOps AI — Parte 1. Front-end fictício sem APIs e sem IA real. */
'use strict';
const original = [
  { id: 1, title: 'Sistema de vendas indisponível', category: 'Sistemas', priority: 'critica', status: 'em_atendimento', assignee: 'Rafael Costa', sla: 'atrasado' },
  { id: 2, title: 'Erro de acesso ao portal financeiro', category: 'Acessos', priority: 'alta', status: 'em_triagem', assignee: 'Bruna Nascimento', sla: 'em_dia' },
  { id: 3, title: 'Impressora do setor não responde', category: 'Equipamentos', priority: 'baixa', status: 'aberto', assignee: 'Rafael Costa', sla: 'em_dia' },
  { id: 4, title: 'Oscilação na rede corporativa', category: 'Infraestrutura', priority: 'alta', status: 'resolvido', assignee: 'Rafael Costa', sla: 'dentro_do_prazo' },
  { id: 5, title: 'Integração do ERP falhando', category: 'Sistemas', priority: 'media', status: 'resolvido', assignee: 'Bruna Nascimento', sla: 'fora_do_prazo' },
  { id: 6, title: 'Solicitação de novo monitor', category: 'Equipamentos', priority: 'baixa', status: 'aberto', assignee: 'Não atribuído', sla: 'em_dia' },
  { id: 7, title: 'Conta bloqueada no sistema interno', category: 'Acessos', priority: 'media', status: 'fechado', assignee: 'Bruna Nascimento', sla: 'dentro_do_prazo' },
  { id: 8, title: 'Painel operacional sem atualização', category: 'Sistemas', priority: 'alta', status: 'aberto', assignee: 'Não atribuído', sla: 'em_dia' }
];
const tickets = [...original];
const $ = (id) => document.getElementById(id);
const labelStatus = {aberto:'Aberto',em_triagem:'Em triagem',em_atendimento:'Em atendimento',resolvido:'Resolvido',fechado:'Fechado'};
const labelPriority = {critica:'Crítica',alta:'Alta',media:'Média',baixa:'Baixa'};
const colors = {critica:'#eb8a54', alta:'#447af2', media:'#a38afa', baixa:'#39bc9a'};
const priorities = ['critica','alta','media','baixa'];
let currentPage = 'overview';
function text(v){ return String(v).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function renderRow(t){return `<tr><td><span class="ticket-id">INC-${String(t.id).padStart(6,'0')}</span></td><td><span class="ticket-title">${text(t.title)}</span><span class="ticket-subtitle">Demo • ${t.sla === 'atrasado'?'SLA vencido':t.sla === 'fora_do_prazo'?'Fora do prazo': 'Operação'}</span></td><td>${text(t.category)}</td><td><span class="pill p-${t.priority}">${labelPriority[t.priority]}</span></td><td><span class="pill s-${t.status}">${labelStatus[t.status]}</span></td><td>${text(t.assignee)}</td></tr>`;}
function renderSummary(){
  const total = tickets.length, pending=tickets.filter(x=>!['resolvido','fechado'].includes(x.status)).length, completed=total-pending,late=tickets.filter(x=>['atrasado','fora_do_prazo'].includes(x.sla)).length;
  $('kpi-total').textContent=total; $('kpi-pending').textContent=pending; $('kpi-complete').textContent=completed; $('kpi-sla').textContent=late;
  $('sidebar-count').textContent=total; $('donut-total').textContent=total;
  const categoryNames=['Sistemas','Acessos','Equipamentos','Infraestrutura','Outros'];
  const counts=categoryNames.map(n=>({name:n,value:tickets.filter(x=>x.category===n).length}));
  const max=Math.max(1,...counts.map(x=>x.value));
  $('category-chart').innerHTML=counts.map(x=>`<div class="chart-row"><span>${x.name}</span><div class="bar-track"><div class="bar-fill" style="width:${100*x.value/max}%"></div></div><strong>${x.value}</strong></div>`).join('');
  const priorityCounts=priorities.map(p=>tickets.filter(x=>x.priority===p).length);
  let pct=0;const segments=[];
  priorities.forEach((p,i)=>{const next=pct + (total?priorityCounts[i]/total*100:0);segments.push(`${colors[p]} ${pct}% ${next}%`);pct=next;});
  $('donut').style.background=total?`conic-gradient(${segments.join(',')})`:'#e6ebf4';
  $('priority-legend').innerHTML=priorities.map((p,i)=>`<div class="legend-line"><span class="legend-name"><span class="dot" style="background:${colors[p]}"></span>${labelPriority[p]}</span><strong>${priorityCounts[i]}</strong></div>`).join('');
  $('recent-tickets').innerHTML=tickets.slice().sort((a,b)=>b.id-a.id).slice(0,5).map(renderRow).join('');
  renderTable();
}
function renderTable(){
  const search=$('search').value.trim().toLowerCase(), status=$('filter-status').value;
  const filtered=tickets.filter(t=>(status==='todos'||t.status===status)&&[t.title, t.category, t.assignee, `inc-${String(t.id).padStart(6,'0')}`].some(s=>s.toLowerCase().includes(search))).sort((a,b)=>b.id-a.id);
  $('all-tickets').innerHTML=filtered.length?filtered.map(renderRow).join(''):'<tr><td colspan="6">Nenhum chamado encontrado.</td></tr>';
  $('table-message').textContent=`${filtered.length} chamado(s) exibido(s) · Dados da demonstração`;
}
function openPage(name){
  currentPage=name;
  document.querySelectorAll('.page').forEach(e=>e.classList.toggle('active',e.id===`page-${name}`));
  document.querySelectorAll('.nav-item').forEach(e=>e.classList.toggle('active',e.dataset.page===name));
  $('breadcrumb').textContent={overview:'Visão geral',tickets:'Chamados',teams:'Equipes',ai:'Central de IA'}[name];
  $('sidebar').classList.remove('open');
  window.scrollTo({top:0,behavior:'instant'});
}
function closeModal(){ $('modal').classList.remove('visible');$('modal').setAttribute('aria-hidden','true'); }
function openModal(){ $('modal').classList.add('visible');$('modal').setAttribute('aria-hidden','false');$('new-title').focus(); }
function toast(message){const t=$('toast');t.textContent=message;t.classList.add('visible');window.clearTimeout(toast.timeout);toast.timeout=window.setTimeout(()=>t.classList.remove('visible'),3200);}
document.querySelectorAll('[data-page]').forEach(b=>b.addEventListener('click',()=>openPage(b.dataset.page)));
document.querySelectorAll('[data-open-modal]').forEach(b=>b.addEventListener('click',openModal));
$('modal-close').addEventListener('click',closeModal);$('modal-cancel').addEventListener('click',closeModal);
$('modal').addEventListener('mousedown',e=>{if(e.target===$('modal'))closeModal();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});
$('mobile-menu').addEventListener('click',()=>$('sidebar').classList.toggle('open'));
$('search').addEventListener('input',renderTable);$('filter-status').addEventListener('change',renderTable);
$('ticket-form').addEventListener('submit',e=>{
  e.preventDefault(); const title=$('new-title').value.trim(),desc=$('new-description').value.trim();
  if(!title||!desc){toast('Preencha título e descrição.');return;}
  const id=Math.max(0,...tickets.map(x=>x.id))+1;
  tickets.push({id,title,category:$('new-category').value,priority:$('new-priority').value,status:'aberto',assignee:'Não atribuído',sla:'em_dia'});
  e.target.reset();closeModal();renderSummary();openPage('tickets');toast(`INC-${String(id).padStart(6,'0')} criado nesta demonstração.`);
});
$('export-csv').addEventListener('click',()=>{
  const header=['ID','Título','Categoria','Prioridade','Status','Responsável'];
  const csvCell = (v) => { const raw=String(v); const safe=/^[=+\-@\t\r]/.test(raw) ? '\''+raw : raw; return '"'+safe.replace(/"/g,'""')+'"'; };
  const csv=[header,...tickets.map(t=>[`INC-${String(t.id).padStart(6,'0')}`,t.title,t.category,labelPriority[t.priority],labelStatus[t.status],t.assignee])].map(row=>row.map(csvCell).join(';')).join('\r\n');
  const blob=new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='pulseops-chamados-demo.csv';document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);toast('CSV exportado (dados fictícios).');
});
renderSummary();
