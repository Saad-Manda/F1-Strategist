import {resolveRelocation} from './course-model-v2.js?v=reading-20261006-r8';
const root=new URL('../',import.meta.url);
try {
  const response=await fetch(new URL('./route-relocations.json?v=reading-20261006-r8',import.meta.url));
  if(!response.ok)throw new Error('Relocation metadata unavailable');
  const map=await response.json();
  const path=decodeURIComponent(location.pathname.slice(root.pathname.length));
  const result=resolveRelocation(map,path+location.hash);
  if(result?.kind==='redirect')location.replace(new URL(result.targets[0],root).href);
} catch { /* Static choices remain available; unknown identities never redirect. */ }
