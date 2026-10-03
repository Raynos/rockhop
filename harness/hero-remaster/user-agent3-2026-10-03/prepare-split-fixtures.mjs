/** Pin capture-free anatomy/contact inputs; mappings remain owner/parent work. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const [matrixFile,driverFile,outputFile]=process.argv.slice(2);
assert(outputFile&&!fs.existsSync(outputFile),'Need prepared Game matrix, shared driver, fresh fixture output');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const matrixBytes=fs.readFileSync(matrixFile),driverBytes=fs.readFileSync(driverFile);
const matrix=JSON.parse(matrixBytes),driver=JSON.parse(driverBytes),root=path.dirname(matrixFile);
assert.equal(matrix.missing.length,0);assert.equal(matrix.cases.length,12);
assert.equal(sha(driverBytes),'8c40c42af362a8d3d8ae44d27a0b07570f600b26adc66d325239413f66c7625b');
const cases=matrix.cases.filter(c=>!['crash-instant-restart','recorded-clear'].includes(c.kind)).map(c=>{
  const file=path.join(root,c.recording);assert.equal(sha(fs.readFileSync(file)),c.sourceSHA256);
  return {...c,recording:file,status:'input window prepared; contact evidence unmeasured',poseInjection:false,bikeVisible:true,requiredVisibleContacts:['hand.L','hand.R','foot.L','foot.R','saddle']};
});
const contacts=Object.fromEntries(['hand.L','hand.R','foot.L','foot.R','saddle'].map(id=>[id,{status:'unmeasured',reason:'Requires new-candidate reviewed visible surface patch and live-bike target binding; no socket/bone guess.'}]));
const fixture={schema:'rockhop.agent3.split-fixtures.v1',status:'PREPARED_NO_NEW_CANDIDATE_CAPTURE',gameInputMatrix:{path:matrixFile,sha256:sha(matrixBytes),method:matrix.method,repeat:matrix.repeat,sourceFiles:matrix.sourceFiles},
  anatomy:{presentation:'bike-free',implementation:'harness/hero-remaster/user-agent3-2026-10-03/presentation.mjs#bikeFreeAnatomyPresentation',driver:{path:driverFile,sha256:sha(driverBytes),completeJointOrder:driver.jointOrderNative},
    allowedPoseInjection:true,pairedCameraAndControllerRequired:true,sourceFrames:[0,24,48,72,96,112,120,144,168,192,216,240],
    labels:['native rest','true A','true T','neutral','forward reach','elbow transition witness','bent elbows','overhead','asymmetric','squat stress','forward FK stress','hip/knee flexion FK stress'],
    continuous:{start:0,end:528,sourceHz:48,videoStep:4,videoFPS:12},
    presentationChecks:['Bike-only branches hidden; rider ancestors/visibility/transforms intact.','No visible bike or bike reflection; apply visibility after live-bike update before draw, then assert.','Entire body/hands/feet framed; same camera/materials for negative-control pairs.']},
  actualBike:{presentation:'live visible bike',driver:'recorded-game-input',allowedPoseInjection:false,cases,
    supportClassification:'Measure all five relations. Forward/standing intentionally clears saddle while grips/pegs support; low seated/back requires intended saddle/foot support. A measured saddle gap is not automatically a failure.',
    seatedReadiness:'Neutral grounded input window requires owner runtime pose plus actual visible saddle support; do not infer seated from anatomy crouch or socket debug flags.',
    contacts,existingFourContactProbe:'harness/hero-remaster/surface-contacts.mts#prepareSurfaceContacts',
    extraSaddleRequirement:'Existing probe has hand/foot only. Separate parent-reviewed pelvis/seat patches and live saddle target are mandatory; keep unmeasured until supplied.',
    candidateReadiness:['Owner-pinned new textured candidate/rig/controller and exact consumed GLB hashes.','Reviewed candidate surface patches/runtime geometry hashes, live-bike target bindings for full and LOD separately.','Actual production update retained; no authored pose injection, body/bike teleport or fitted socket as surrogate.','Replay every recording prefix from input1; state/hash/finish-byte and effective-camera equality between baseline/candidate.','All five visible contacts sampled through motion; root judges gaps/penetration/coverage and played choreography.']},
  preservation:{historicalPacket:'683cff0a',redoHistoricalCapture:false,sourceConstruction:false,canonicalControls:'unchanged; full/raw/four and prior played packets remain pinned'},
  limits:['Input/mode preparation only: no new rider/body/cloth geometry, movie, contact measurement, supported motion or art/device acceptance.','Dense collision pair counts and socket booleans are not acceptance. Do not manufacture contact mappings from bones/skin weights.']};
fs.mkdirSync(path.dirname(outputFile),{recursive:true});fs.writeFileSync(outputFile,JSON.stringify(fixture,null,2)+'\n');
console.log(JSON.stringify({status:fixture.status,actualBikeWindows:cases.length,anatomyFrames:fixture.anatomy.sourceFrames.length,unmeasuredContacts:Object.keys(contacts)}));
