'use strict';
const $ = id => document.getElementById(id);
const num = value => value === '' || value == null ? null : Number(value);
const fold = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const dateText = value => value ? new Intl.DateTimeFormat('es', {dateStyle:'medium',timeZone:'UTC'}).format(new Date(value+'T00:00:00Z')) : 'Fecha desconocida';
const money = (value,currency='EUR') => value === null ? 'Precio desconocido' : new Intl.NumberFormat('es',{style:'currency',currency:currency||'EUR'}).format(value);
function node(tag, text, className) { const el=document.createElement(tag); if(text!==undefined) el.textContent=text; if(className)el.className=className; return el; }
function link(url, text) { try { const u=new URL(url); if(!['https:','http:'].includes(u.protocol))return null; const a=node('a',text,'shop');a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';return a;}catch{return null;} }
function models(data) {
  return data.cafes.map(cafe=>{
    const purchases=data.compras.filter(p=>p.cafe_id===cafe.id).sort((a,b)=>(b.fecha||b.fecha_registro).localeCompare(a.fecha||a.fecha_registro));
    const reviews=data.valoraciones.filter(r=>r.cafe_id===cafe.id).sort((a,b)=>b.fecha.localeCompare(a.fecha)||b.id.localeCompare(a.id));
    const latest=purchases[0], review=reviews[0];
    const versions=(data.versiones||[]).filter(v=>v.cafe_id===cafe.id).sort((a,b)=>b.fecha.localeCompare(a.fecha));
    return {...cafe,purchases,reviews,versions,latest,review,rating:review?num(review.puntuacion):null,price:latest?num(latest.precio):null,activity:[...purchases.map(p=>p.fecha||p.fecha_registro),...reviews.map(r=>r.fecha)].sort().at(-1)||'',search:fold([cafe.nombre,cafe.origen,cafe.proceso,cafe.descripcion,cafe.notas,...reviews.map(r=>r.notas),...versions.map(v=>[v.notas_cata,v.proceso,v.variedades,v.region,v.productor,v.descripcion].join(' '))].join(' '))};
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
  heading.append(node('p',c.origen||'Origen sin registrar','origin'),node('h3',c.nombre));
  const score=node('span',c.rating===null?'Sin valorar':String(c.rating).replace('.',','),'score'+(c.rating===null?' pending':''));
  if(c.rating!==null)score.append(node('small','/ 5'));
  top.append(heading,score);el.append(top,node('p',[c.tienda,c.proceso].filter(Boolean).join(' · '),'meta'));
  if(c.review){el.append(node('blockquote',c.review.notas||'Sin comentario.','quote'),node('p','Valoración del '+dateText(c.review.fecha)+' · '+c.review.version,'meta'));}
  else el.append(node('p','Todavía sin valoración.','quote'));
  const tasted=c.versions.find(v=>v.id===c.review?.version_id);
  if(tasted?.notas_cata)el.append(node('p','Cata comercial de la versión valorada: '+tasted.notas_cata,'meta'));
  if(c.latest&&!c.reviews.some(r=>r.compra_id===c.latest.id)) el.append(node('p',c.reviews.some(r=>!r.compra_id)?'Valoración registrada; compra concreta sin confirmar.':'Última '+(c.latest.tipo==='muestra'?'muestra':'compra')+' pendiente de valoración.','status'));
  const priceRow=node('div',undefined,'price-row'),price=node('span',c.latest?.tipo==='muestra'&&c.price===null?'Muestra regalada':money(c.price,c.latest?.moneda),'price');
  if(c.latest?.gramos)price.append(node('small',c.latest.gramos+' g'));
  priceRow.append(price);const shop=link(c.url,'Ver en '+(c.tienda||'la tienda'));if(shop)priceRow.append(shop);el.append(priceRow);
  const details=node('details',undefined,'details');details.append(node('summary','Ficha e historial'));
  if(c.descripcion)details.append(node('p',c.descripcion));if(c.notas)details.append(node('p',c.notas));
  details.append(node('p','Compras y muestras','detail-title'));const buys=node('ul');
  for(const p of c.purchases){const li=node('li');li.append(node('strong',p.tipo==='muestra'?'Muestra · ':'Compra · '),document.createTextNode(dateText(p.fecha)+' · '+(p.tipo==='muestra'&&p.precio===''?'regalada':money(num(p.precio),p.moneda))+(p.gramos?' / '+p.gramos+' g':'')),node('p',[p.molienda,p.tueste,p.version,p.notas].filter(Boolean).join(' · ')));if(p.version_id)li.append(node('p','Ficha conservada: '+p.version_id));buys.append(li);}details.append(buys);
  details.append(node('p','Valoraciones por bolsa','detail-title'));const reviews=node('ul');
  for(const r of c.reviews){const li=node('li');li.append(node('strong',r.puntuacion.replace('.',',')+'/5 · '+dateText(r.fecha)),node('p',r.version+(r.compra_id?' · Compra: '+r.compra_id:' · Compra concreta sin confirmar')+(r.fecha_consumo?' · Consumo: '+dateText(r.fecha_consumo):'')),node('p',r.notas));if(r.version_id)li.append(node('p','Ficha conservada: '+r.version_id));reviews.append(li);}if(!c.reviews.length)reviews.append(node('li','Sin valoraciones.'));details.append(reviews);
  if(c.versions.length){details.append(node('p','Notas de cata comerciales · historial','detail-title'));for(const v of c.versions){const section=node('section');section.append(node('p',dateText(v.fecha)+' · '+v.fuente+' · '+v.id,'detail-title'),node('p',v.notas_cata||'Notas de cata no publicadas.'));section.append(node('p',[v.proceso,v.variedades,v.region,v.productor,v.altitud,v.sca?'SCA '+v.sca:''].filter(Boolean).join(' · ')));if(v.descripcion)section.append(node('p',v.descripcion));if(v.notas)section.append(node('p',v.notas));const source=link(v.url,'Fuente original');if(source)section.append(source);details.append(section);}}
  el.append(details);return el;
}
async function start(){
  try{
    const response=await fetch('datos.json');if(!response.ok)throw new Error('No se pudo cargar la colección.');const data=await response.json(),items=models(data);
    $('title').textContent=data.coleccion.titulo;$('author').textContent=data.coleccion.autor?'EL CUADERNO DE '+data.coleccion.autor.toUpperCase():'MI COLECCIÓN';$('description').textContent=data.coleccion.descripcion;document.title=data.coleccion.titulo+' · Café de Datos';
    for(const [count,label] of [[items.length,'cafés'],[data.valoraciones.length,'valoraciones'],[data.compras.length,'compras y muestras']]){const s=node('div',undefined,'stat');s.append(node('strong',String(count)),node('span',label));$('summary').append(s);}
    function render(){const f={search:$('search').value.trim(),rating:$('rating').value,min:$('min-price').value,max:$('max-price').value,kind:$('date-kind').value,from:$('from').value,to:$('to').value,sort:$('sort').value};const shown=filtered(items,f);$('cards').replaceChildren(...shown.map(card));$('count').textContent=shown.length+' de '+items.length+' cafés';$('empty').hidden=shown.length>0;}
    $('filters').addEventListener('input',render);$('filters').addEventListener('change',render);$('filters').addEventListener('submit',e=>e.preventDefault());$('filters').addEventListener('reset',()=>setTimeout(render,0));render();
  }catch(error){$('count').textContent='Colección no disponible';$('error').hidden=false;$('error').textContent=error.message+' Genera la web con scripts/construir.py y ábrela mediante un servidor HTTP.';}
}
if(typeof document!=='undefined')start();
if(typeof module!=='undefined')module.exports={models,filtered};
