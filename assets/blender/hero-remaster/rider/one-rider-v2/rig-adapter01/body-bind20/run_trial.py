"""One CPU construction; preserve any stopped diagnostic before export."""
from pathlib import Path
import json,traceback
import numpy as np
base=Path(__file__).resolve().parent
context={'__file__':str(base/'build_graft.py'),'__name__':'__main__'}
try:
    exec(compile((base/'build_graft.py').read_text(),str(base/'build_graft.py'),'exec'),context)
except SystemExit:
    raise
except Exception as error:
    evidence=context.get('EVIDENCE');out=context.get('OUT')
    if evidence:
        payload={'status':'REJECTED before export at CPU construction guard','exception':type(error).__name__,
            'detail':str(error),'traceback':traceback.format_exc(),'candidateExported':False,'GPUWorkPerformed':False}
        (evidence/'construction-guard-failure.json').write_text(json.dumps(payload,indent=2)+'\n')
    if out:
        keys=['positions','output','bridge','v','tri','current','nt','join','wall']
        data={key:np.asarray(context[key]) for key in keys if key in context and np.asarray(context[key]).dtype!=object}
        np.savez_compressed(out/'construction-guard-failure.npz',**data)
    raise
