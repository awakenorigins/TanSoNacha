export function mount(host: HTMLElement) {
  const canvas = document.createElement('canvas'); canvas.className = 'sacred-hyperspeed'; canvas.setAttribute('aria-hidden', 'true');
  let raf = 0, running = true, particles: {x:number;y:number;z:number}[] = [];
  const ctx = canvas.getContext('2d', { alpha: true });
  if (!ctx) return { pause(){}, resume(){}, destroy(){ canvas.remove(); } };
  host.prepend(canvas);
  const resize = () => { const d=Math.min(devicePixelRatio||1,1.5); canvas.width=Math.floor(host.clientWidth*d); canvas.height=Math.floor(host.clientHeight*d); particles=Array.from({length:48},()=>({x:Math.random()-.5,y:Math.random()-.5,z:Math.random()})); };
  const draw = () => { if(!running)return; const w=canvas.width,h=canvas.height;ctx.clearRect(0,0,w,h);ctx.strokeStyle='rgba(218,190,126,.28)'; for(const p of particles){p.z-=.003;if(p.z<=.02)p.z=1;const x=w/2+p.x*w/p.z,y=h/2+p.y*h/p.z;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(w/2+p.x*w/(p.z+.035),h/2+p.y*h/(p.z+.035));ctx.stroke()}raf=requestAnimationFrame(draw); };
  const pause=()=>{running=false;cancelAnimationFrame(raf)}, resume=()=>{if(!running){running=true;draw()}}, destroy=()=>{pause();removeEventListener('resize',resize);canvas.remove()};
  addEventListener('resize',resize,{passive:true});resize();draw();return {pause,resume,destroy};
}
