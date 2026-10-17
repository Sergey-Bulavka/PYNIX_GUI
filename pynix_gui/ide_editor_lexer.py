# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Editor display lexer; independent of compiler diagnostics and file editing.

This small browser lexer emits ranges instead of modifying text. The source
textarea remains authoritative for caret, selection, undo and IME.
"""

EDITOR_LEXER_JS = r"""<script id="pynix-v4-editor-lexer">
(() => {
 const PYTHON_KEYWORDS = new Set([
  'False','None','True','and','as','assert','async','await','break','class',
  'continue','def','del','elif','else','except','finally','for','from',
  'global','if','import','in','is','lambda','nonlocal','not','or','pass',
  'raise','return','try','while','with','yield','match','case'
 ]);
 const PYNIX_KEYWORDS = new Set([
  'function','module','import','from','as','let','var','const','if','else',
  'elif','while','for','in','return','break','continue','and','or','not',
  'class','interface','type','enum','match','case','try','catch','finally',
  'raise','public','private','async','await'
 ]);
 const BUILTINS = new Set([
  'print','input','len','range','str','int','float','bool','list','dict',
  'set','tuple','super','open','enumerate','zip','sum','min','max'
 ]);
 const TYPES = new Set(['Int','Float','Bool','String','Void','Any','List','Map']);
 const wordRE=/[A-Za-z_][A-Za-z_0-9]*/y;
 const numberRE=/(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|(?:\d[\d_]*(?:\.\d[\d_]*)?|\.\d[\d_]+)(?:[eE][+-]?\d[\d_]*)?)/y;
 const quotePrefixes=/^(?:[rRuUbBfF]{1,3})?(?:"{3}|'{3}|"|')/;
 const isWord=ch=>ch!==undefined&&/[A-Za-z_0-9]/.test(ch);
 const kindForWord=(text,value,start,end,isPython)=>{
  const before=value.slice(value.lastIndexOf('\n',start-1)+1,start);
  const after=value.slice(end);
  if(isPython){
   if(['True','False','None'].includes(text))return 'python-constant';
   if(PYTHON_KEYWORDS.has(text))return 'python-keyword';
   if(/\bdef\s+$/.test(before))return 'python-definition';
   if(/\bclass\s+$/.test(before))return 'python-class';
   if(BUILTINS.has(text)&&/^\s*\(/.test(after))return 'python-builtin';
   if(/^\s*\(/.test(after))return 'python-call';
   return 'python-plain';
  }
  if(PYNIX_KEYWORDS.has(text))return 'keyword';
  if(/\b(function|class|interface|type|enum)\s+$/.test(before))return 'definition';
  if(['true','false','none','null'].includes(text))return 'constant';
  if(TYPES.has(text))return 'type';
  if(BUILTINS.has(text)&&/^\s*\(/.test(after))return 'builtin';
  if(/^\s*\(/.test(after))return 'call';
  return 'plain';
 };
 const consumeQuoted=(value,quoteAt,quote)=>{
  const triple=value.startsWith(quote.repeat(3),quoteAt);
  const width=triple?3:1;
  let i=quoteAt+width;
  while(i<value.length){
   if(value[i]==='\\'){i+=Math.min(2,value.length-i);continue;}
   if(value.startsWith(quote.repeat(width),i))return i+width;
   if(!triple&&value[i]==='\n')return i;
   i++;
  }
  return i;
 };
 const tokenize=(value,filename)=>{
  if(typeof value!=='string')return [];
  const isPython=/\.pyi?$/i.test(filename||'');
  const isPynix=/\.pnx$/i.test(filename||'');
  if(!isPython&&!isPynix)return [];
  const result=[];
  const push=(start,end,kind)=>{
   if(end>start)result.push({start,end,kind});
  };
  let i=0;
  while(i<value.length){
   const start=i;
   if(value[i]==='#'||(isPynix&&value.startsWith('//',i))){
    i=value.indexOf('\n',i);
    if(i<0)i=value.length;
    push(start,i,isPython?'python-comment':'comment');continue;
   }
   // Recognize f-strings, raw strings, byte strings and multi-line docstrings.
   // A prefix is accepted only at a lexical boundary.
   const quoted=!isWord(value[i-1])?value.slice(i).match(quotePrefixes):null;
   if(quoted){
    const full=quoted[0],quote=full[full.length-1];
    const quoteAt=i+full.length-(full.endsWith(quote.repeat(3))?3:1);
    i=consumeQuoted(value,quoteAt,quote);
    push(start,i,isPython?'python-string':'string');continue;
   }
   if(isPython&&value[i]==='@'){
    const decorated=/^@[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*/.exec(value.slice(i));
    const before=value.slice(value.lastIndexOf('\n',i-1)+1,i);
    if(decorated&&/^\s*$/.test(before)){
     i+=decorated[0].length;push(start,i,'python-decorator');continue;
    }
   }
   numberRE.lastIndex=i;
   const number=numberRE.exec(value);
   if(number&&!isWord(value[i-1])){
    i=numberRE.lastIndex;push(start,i,isPython?'python-number':'number');continue;
   }
   wordRE.lastIndex=i;
   const word=wordRE.exec(value);
   if(word){
    i=wordRE.lastIndex;
    push(start,i,kindForWord(word[0],value,start,i,isPython));continue;
   }
   if('(){}[]'.includes(value[i])){
    i++;push(start,i,'bracket');continue;
   }
   i++;
  }
  return result;
 };
 window.pynixHighlightTokens=tokenize;
})();
</script>"""
