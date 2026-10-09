"""Parent-guarded frozen67 proof with complete saved-stage witness readback.

--python native-proof.py -- NEW_NATIVE68_PROOF_DIRECTORY
No Blender import or scene read until main; frozen67 files stay unchanged.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import witness68 as w


def adapted_source():
    source=w.NATIVE67.read_text()
    patches=[
        ('import proof as p','import witness68 as p'),
        ("p.ROOT/'harness/out/rider-rebuild/selected-boot-surface67'", "p.ROOT/'harness/out/rider-rebuild/selected-boot-witness68'"),
        ("'recipeSHA256':p.sha(__file__),'proofRecipeSHA256':p.sha(p.__file__),",
         "'recipeSHA256':p.sha(__file__),'proofRecipeSHA256':p.sha(p.__file__),\n        'nativeProofAncestry67':p.pin(p.NATIVE67,p.NATIVE67_SHA),'proofValidatorAncestry67':p.pin(p.PROOF67,p.PROOF67_SHA),"),
        ("before=witness.retained(sources,rig);assert before==json.loads(p.PRODUCTION.read_text())['sourceWitness'];report['sourceWitnessExact']=True",
         "before=witness.retained(sources,rig);expected=json.loads(p.PRODUCTION.read_text())['sourceWitness']\n        report['sourceWitnessReadback']=p.persist_comparison(out,before,expected,'before-native-proof')\n        report['status']='PARTIAL_NATIVE68_FULL_WITNESS_SAVED_BEFORE_ASSERT';write()\n        assert report['sourceWitnessReadback']['equal'], ('Saved-stage source witness mismatch',report['sourceWitnessReadback'])\n        report['sourceWitnessExact']=True"),
        ("report['sourceWitnessUnchangedAfterProbe']=before==witness.retained(sources,rig)",
         "after=witness.retained(sources,rig)\n        report['sourceWitnessUnchangedAfterProbe']=before==after\n        report['sourceWitnessAfterReadback']=p.persist_comparison(out,after,expected,'after-native-proof')\n        report['status']='PARTIAL_NATIVE68_AFTER_WITNESS_SAVED_BEFORE_VALIDATION';write()"),
    ]
    for old,new in patches:
        assert source.count(old)==1,('Frozen67 witness adapter drift',old);source=source.replace(old,new)
    source=source.replace('PARTIAL_NATIVE67_','PARTIAL_NATIVE68_').replace('REJECTED_OR_INCOMPLETE_NATIVE67_PROOF','REJECTED_OR_INCOMPLETE_NATIVE68_PROOF')
    return source


def main():
    source=adapted_source()
    namespace={'__file__':str(Path(__file__).resolve()),'__name__':'native68_saved_stage_witness'}
    exec(compile(source,str(w.NATIVE67)+'[witness68]','exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
