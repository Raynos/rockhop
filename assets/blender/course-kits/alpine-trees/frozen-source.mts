/** Node-side frozen-build proof shared by the parent-run A1 capture and perf tools. */
import { createHash } from 'node:crypto';
export async function frozenSource(url: string, expectedVersion: string, expectedIndex?: string) {
  const read = async (path: string) => {
    const response = await fetch(new URL(path,url));
    if (!response.ok) throw new Error(`Frozen source ${path}: HTTP ${response.status}`);
    return Buffer.from(await response.arrayBuffer());
  };
  const version = JSON.parse((await read('version.json')).toString()) as {sha:string;time?:string};
  if(version.sha!==expectedVersion) throw new Error(`Frozen version ${version.sha} != ${expectedVersion}`);
  const html = await read('index.html');
  const entry = html.toString().match(/data-entry="([^"]+)"/)?.[1];
  if(!entry) throw new Error('Frozen index has no loader data-entry');
  const index = await read(entry);
  const indexSHA256 = createHash('sha256').update(index).digest('hex');
  if(expectedIndex && indexSHA256!==expectedIndex) throw new Error(`Frozen entry ${indexSHA256} != ${expectedIndex}`);
  return {url,versionSha:version.sha,versionTime:version.time,indexUrl:new URL(entry,url).href,indexSHA256,
    htmlSHA256:createHash('sha256').update(html).digest('hex')};
}
