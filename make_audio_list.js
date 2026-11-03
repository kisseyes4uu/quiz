const fs=require('fs'),vm=require('vm');
const dir=process.argv[2]||'.';
const html=fs.readFileSync(dir+'/index.html','utf8');
const grab=(re)=>{const m=html.match(re);if(!m)throw new Error('missing '+re);return m[0]};
const code=[grab(/const H=t=>\{[^\n]*\n/),grab(/const JAMO=[^\n]*\n/),grab(/const speakable=[^\n]*\n/),grab(/const NUMK=[^\n]*\n/),grab(/const sent=[^\n]*\n/),grab(/const GRID_TAIL=[^\n]*\n/),grab(/const OX_TAIL=[^\n]*\n/),grab(/function partsOf[\s\S]*?\n\}\n/)].join('')+';this.H=H;this.speakable=speakable;this.sent=sent;this.partsOf=partsOf;';
const ctx={};ctx.window=ctx;vm.createContext(ctx);vm.runInContext(code,ctx);
const qs=fs.readFileSync(dir+'/questions.js','utf8')+';this.QB=QUIZ_BANK;';
vm.runInContext(qs,ctx);
const set=new Map();const add=t=>set.set(ctx.H(t),t);
for(const x of ctx.QB){
  if(x.c==='OX'){const p=ctx.partsOf({type:'ox',q:x.q});p.forEach(add)}
  else if(x.c==='낱말찾기'){ctx.partsOf({type:'grid',letters:x.letters}).forEach(add)}
  else{const all=[x.a,...x.w];
    add(ctx.sent(ctx.speakable(x.q)));}
}

const out=[...set].map(([f,t])=>({file:f+'.mp3',text:t}));
fs.writeFileSync(dir+'/audio_texts.json',JSON.stringify(out,null,1));
console.log(out.length,'clips; bank',ctx.QB.length);
