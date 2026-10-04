# Neck interface103: the archived chord fails normals before new crossings

Status: diagnostic only, unaccepted. Independent neck71 rejected102. The
464-ID expansion remains rejected. No candidate, native save, fitting or skin
solve, normal edit, pose, render or capture was made in103. All M0–M5 and
contact, identity, art, engine, device and player gates remain open.

The user's bar is a continuous, natural head-to-neck-to-shoulder transition
that preserves the selected face identity. Counts and zero seam drift cannot
establish that result. Root remains the sole played visual judge.

## What the archive supports

The102 operator was one direct linear solve. No iterates, line-search or
intermediate native tessellations were recorded. This analysis reconstructs
`P(alpha)=P0+alpha*(P1-P0)` from the frozen endpoints; it is not solver
chronology. Collision coordinates are continuous Float64; normal probes use
native Float32 positions and actual Blender decoding on unlinked transient
mesh copies. The alpha0 decoder matches the frozen100 normal bytes exactly.

Using one fixed reference tessellation makes pair identity comparable:

| Proper crossings | Start | Final | Introduced | Resolved original |
| --- | ---: | ---: | ---: | ---: |
| Body self | 1 | 0 | 0 | 1 |
| Head self | 0 | 1112 | 1112 | 0 |
| Body/head | 245 | 308 | 307 | 244 |

One original body/head pair persists. Final native tessellation changes six
body and two head triangle rows: its separate endpoint count is307
body/head, agreeing with neck71. The final-template start count is246; these
counts must not be substituted into the reference pair chronology.

The complete swept new-pair universe through alpha0.01 has3783 body-self,
5967 head-self and3968 body/head pairs. Numeric vertex/face and edge/edge
coplanarity events find nine introduced body/head entries and no introduced
self entries in that interval. No persistent coplanar or always-collinear
features occurred in this universe. The earliest numeric event is at
alpha **0.0016151760910615134**, body triangle9188/head triangle71886:
body vertices `[4675,9197,9196]`, head `[22062,22057,43762]`;43762 is the
inner-cap centroid. Its selected edge/edge polynomial has an exact binary
rational sign-change bracket
`[0.0016151760890615134,0.0016151760930615134]`. The proper classifier is
false at root−1e−6 and true at root+1e−6. This certifies that selected root;
all other root ordering is numerical. It does not certify a global first
contact or an event in the actual one-shot solver execution.

The cap does not explain the final failure by itself. Two selected non-cap
neck71 witnesses have unchanged reference/final triangle rows and all six
corners with archived tangentDOF3. Head-self4/94 first crosses on this chord
at0.829590974791729; body/head208/22652 at0.8990748037683983. These are
selected pair onsets, not globally earliest non-cap events.

## The decoded-normal constraint is already violated

At alpha1e−6 there are no introduced proper crossings, but **726 protected
head corners** decode differently (maximum vector delta4.472233454288665e−5).
At alpha0.01,1365 head/148 body protected corners differ; at alpha1,1365
head/152 body differ. The head mask includes the173 inside-but-pinned-alias
corners identified by neck71, alongside1192 outside corners.

The exact witness is head corner735, native vertex21411, candidate
polygon245/checkpoint polygon241, source corner ancestry `[723,723,0]`.
The vertex is outside authoring scope and its position remains exactly
pinned. Polygon vertices `[21411,21420,21410]` have archived tangentDOFs
`[0,1,0]`;21420 moves while the other two remain fixed. With raw custom
normal fields unedited, the corner decodes from
`[.29217270016670227,.495890349149704,-.8177578449249268]` to
`[.2922154664993286,.49588340520858765,-.8177467584609985]` at alpha1e−6.

Thus the archived approximate tangent clamps do not preserve the actual
normal decoder. Native Float32 rounding is part of this observation; it is
not a continuous normal Jacobian or a proof of whole-scope infeasibility.

## One proposed operator, without executing it

[The exact formulation](operator-proposal.json) keeps the102 anatomical
screened-biharmonic objective and frozen coefficients. It replaces the
approximate tangent substitute with hard actual decoded-normal equalities,
retains all immutable fields and existing scope pins, and adds collision
constraints. Constrained trust-region SQP may propose steps; only the exact
native Float32 decoder and swept collision qualification can accept them.
Unsupported decoder derivatives or tessellation switches stop the attempt.
Matching endpoint normal bytes alone cannot certify intermediate normals;
a continuous path claim also requires normal invariance throughout the
segment, otherwise only a discrete feasible point can be reported.

The starting geometry already has246 proper crossings. No collision-free
path can include that start. The proposed operator therefore requires an
initial feasible-seed search under the same hard normals and pins, with no
contact waivers, before any collision-free continuation claim. None of the
starting pairs has all its corners scope-pinned or all zero archived tangent
DOF; this simple obstruction is absent, but it proves neither successful
untangling nor a feasible normal-preserving route. No seed, decoded-normal
Jacobian/rank or constrained solve is archived. This formulation remains
unqualified and requires root admission before any execution.

## Evidence and validation

- [Endpoint/source classification and normal probes](path-samples.json)
- [Swept numeric events](chord-events.json)
- [Exact selected root and native witness IDs](exact-path-witnesses.json)
- [All original contact constraints](starting-contact-constraints.json)
- [Pinned diagnostic handoff](handoff.json)

Archived native/source field pins are unchanged. Starting-contact
classification reproduces exactly from archived arrays. Recipe syntax,
JSON parsing, receipt hashes and owned diff whitespace pass. No new game
behavior was changed; third-round ship102 already passed and103 is not a
third round. No new visual or device acceptance is claimed.
