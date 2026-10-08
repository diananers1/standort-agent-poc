"""HTTP interface and single-service frontend hosting for the interview demo."""
import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from standort_agent.models import BusinessProfile
from standort_agent.loader import load_municipalities
from standort_agent.graph.workflow import location_graph
from standort_agent.interpretation.rules import profile_input_errors
from standort_agent.scoring.weighting import get_weights
from standort_agent.reporting.explanation import explain_for_customer
from standort_agent.reporting.report import generate_html_report
from standort_agent.reporting.names import format_location_text

ROOT = Path(__file__).resolve().parents[2]
DATA = load_municipalities(ROOT / 'data/municipalities.json')
app = FastAPI(title='Standort location intelligence')
analysis_lock = Lock()

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.get('/api/config')
def config():
    return {'regions': ['Österreich', *sorted({m.bundesland for m in DATA.municipalities} | {m.gemeinde.split('(', 1)[0].strip() for m in DATA.municipalities})],
            'locations': len(DATA.municipalities), 'states': len({m.bundesland for m in DATA.municipalities}), 'data_date': 'June 2026'}

def event(payload):
    return format_location_text(json.dumps(payload, ensure_ascii=False)) + '\n'

@app.post('/api/analyze')
def analyze(profile: BusinessProfile):
    errors = profile_input_errors(profile)
    if errors:
        raise HTTPException(422, detail=' '.join(errors))
    if not analysis_lock.acquire(blocking=False):
        raise HTTPException(429, detail='Another analysis is running. Please try again shortly.')

    def stream():
        try:
            yield event({'type': 'progress', 'stage': 'Validating your business profile'})
            final = {}
            for update in location_graph.stream({'raw_profile': profile, 'municipalities': DATA.municipalities}, stream_mode='updates'):
                for node, value in update.items():
                    value = value or {}
                    final.update(value)
                    if value.get('error'):
                        yield event({'type': 'error', 'message': value['error']})
                        return
                    stages = {'validate_scope': 'Interpreting your business profile', 'interpret_profile': 'Finding matching regions', 'filter_region': 'Evaluating four location signals', 'evaluate_locations': 'Preparing specialist explanations', 'llm_analysis': 'Building your recommendation'}
                    yield event({'type': 'progress', 'stage': stages.get(node, 'Analyzing locations')})
            rankings = final.get('rankings', [])
            if not rankings:
                yield event({'type': 'error', 'message': 'No matching locations. Try another region.'})
                return
            explanation = final.get('customer_explanation') or explain_for_customer(profile, rankings[0])
            with TemporaryDirectory() as folder:
                report = generate_html_report(profile, rankings, Path(folder) / 'report.html', explanation, final.get('llm_status'))
                html = report.read_text(encoding='utf-8')
            yield event({'type': 'result', 'data': {'rankings': [r.model_dump() for r in rankings], 'weights': get_weights(final['interpreted_profile']), 'explanation': explanation, 'llm_status': final.get('llm_status', 'Rule-based explanations'), 'profile': profile.model_dump(), 'report_html': html}})
        except Exception:
            logging.exception('Analysis failed')
            yield event({'type': 'error', 'message': 'The analysis could not complete. Please try again.'})
        finally:
            analysis_lock.release()
    return StreamingResponse(stream(), media_type='application/x-ndjson', headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})

from pydantic import BaseModel, Field
from standort_agent.interpretation.rules import interpret_profile
from standort_agent.graph.workflow import filter_region_node, evaluate_locations_node

class ScenarioPriorities(BaseModel):
    demographics: float = Field(ge=0, le=100)
    poi: float = Field(ge=0, le=100)
    rent: float = Field(ge=0, le=100)
    transit: float = Field(ge=0, le=100)

class ScenarioRequest(BaseModel):
    profile: BusinessProfile
    priorities: ScenarioPriorities

@app.post('/api/scenario')
def scenario(request: ScenarioRequest):
    errors = profile_input_errors(request.profile)
    if errors:
        raise HTTPException(422, detail=' '.join(errors))
    priorities = request.priorities.model_dump()
    total = sum(priorities.values())
    if total <= 0:
        raise HTTPException(422, detail='Give at least one priority a value above zero.')
    weights = {key: value / total for key, value in priorities.items()}
    state = {'interpreted_profile': interpret_profile(request.profile), 'municipalities': DATA.municipalities}
    state.update(filter_region_node(state))
    if state.get('error'):
        raise HTTPException(422, detail=state['error'])
    rankings = evaluate_locations_node(state)['rankings']
    for result in rankings:
        result.total_score = sum(result.signals[key].score * weight for key, weight in weights.items())
    rankings.sort(key=lambda result: result.total_score, reverse=True)
    return json.loads(format_location_text(json.dumps({'rankings': [result.model_dump() for result in rankings], 'weights': weights}, ensure_ascii=False)))

DIST = ROOT / 'frontend/dist'
if DIST.exists():
    app.mount('/assets', StaticFiles(directory=DIST / 'assets'), name='assets')

@app.get('/standora-mark.svg', include_in_schema=False)
def brand_mark():
    return FileResponse(DIST / 'standora-mark.svg', media_type='image/svg+xml')

@app.get('/how-it-works', include_in_schema=False)
@app.get('/', include_in_schema=False)
def index():
    if not DIST.exists():
        raise HTTPException(503, 'Build the frontend first: cd frontend && npm ci && npm run build')
    return FileResponse(DIST / 'index.html')
