'use strict';
const $ = id => document.getElementById(id);
const num = value => value === '' || value == null ? null : Number(value);
const fold = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const dateText = value => value ? new Intl.DateTimeFormat('es', {dateStyle:'medium',timeZone:'UTC'}).format(new Date(value+'T00:00:00Z')) : 'Fecha desconocida';
const money = (value,currency='EUR') => value === null ? 'Precio desconocido' : new Intl.NumberFormat('es',{style:'currency',currency:currency||'EUR'}).format(value);
function node(tag, text, className) { const el=document.createElement(tag); if(text!==undefined) el.textContent=text; if(className)el.className=className; return el; }
function link(url, text) { try { const u=new URL(url); if(!['https:','http:'].includes(u.protocol))return null; const a=node('a',text,'shop');a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';return a;}catch{return null;} }
function models(data) {
  const groups=new Map();
  for(const r of data.registros){if(!groups.has(r.cafe_id))groups.set(r.cafe_id,[]);groups.get(r.cafe_id).push(r);}
  return [...groups.entries()].map(([id,rows])=>{
    const purchases=rows.filter(r=>r.tipo!=='cata').map(r=>({...r,fecha:r.fecha_compra})).reverse().sort((a,b)=>b.fecha.localeCompare(a.fecha));
    const reviews=rows.filter(r=>r.puntuacion!=='').map(r=>({...r,fecha:r.fecha_valoracion})).reverse().sort((a,b)=>b.fecha.localeCompare(a.fecha));
    const latest=purchases[0],review=reviews[0],base=latest||rows.at(-1);
    return {...base,id,rows,purchases,reviews,latest,review,rating:review?num(review.puntuacion):null,price:latest?num(latest.precio):null,activity:rows.flatMap(r=>[r.fecha_compra,r.fecha_valoracion]).sort().at(-1)||'',search:fold(rows.map(r=>[r.nombre,r.tienda,r.notas_web,r.notas_usuario].join(' ')).join(' '))};
  });
}
function filtered(items, f) {
  const min=num(f.min),max=num(f.max);
  return items.filter(c=>{
    if(f.search&&!c.search.includes(fold(f.search)))return false;
    if(f.rating==='unrated'&&c.rating!==null)return false;
    if(!['all','unrated'].includes(f.rating)&&(c.rating===null||c.rating<Number(f.rating)))return false;
    if((min!==null||max!==null)&&c.price===null)return false;
    if(min!==null&&c.price<min || max!==null&&c.price>max)return false;
    if(f.from||f.to){const dates=(f.kind==='compra'?c.purchases:c.reviews).map(r=>r.fecha);if(!dates.some(d=>d&&(!f.from||d>=f.from)&&(!f.to||d<=f.to)))return false;}
    return true;
  }).sort((a,b)=>{
    if(f.sort==='name')return a.nombre.localeCompare(b.nombre,'es');
    if(f.sort==='recent')return b.activity.localeCompare(a.activity)||a.nombre.localeCompare(b.nombre,'es');
    const field=f.sort==='rating'?'rating':'price', direction=f.sort==='cheap'?1:-1;
    if(a[field]===null||b[field]===null)return a[field]===b[field]?a.nombre.localeCompare(b.nombre,'es'):a[field]===null?1:-1;
    return direction*(a[field]-b[field])||a.nombre.localeCompare(b.nombre,'es');
  });
}
function card(c) {
  const el=node('article',undefined,'card'),top=node('div',undefined,'card-top'),heading=node('div');
  heading.append(node('p',c.tienda||'Mi colección','origin'),node('h3',c.nombre));
  const score=node('span',c.rating===null?'Sin valorar':String(c.rating).replace('.',','),'score'+(c.rating===null?' pending':''));
  if(c.rating!==null)score.append(node('small','/ 5'));top.append(heading,score);el.append(top);
  if(c.review)el.append(node('blockquote',c.review.notas_usuario||'Sin comentario.','quote'),node('p','Valoración del '+dateText(c.review.fecha_valoracion),'meta'));
  else el.append(node('p','Todavía sin valoración.','quote'));
  if(c.latest&&c.latest.puntuacion==='')el.append(node('p',c.review?.tipo==='cata'?'Valoración registrada; compra concreta sin confirmar.':'Última compra o muestra pendiente de valoración.','status'));
  const priceRow=node('div',undefined,'price-row'),price=node('span',c.latest?.tipo==='muestra'&&c.price===null?'Muestra regalada':money(c.price),'price');
  if(c.latest?.gramos)price.append(node('small',c.latest.gramos+' g'));priceRow.append(price);
  const shop=link(c.url,'Ver en '+(c.tienda||'la tienda'));if(shop)priceRow.append(shop);el.append(priceRow);
  const details=node('details',undefined,'details');details.append(node('summary','Notas de cata e historial'));
  for(const r of [...c.rows].reverse()){
    details.append(node('p',r.tipo==='cata'?'Cata · compra concreta sin confirmar':(r.tipo==='muestra'?'Muestra':'Compra')+' · '+dateText(r.fecha_compra),'detail-title'));
    if(r.precio!=='')details.append(node('p',money(num(r.precio))+(r.gramos?' / '+r.gramos+' g':'')));
    if(r.puntuacion!=='')details.append(node('p',r.puntuacion.replace('.',',')+'/5 · '+dateText(r.fecha_valoracion)));
    if(r.notas_usuario)details.append(node('p','Mi opinión','detail-title'),node('p',r.notas_usuario));
    if(r.notas_web)details.append(node('p','Notas comerciales conservadas','detail-title'),node('p',r.notas_web));
    if(r.detalles)details.append(node('p','Contexto','detail-title'),node('p',r.detalles));
  }
  el.append(details);return el;
}
async function start(){
  try{
    const response=await fetch('datos.json');if(!response.ok)throw new Error('No se pudo cargar la colección.');const data=await response.json(),items=models(data);
    $('title').textContent=data.coleccion.titulo;$('author').textContent=data.coleccion.autor?'EL CUADERNO DE '+data.coleccion.autor.toUpperCase():'MI COLECCIÓN';$('description').textContent=data.coleccion.descripcion;document.title=data.coleccion.titulo+' · Café de Datos';
    for(const [count,label] of [[items.length,'cafés'],[data.registros.filter(r=>r.puntuacion!=='').length,'valoraciones'],[data.registros.filter(r=>r.tipo!=='cata').length,'compras y muestras']]){const s=node('div',undefined,'stat');s.append(node('strong',String(count)),node('span',label));$('summary').append(s);}
    function render(){const f={search:$('search').value.trim(),rating:$('rating').value,min:$('min-price').value,max:$('max-price').value,kind:$('date-kind').value,from:$('from').value,to:$('to').value,sort:$('sort').value};const shown=filtered(items,f);$('cards').replaceChildren(...shown.map(card));$('count').textContent=shown.length+' de '+items.length+' cafés';$('empty').hidden=shown.length>0;}
    $('filters').addEventListener('input',render);$('filters').addEventListener('change',render);$('filters').addEventListener('submit',e=>e.preventDefault());$('filters').addEventListener('reset',()=>setTimeout(render,0));render();
  }catch(error){$('count').textContent='Colección no disponible';$('error').hidden=false;$('error').textContent=error.message+' Genera la web con scripts/construir.py y ábrela mediante un servidor HTTP.';}
}
if(typeof document!=='undefined')start();
if(typeof module!=='undefined')module.exports={models,filtered};
