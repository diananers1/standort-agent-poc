import json
from fastapi.testclient import TestClient
from standort_agent.api import app

client = TestClient(app)
PROFILE = {'branche': 'retail', 'flaeche_m2': 200, 'zielgruppe': 'young_professionals', 'budget_miete_eur': 4000, 'region_praeferenz': ['Österreich']}

def test_configuration_and_health():
    assert client.get('/api/health').json()['status'] == 'ok'
    assert client.get('/api/config').json()['locations'] == 20

def test_streamed_analysis_and_private_report(monkeypatch):
    monkeypatch.setenv('STANDORT_LLM_MODE', 'offline')
    response = client.post('/api/analyze', json=PROFILE)
    events = [json.loads(line) for line in response.text.splitlines()]
    assert response.status_code == 200
    assert events[0]['type'] == 'progress'
    result = events[-1]['data']
    assert len(result['rankings']) == 20
    assert sum(result['weights'].values()) == 1
    assert 'Offline' in result['llm_status']
    assert result['rankings'][0]['municipality']['gemeinde'] in result['report_html']
    assert '<html' in result['report_html']

def test_invalid_profiles_and_regions():
    assert client.post('/api/analyze', json=PROFILE | {'flaeche_m2': -1}).status_code == 422
    assert client.post('/api/analyze', json=PROFILE | {'region_praeferenz': ['Berlin']}).status_code == 422

def test_concurrent_analysis_rejected():
    from standort_agent.api import analysis_lock
    analysis_lock.acquire()
    try:
        assert client.post('/api/analyze', json=PROFILE).status_code == 429
    finally:
        analysis_lock.release()

def test_methodology_direct_navigation(monkeypatch, tmp_path):
    import standort_agent.api as api
    (tmp_path / 'index.html').write_text('<html><body>Application shell</body></html>')
    monkeypatch.setattr(api, 'DIST', tmp_path)
    for path in ['/', '/how-it-works']:
        response = client.get(path)
        assert response.status_code == 200
        assert 'Application shell' in response.text
        assert response.headers['content-type'].startswith('text/html')

def test_scenario_matches_original_and_recalculates_budget(monkeypatch):
    monkeypatch.setenv('STANDORT_LLM_MODE', 'offline')
    original = json.loads(client.post('/api/analyze', json=PROFILE).text.splitlines()[-1])['data']
    priorities = {key: value * 100 for key, value in original['weights'].items()}
    response = client.post('/api/scenario', json={'profile': PROFILE, 'priorities': priorities})
    assert response.status_code == 200
    assert response.json()['rankings'] == original['rankings']
    cheaper = client.post('/api/scenario', json={'profile': PROFILE | {'budget_miete_eur': 1000}, 'priorities': priorities}).json()
    assert {r['municipality']['gemeinde'] for r in cheaper['rankings']} == {r['municipality']['gemeinde'] for r in original['rankings']}
    assert cheaper['rankings'][0]['total_score'] < original['rankings'][0]['total_score']
    for r in cheaper['rankings']:
        assert r['total_score'] == sum(r['signals'][key]['score'] * weight for key, weight in cheaper['weights'].items())


def test_scenario_priorities_validation_and_region_filter():
    priorities = {'demographics': 0, 'poi': 0, 'rent': 100, 'transit': 0}
    data = client.post('/api/scenario', json={'profile': PROFILE | {'region_praeferenz': ['Wien']}, 'priorities': priorities}).json()
    assert all(r['municipality']['bundesland'] == 'Wien' for r in data['rankings'])
    assert all(r['total_score'] == r['signals']['rent']['score'] for r in data['rankings'])
    for invalid in [dict.fromkeys(priorities, 0), priorities | {'rent': -1}, priorities | {'rent': 101}, priorities | {'rent': 'NaN'}]:
        assert client.post('/api/scenario', json={'profile': PROFILE, 'priorities': invalid}).status_code == 422
