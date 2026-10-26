import React from 'react';
import {Composition, registerRoot, useCurrentFrame, interpolate, AbsoluteFill} from 'remotion';
const NewsCard=()=>{const f=useCurrentFrame();const scale=interpolate(f,[0,7,20],[0.7,1.13,1],{extrapolateRight:'clamp'});return <AbsoluteFill style={{background:'#f9e6c8',justifyContent:'center',alignItems:'center',fontFamily:'sans-serif'}}><div style={{fontSize:90,fontWeight:900,color:'#b92e28',transform:`scale(${scale})`,textAlign:'center'}}>बकरा न्यूज़</div><div style={{fontSize:50,color:'#1e344c',marginTop:50}}>खबर में ट्विस्ट!</div></AbsoluteFill>};
registerRoot(()=> <Composition id="NewsCard" component={NewsCard} durationInFrames={75} fps={25} width={1080} height={1920}/>);
