import '@fontsource/noto-sans-devanagari/400.css';
import '@fontsource/noto-sans-devanagari/700.css';
import '@fontsource/noto-sans-devanagari/900.css';
import React from 'react';
import {AbsoluteFill, Composition, interpolate, registerRoot, useCurrentFrame} from 'remotion';

// This is a 3-second, vertical, animated news bumper; it is NOT the final episode.
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const NewsCard = () => {
  const f = useCurrentFrame();
  const entry = interpolate(f, [0, 9], [110, 0], clamp);
  const headlineScale = interpolate(f, [0, 7, 13, 23], [0.82, 1.1, 1, 1], clamp);
  const invoiceX = interpolate(f, [17, 28], [950, 0], clamp);
  const invoiceTurn = interpolate(f, [17, 28], [12, -4], clamp);
  const boxX = interpolate(f, [8, 23], [-620, 0], clamp);
  const boxTurn = interpolate(f, [8, 23], [-16, 7], clamp);
  const pulse = 1 + Math.sin(f / 3.2) * 0.045;
  const stripe = (f * 16) % 180;
  const flash = f >= 35 && f <= 41;
  const tvGlow = 0.3 + 0.2 * Math.sin(f / 2.4);
  const titleStyle = {fontFamily: '"Noto Sans Devanagari",sans-serif', fontWeight: 900};
  return <AbsoluteFill style={{background: '#fff3da', overflow: 'hidden', ...titleStyle}}>
    <AbsoluteFill style={{background: 'linear-gradient(180deg,#fff7e7 0%,#ffdcaa 70%,#ffc67d 100%)'}}/>
    <AbsoluteFill style={{opacity: 0.16, transform: 'translateX(' + (stripe - 180) + 'px) rotate(-16deg)', background: 'repeating-linear-gradient(90deg,transparent 0px,transparent 90px,#d44724 90px,#d44724 105px,transparent 105px,transparent 180px)'}}/>
    <div style={{position:'absolute',left:55,right:55,top:95,height:112,borderRadius:25,background:'#192a48',display:'flex',alignItems:'center',justifyContent:'space-between',padding:'0 38px',boxShadow:'0 12px 0 #d35b28'}}>
      <div style={{fontSize:50,color:'#fff7e9',letterSpacing:1}}>🐐 बकरा न्यूज़</div>
      <div style={{fontSize:29,color:'#ffdc62',background:'#a82b2b',padding:'12px 20px',borderRadius:12}}>COD कांड</div>
    </div>
    <div style={{position:'absolute',top:270,left:60,right:60,transform:'translateY(' + entry + 'px) scale(' + headlineScale + ')',textAlign:'center'}}>
      <div style={{fontSize:84,lineHeight:1.22,color:'#a92022',textShadow:'4px 5px 0 #fff',fontWeight:900}}>मिठाई माँगी...</div>
      <div style={{fontSize:90,lineHeight:1.24,color:'#152e53',fontWeight:900,background:'#ffe55a',border:'9px solid #172d4c',borderRadius:25,padding:'24px 10px',marginTop:28,boxShadow:'12px 13px 0 #db6029'}}>₹1.69 लाख का टीवी!</div>
    </div>
    <div style={{position:'absolute',left:75,top:810,transform:'translateX(' + boxX + 'px) rotate(' + boxTurn + 'deg)',width:470,height:420}}>
      <div style={{position:'absolute',left:0,top:115,width:430,height:300,background:'#c7833e',border:'12px solid #69411e',borderRadius:17,boxShadow:'20px 20px 0 #ae612b'}}/>
      <div style={{position:'absolute',left:155,top:117,width:84,height:294,background:'#f9d38e',opacity:0.85}}/>
      <div style={{position:'absolute',left:0,top:115,width:430,height:58,background:'#e9a24d',border:'8px solid #69411e',borderRadius:10}}/>
      <div style={{position:'absolute',left:85,top:205,fontSize:75,color:'#4c321c'}}>COD</div>
      <div style={{position:'absolute',left:120,top:0,fontSize:110,transform:'rotate(-18deg)'}}>📦</div>
    </div>
    <div style={{position:'absolute',right:30,top:840,width:510,height:380,transform:'scale(' + pulse + ')'}}>
      <div style={{height:285,border:'24px solid #1d2944',borderRadius:26,background:'linear-gradient(130deg,#7cc9e9,#c0f2ff 55%,#8bc3e0)',boxShadow:'15px 17px 0 #536b87, inset 0 0 70px rgba(255,255,255,' + tvGlow + ')',display:'flex',alignItems:'center',justifyContent:'center'}}>
        <div style={{fontSize:120}}>📺</div>
      </div>
      <div style={{width:130,height:28,background:'#25344d',margin:'0 auto'}}/>
      <div style={{width:260,height:23,background:'#25344d',borderRadius:12,margin:'0 auto'}}/>
    </div>
    <div style={{position:'absolute',top:1260,left:85,right:85,transform:'translateX(' + invoiceX + 'px) rotate(' + invoiceTurn + 'deg)',background:'#fff',border:'8px dashed #b62b28',borderRadius:24,padding:'36px 20px',textAlign:'center',boxShadow:'14px 16px 0 #e98a51'}}>
      <div style={{fontSize:39,color:'#4b5360'}}>कैश ऑन डिलीवरी बिल</div>
      <div style={{fontSize:112,color:'#c12529',lineHeight:1.3}}>₹1,69,000</div>
      <div style={{fontSize:37,color:'#142c4a'}}>मिठाई के बदले ये क्या आ गया?</div>
    </div>
    <div style={{position:'absolute',bottom:105,left:55,right:55,background:flash?'#ffe65b':'#192b4a',color:flash?'#1a2a43':'#fff',borderRadius:24,padding:'27px 26px',fontSize:49,textAlign:'center',boxShadow:'0 12px 0 #bb5227'}}>
      अगला ट्विस्ट? चाचा से पूछो! 😳
    </div>
  </AbsoluteFill>;
};
registerRoot(() => <Composition id="NewsCard" component={NewsCard} durationInFrames={75} fps={25} width={1080} height={1920}/>);
