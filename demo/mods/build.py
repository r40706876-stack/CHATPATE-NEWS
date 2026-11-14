import sys,os
d=os.path.dirname(os.path.abspath(__file__))
s=open(os.path.join(d,'src.html')).read()
s=s.replace('/*ENGINE*/',open(os.path.join(d,'engine.js')).read()).replace('/*SCENE*/',open(os.path.join(d,'scene.js')).read())
open(os.path.join(d,'demo.html'),'w').write(s); print('built')
