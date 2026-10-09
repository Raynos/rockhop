/** CPU decoded-frame evidence. Container FPS tags never establish motion60. */
import assert from 'node:assert/strict';
export function cadence(times, scale=1) {
  assert(times.length >= 2, 'Need at least two observed frames');
  const values=times.map(value=>Number(value)*scale);
  assert(values.every(Number.isFinite));
  const gaps=values.slice(1).map((value,index)=>value-values[index]);
  assert(gaps.every(value=>value>0),'Non-increasing real presentation times');
  const sorted=[...gaps].sort((a,b)=>a-b), span=values.at(-1)-values[0];
  return { frames:values.length,observedFPS:(values.length-1)/span,
    intervalSeconds:{p50:sorted[Math.floor((sorted.length-1)*.5)],p95:sorted[Math.floor((sorted.length-1)*.95)],maximum:sorted.at(-1)},
    longestDeviationFrom60Seconds:Math.max(...gaps.map(value=>Math.abs(value-1/60))),
    timestamps:values };
}
export function decodeProof(probe, hashes) {
  const video=probe.streams.filter(row=>row.codec_type==='video');
  assert.equal(video.length,1);assert(!probe.streams.some(row=>row.codec_type==='audio'),'Silent video only');
  assert(video[0].width>0&&video[0].height>0);
  assert.equal(video[0].pix_fmt,'yuv420p','Exact decoded pixel parity requires yuv420p');
  const frames=probe.frames.filter(row=>row.media_type==='video');
  const result=cadence(frames.map(row=>row.best_effort_timestamp_time));
  assert.equal(hashes.length,frames.length,'Every decoded frame has a pixel digest');
  const unique=new Set(hashes).size;
  return { ...result,codec:video[0].codec_name,pixelFormat:video[0].pix_fmt,
    width:video[0].width,height:video[0].height,declaredAverageRate:video[0].avg_frame_rate,
    uniqueDecodedFrames:unique,distinctFraction:unique/hashes.length,
    // A stated millisecond timestamp quantum, not upsampled25fps or averaged
    // dropped frames. Actual numeric FPS always accompanies this observation.
    nominal60CadenceObserved:Math.abs(result.observedFPS-60)<=.1 && result.longestDeviationFrom60Seconds<=.002,
    meaning:'Measured decoded PTS/count/pixels; requested or declared container FPS is not substituted.' };
}
export function comparePresentation(source,encoded,sourceHashes,encodedHashes) {
  assert.equal(encoded.frames,source.frames,'Transcode duplicated/dropped frames');
  assert.equal(encoded.width,source.width);assert.equal(encoded.height,source.height);
  const a=source.timestamps.map(t=>t-source.timestamps[0]),b=encoded.timestamps.map(t=>t-encoded.timestamps[0]);
  const max=Math.max(...a.map((t,i)=>Math.abs(t-b[i])));
  assert(max<=.00002,'Passthrough presentation times changed');
  assert.deepEqual(encodedHashes,sourceHashes,'Lossless presentation changed decoded pixels');
  return {decodedFrameCountExact:true,decodedPixelsExact:true,maximumNormalizedPTSDifferenceSeconds:max};
}
export function parseFrameHashes(text) {
  return text.split('\n').filter(line=>line.trim()&&!line.startsWith('#')).map(line=> {
    const value=line.split(',').at(-1).trim();assert(/^[a-f0-9]{32}$/.test(value));return value;
  });
}

export function requestCoverage(proof,requestTimesMs) {
  const requested=cadence(requestTimesMs,.001);
  const countDifference=proof.frames-requested.frames;
  const spanDifference=Math.abs((proof.timestamps.at(-1)-proof.timestamps[0])
    -(requested.timestamps.at(-1)-requested.timestamps[0]));
  return {requests:requested.frames,decodedFrames:proof.frames,countDifference,
    presentationSpanDifferenceSeconds:spanDifference,
    completeRequestSpanObserved:Math.abs(countDifference)<=1 && spanDifference<=2/60+.002,
    meaning:'At most one initial stream frame and two frame periods of edge serialization; no missing long orbit segment.'};
}
