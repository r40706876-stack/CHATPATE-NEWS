// Deterministic, narration-timed motion for the local video scene, never a live site.
(()=>{
const baseSeek=window.seek, isDates=!!document.getElementById('calendar');
const clip=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const ease=x=>1-Math.pow(1-clip(x),3);
const style=document.createElement('style');style.textContent=`
.stage,.calendar{perspective:1000px}.stage .stat{transform-origin:50% 80%}
.motion-rail{position:absolute;left:25px;right:25px;bottom:10px;height:6px;background:#e8dfd0;border-radius:5px;overflow:visible}
.motion-fill{height:100%;background:#b92d2c;border-radius:5px;transform-origin:left}
.motion-dot{position:absolute;top:-5px;width:16px;height:16px;border:3px solid white;background:#b92d2c;border-radius:50%;box-shadow:0 2px 6px #202b4b33}
.chance-dots{display:flex;gap:7px;margin-top:8px}.chance-dots i{width:19px;height:19px;border-radius:50%;background:#28745c;border:2px solid white;box-shadow:0 1px 4px #0002}
#motion-mail{position:absolute;right:22px;top:60px;font:800 34px sans-serif;color:#b6302c;width:76px;height:66px;border:3px solid #b6302c;border-radius:11px;background:#fff8ec;display:grid;place-items:center}
#motion-mail:before{content:'';position:absolute;width:47px;height:27px;border-bottom:3px solid #b6302c;transform:rotate(-25deg);top:4px}
#calendar:before,#calendar:after{content:'';position:absolute;inset:6px -5px -7px;background:#eadac2;border:1px solid #d7c7b0;border-radius:23px;z-index:-1;transform:rotate(3deg)}
#calendar:after{inset:12px -9px -13px;transform:rotate(-3deg);background:#f5e8d5;z-index:-2}
.cell.day{position:relative}.motion-step{position:absolute;height:3px;background:#b6302c;top:243px;left:30px;transform-origin:left;z-index:1}
`;
document.head.appendChild(style);
if(!isDates){
 for(let i=1;i<=7;i++){const s=document.getElementById('sc'+i),r=document.createElement('div');r.className='motion-rail';r.innerHTML='<div class="motion-fill"></div><i class="motion-dot"></i>';s.appendChild(r);}
 document.querySelectorAll('#sc5 .stat').forEach((el,i)=>{const q=document.createElement('div');q.className='chance-dots';q.innerHTML='<i></i>'.repeat(i?3:2);el.appendChild(q)});
 const m=document.createElement('div');m.id='motion-mail';m.textContent='✓';document.getElementById('sc6').appendChild(m);
}
else{let step=document.createElement('div');step.className='motion-step';document.getElementById('film').appendChild(step)}
function enter(el,age,delay=0,dx=0,dy=26,duration=.65){if(!el)return;const p=ease((age-delay)/duration);el.style.opacity=p;el.style.transform=`translate(${dx*(1-p)}px,${dy*(1-p)}px) scale(${.91+.09*p})`;}
window.seek=function(t){
 baseSeek(t);
 const list=LINES;const cueset=window.CUES||{};let line=0;for(let k=0;k<list.length;k++)if(t>=(cueset[list[k][0]]||{}).t)line=k;
 const scene=list[line][3],start=(cueset[SCENES[scene][1]]||{}).t||0,age=Math.max(0,t-start),cue=cueset[list[line][0]],duration=(cue&&cue.d)||4;
 // Title enters quickly then remains still while the reader reads it.
 const title=document.getElementById(isDates?'heading':'title');enter(title,age,0,0,22,.42);
 if(!isDates){
  const s=document.getElementById('sc'+scene);const p=ease(age/.65);s.style.opacity=p;s.style.transform=`perspective(900px) translateX(${(scene%2?1:-1)*55*(1-p)}px) rotateY(${(scene%2?1:-1)*14*(1-p)}deg)`;
  const rail=s.querySelector('.motion-rail');if(rail){const progress=clip(age/Math.max(1,duration));rail.querySelector('.motion-fill').style.transform=`scaleX(${progress})`;rail.querySelector('.motion-dot').style.left=`calc(${progress*100}% - 8px)`;}
  s.querySelectorAll('.stat').forEach((el,i)=>{const delay=scene===2?(i?1.9:.12):i*.9;enter(el,age,delay,i?40:-40,16,.62);if(age>delay+.65)el.style.transform=`translateY(${-3*Math.sin((age-delay)*2)}px)`});
  s.querySelectorAll('.check').forEach((el,i)=>{const delay=scene===4?[.1,2.65,4.2][i]:[.45,1.65,3.0][i];enter(el,age,delay,-50,0,.45);const icon=el.querySelector('i');const q=clip((age-delay-.22)/.34);icon.style.transform=`scale(${.2+.8*(1-Math.pow(1-q,3))}) rotate(${-75*(1-q)}deg)`;});
  const cal=s.querySelector('svg');if(cal&&scene===1){const q=ease(age/.8);cal.style.transform=`perspective(500px) rotateX(${-85*(1-q)}deg) translateY(${-4*Math.sin(age*2)}px)`;cal.style.transformOrigin='50% 25%';const paths=cal.querySelectorAll('path');const last=paths[paths.length-1];if(last){last.style.strokeDasharray='90';last.style.strokeDashoffset=90*(1-clip((age-.75)/.7));}}
  s.querySelectorAll('.num').forEach((el,i)=>{const q=ease((age-.15-i*.28)/.5);el.style.transform=`scale(${.7+.3*q})`;el.style.transformOrigin='left center'});
  s.querySelectorAll('.chance-dots').forEach((row,i)=>row.querySelectorAll('i').forEach((el,k)=>{const q=ease((age-.55-i*.85-k*.32)/.3);el.style.opacity=q;el.style.transform=`translateY(${-18*(1-q)}px) scale(${q})`;}));
  const stamp=s.querySelector('.stamp');if(stamp){const q=ease((age-1.3)/.45);stamp.style.opacity=q;stamp.style.transform=`scale(${1.5-.5*q}) rotate(${-18+13*q}deg)`;}
  if(scene===6){const m=document.getElementById('motion-mail');m.style.transform=`translate(${65*(1-ease(age/.7))}px,${-6*Math.sin(age*2)}px) rotate(${5*Math.sin(age*1.8)}deg)`;m.style.opacity=ease(age/.7);}
  if(scene===7){s.querySelectorAll('span').forEach((el,i)=>{el.style.display='inline-block';el.style.transform=`scale(${1+.08*Math.exp(-Math.pow(age-(.3+i*1.3),2)*4)})`})}
  s.querySelectorAll('.pill').forEach(el=>enter(el,age,.8,0,20,.5));
 }else{
  const cal=document.getElementById('calendar'),q=ease(age/.78);
  if(scene<6){
   cal.style.opacity=q;cal.style.transform=`perspective(1000px) rotateX(${-72*(1-q)}deg) rotateY(${14*(1-q)}deg) translateY(${42*(1-q)-3*Math.sin(age*1.7)}px)`;
   const date=document.getElementById('date');const dp=ease((age-.18)/.68);date.style.opacity=dp;date.style.transform=`translateY(${35*(1-dp)}px) scale(${.82+.18*dp})`;
   const days=[...document.querySelectorAll('.day.hit')],index=Math.floor(Math.max(0,age-.8)*4)%Math.max(1,days.length);
   days.forEach((el,i)=>{const reveal=ease((age-.6-i*.045)/.3);el.style.opacity=.3+.7*reveal;el.style.transform=`scale(${i===index?1.22:1})`;el.style.boxShadow=i===index?'0 0 0 2px #d8a243':'none';el.style.background=i===index?'#d39a32':'#b6302c';});
   const st=document.getElementById('stamp'),sp=ease((age-1)/.35);st.style.opacity=sp;st.style.transform=`scale(${1.8-.8*sp}) rotate(${-25+17*sp}deg)`;
   const host=document.getElementById('character');host.style.opacity=q;host.style.transform=`translateX(${-90*(1-q)}px) translateY(${-4*Math.sin(age*1.7)}px) rotate(${1.2*Math.sin(age*1.1)}deg)`;
   enter(document.getElementById('bubble'),age,.2,-35,0,.5);enter(document.getElementById('info'),age,.5,40,0,.55);
   const pointer=document.getElementById('pointer');pointer.style.left=(scene===4?300:277)+'px';pointer.style.top='365px';pointer.style.transform=`translate(${12*Math.sin(age*2)}px,${12*Math.cos(age*2)}px) scale(${1+.18*Math.sin(age*4)})`;pointer.style.opacity=.5;
  }
  document.querySelector('.motion-step').style.width=(102*clip((scene-1+clip(age/2))/5))+'px';
  if(scene===6){document.querySelectorAll('.event').forEach((el,i)=>{enter(el,age,i*.4,i%2?65:-65,0,.55);el.style.borderLeft=(i===Math.floor(age/.65)%5?'4px solid #b6302c':'4px solid transparent');});}
 }
};
})();
