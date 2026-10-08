# Map metadata and attribution

The scoring dataset is synthetic. Map coordinates locate the actual named areas,
independently of the synthetic population and commercial measurements.

`src/geography.json` contains 20 reference points, manually checked on 8 October
2026 against the linked Wikipedia/Wikidata coordinate sources. Each entry carries
its source, precision and a default neighbourhood-scale zoom. These are area
reference points rather than exact property addresses, geometric centroids or
surveyed boundaries. Generic `Zentrum` labels use representative city-centre
coordinates. Linz `Stadtmitte` maps to Innenstadt; Innsbruck `Zentrum` maps to
Innenstadt; Klagenfurt `Innenstadt` maps to Innere Stadt.

`src/district-boundaries.json` contains the official Vienna polygons for districts
1, 7 and 10, retrieved from Stadt Wien's Bezirksgrenzen Wien WFS. Coordinates are
rounded to six decimal places and retain GeoJSON longitude/latitude order.

- Dataset: https://www.data.gv.at/katalog/dataset/2ee6b8bf-6292-413c-bb8b-bd22dbb2ad4b
- Source: https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:BEZIRKSGRENZEOGD&srsName=EPSG:4326&outputFormat=json
- Attribution: Stadt Wien – data.wien.gv.at
- License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)

Other districts have source-backed pins, without an invented boundary polygon.
Map tiles: © OpenStreetMap contributors, https://www.openstreetmap.org/copyright.
The client uses ordinary interactive tiles and makes no geocoding API calls.
