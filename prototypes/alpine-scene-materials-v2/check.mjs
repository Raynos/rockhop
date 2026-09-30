/** Typecheck each phase using the same immutable application graph; no build/plugin execution. */
import fs from 'node:fs';
import path from 'node:path';
import ts from 'typescript';
import { home, common, sha, verifySnapshot } from './prepare.mjs';
const manifest = verifySnapshot();
const configPath = path.join(common,'tsconfig.json');
const config = ts.readConfigFile(configPath,ts.sys.readFile);
if(config.error) throw new Error(ts.flattenDiagnosticMessageText(config.error.messageText,'\n'));
const parsed = ts.parseJsonConfigFileContent(config.config,ts.sys,common);
const phases=[];
for(const phase of ['before','after']) {
  const host=ts.createCompilerHost(parsed.options);
  const originalRead=host.readFile;
  const replacements=new Map(phase==='after'?manifest.overrides.map(entry=>[path.join(common,entry.file),fs.readFileSync(path.join(home,'out/after',entry.file),'utf8')]):[]);
  host.readFile=file=>replacements.get(path.resolve(file))??originalRead(file);
  const program=ts.createProgram(parsed.fileNames,parsed.options,host);
  const diagnostics=ts.getPreEmitDiagnostics(program);
  if(diagnostics.length) {
    console.error(ts.formatDiagnosticsWithColorAndContext(diagnostics,{getCurrentDirectory:()=>common,getCanonicalFileName:name=>name,getNewLine:()=> '\n'}));
    process.exitCode=1;
  }
  phases.push({phase,sourceFiles:program.getSourceFiles().length,diagnostics:diagnostics.length});
}
fs.writeFileSync(path.join(home,'checks.json'),JSON.stringify({schema:1,status:process.exitCode?'failed':'passed',
  snapshotManifestSHA256:sha(fs.readFileSync(path.join(home,'snapshot-manifest.json'))),phases,
  buildsRun:false,browserRun:false},null,2)+'\n');
console.info(JSON.stringify(phases,null,2));
