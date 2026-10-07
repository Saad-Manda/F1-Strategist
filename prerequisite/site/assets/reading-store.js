// Every active writer uses this coordinator and the same exclusive storage lock.
import {emptyCourseV2, COURSE_KEY_V2, LEGACY_COURSE_KEY, JOURNAL_KEY, prepareStoredProgress, commitProgress, recoverTransaction, withProgressLock, exportBundleV2, validateBundleV2} from './course-progress-v2.js?v=reading-20261006-r8';

export async function createReadingSession({storage,locks,data}) {
  let bundle={course:emptyCourseV2(),labs:{version:1,labs:{}},retainedLegacy:null};
  let warning='',blocked=false,pendingMigration=false,queue=Promise.resolve();
  const listeners=new Set();
  const changed=()=>{for(const fn of listeners)fn();};
  const prepare=()=>prepareStoredProgress(storage,data.course,data.snapshot,data.mapping,data.labs);
  const commit=next=>commitProgress(storage,next,data.course,data.snapshot,data.mapping,data.labs);
  try {
    if(!locks?.request) {
      bundle=prepare();blocked=true;
      warning='Saving and migration need an exclusive browser storage lock. You can read and export your retained progress.';
    } else await withProgressLock(locks,()=>{
      recoverTransaction(storage);
      bundle=prepare();
      pendingMigration=storage.getItem(COURSE_KEY_V2)===null && bundle.retainedLegacy!==null;
    });
  } catch(error) {blocked=true;warning='Saved progress could not be loaded safely. Original data was retained. '+error.message;}
  return {
    get bundle(){return structuredClone(bundle);},
    get warning(){return warning;},
    get pendingMigration(){return pendingMigration;},
    get writable(){return !blocked && !pendingMigration;},
    subscribe(fn){listeners.add(fn);return ()=>listeners.delete(fn);},
    export(){return exportBundleV2(bundle);},
    recoveryExport(){
      const saved={};
      for(const key of [LEGACY_COURSE_KEY,'rl-labs:v1',COURSE_KEY_V2,'rl-course:migration-backup:v1',JOURNAL_KEY]) {
        try {saved[key]=storage.getItem(key);} catch {saved[key]='Storage unavailable';}
      }
      return JSON.stringify({format:'rl-course-raw-recovery',saved},null,2);
    },
    update(change,{activate=false}={}) {
      const operation=async()=>{
        if(blocked)throw new Error(warning);
        if(pendingMigration && !activate)throw new Error('Close or reload older course tabs, then choose Retain my progress before saving.');
        try {
          const saved=await withProgressLock(locks,()=>{
            recoverTransaction(storage);
            const latest=prepare();
            return commit(change(structuredClone(latest)));
          });
          bundle=saved;pendingMigration=false;warning='';changed();return true;
        } catch(error) {
          warning=error.message+' Completion was not saved. Export your progress or use Next to browse without saving.';
          changed();throw error;
        }
      };
      const result=queue.then(operation);queue=result.catch(()=>{});return result;
    },
    activateMigration(){return this.update(b=>b,{activate:true});},
    async import(raw) {
      const valid=validateBundleV2(raw,data.course,data.snapshot,data.mapping,data.labs);
      return this.update(()=>valid);
    },
    refresh(key) {
      return queue.then(async()=>{
        if(key===LEGACY_COURSE_KEY) {
          blocked=true;warning='An older course tab changed progress. Close or reload older tabs, then reload this page before saving.';
        } else try {
          await withProgressLock(locks,()=>{recoverTransaction(storage);bundle=prepare();pendingMigration=storage.getItem(COURSE_KEY_V2)===null && bundle.retainedLegacy!==null;});
        } catch(error){blocked=true;warning=error.message;}
        changed();
      });
    }
  };
}
