import json
from pathlib import Path

def count_geocoded_properties(geojson_path):
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_features = len(data['features'])
    
    # Count features with valid coordinates
    geocoded_count = 0
    null_geometry = 0
    invalid_coords = 0
    
    for feature in data['features']:
        if feature.get('geometry') is None:
            null_geometry += 1
            continue
            
        coords = feature['geometry'].get('coordinates')
        if not coords:
            invalid_coords += 1
        elif len(coords) == 2 and all(isinstance(x, (int, float)) for x in coords):
            geocoded_count += 1
        else:
            invalid_coords += 1
    
    return {
        'total': total_features,
        'geocoded': geocoded_count,
        'null_geometry': null_geometry,
        'invalid_coords': invalid_coords
    }

if __name__ == "__main__":
    geojson_path = Path("data/processed/geocoded_properties.geojson")
    if not geojson_path.exists():
        print(f"Error: File not found: {geojson_path}")
    else:
        stats = count_geocoded_properties(geojson_path)
        
        print(f"Geocoding Statistics:")
        print(f"- Total properties: {stats['total']}")
        print(f"- Successfully geocoded: {stats['geocoded']} ({(stats['geocoded']/stats['total'])*100:.1f}%)")
        print(f"- Null geometry: {stats['null_geometry']} ({(stats['null_geometry']/stats['total'])*100:.1f}%)")
        print(f"- Invalid coordinates: {stats['invalid_coords']} ({(stats['invalid_coords']/stats['total'])*100:.1f}%)")
        print(f"- Failed to geocode: {stats['total'] - stats['geocoded']} ({((stats['total'] - stats['geocoded'])/stats['total'])*100:.1f}%)")
