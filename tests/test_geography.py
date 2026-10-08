"""Keep map metadata aligned with the synthetic ranking dataset."""
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
GEOGRAPHY = json.loads((ROOT / 'frontend/src/geography.json').read_text())
BOUNDARIES = json.loads((ROOT / 'frontend/src/district-boundaries.json').read_text())


def test_every_candidate_has_a_sourced_map_point():
    municipalities = json.loads((ROOT / 'data/municipalities.json').read_text())['municipalities']
    assert set(GEOGRAPHY) == {item['gemeinde'] for item in municipalities}
    for point in GEOGRAPHY.values():
        assert 46.3 < point['lat'] < 49.1
        assert 9.4 < point['lon'] < 17.2
        assert point['source'].startswith('https://')
        assert point['precision'] in {'district', 'city-centre'}


@pytest.mark.parametrize('names', [
    ['Wien (1., Innere Stadt)', 'Wien (7., Neubau)', 'Wien (10., Favoriten)'],
    ['Graz (Innere Stadt)', 'Graz (Lend)'],
    ['Linz (Stadtmitte)', 'Linz (Urfahr)'],
    ['Innsbruck (Zentrum)', 'Innsbruck (Wilten)'],
    ['Salzburg (Altstadt)', 'Salzburg (Lehen)'],
])
def test_districts_do_not_share_a_generic_city_pin(names):
    assert len({(GEOGRAPHY[name]['lat'], GEOGRAPHY[name]['lon']) for name in names}) == len(names)


def test_vienna_boundaries_use_geojson_longitude_latitude_order():
    assert len(BOUNDARIES) == 3
    for name, feature in BOUNDARIES.items():
        assert name in GEOGRAPHY
        assert feature['geometry']['type'] == 'Polygon'
        ring = feature['geometry']['coordinates'][0]
        assert ring[0] == ring[-1]
        for lon, lat in ring:
            assert 16.1 < lon < 16.6
            assert 48 < lat < 48.4
