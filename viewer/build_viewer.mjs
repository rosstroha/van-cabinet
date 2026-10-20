import { build } from 'esbuild';
import { mkdir, copyFile, access } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));
const project=path.dirname(root);
const out=path.join(root,'dist');
await mkdir(path.join(out,'files'),{recursive:true});
try { await access(path.join(out,'model.json')); }
catch { throw new Error('Export CAD geometry first: npm run model'); }
await build({entryPoints:[path.join(root,'viewer.js')],bundle:true,format:'esm',target:'es2022',outfile:path.join(out,'app.js'),minify:true,sourcemap:true,legalComments:'eof'});
for (const [source,destination] of [['viewer.html','index.html'],['viewer.css','style.css'],['concept/cabinet_stowed.step','files/cabinet_stowed.step'],['concept/cabinet_deployed.step','files/cabinet_deployed.step'],['concept/layout.png','files/layout.png'],['COMPONENTS.md','files/COMPONENTS.md'],['parameters.json','files/parameters.json']]) {
  const sourceRoot=source.startsWith('viewer.')?root:project;
  await copyFile(path.join(sourceRoot,source),path.join(out,destination));
}
console.log('Browser viewer built in viewer/dist/. Start with npm start.');
