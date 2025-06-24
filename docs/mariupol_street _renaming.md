# Comprehensive Mariupol Street Naming Documentation

## Executive Summary

Russian occupation authorities have systematically renamed streets in Mariupol since May 2022 as part of a broader cultural erasure campaign. This documentation reveals sophisticated address manipulation tactics designed to deny Ukrainian property rights while facilitating Russian settlement. The evidence shows **over 500 buildings demolished** with strategic address changes affecting compensation claims, supported by a comprehensive technical framework for building evidence databases.

## Database Construction Framework

### Pre-2022 Ukrainian Street Database

**Primary Sources Identified:**
- **Ukrainian State Land Cadastre**: Contains official street addresses and cadastral numbers, though public access restricted since 2022 for security
- **OpenStreetMap Historical Data**: Complete changeset history available through February 2022 with Ukrainian names and coordinates
- **Mariupol City Administration**: Municipal records archived at mariupolrada.gov.ua before occupation
- **Ukrainian Institute of National Memory**: Toponymic research covering 2,897 renamed objects across 36 cities

**Major Streets Documented:**
- Miru Avenue (Миру проспект) - central boulevard
- Metalurhiv Avenue (Металургів проспект) 
- Nakhimov Avenue (Нахімова проспект)
- Azovstalska Street (Азовсталь вулиця)
- Nezalezhnosti Square (Площа Незалежності)
- Peremohy Square (Площа Перемоги)

### Post-2022 Russian Occupation Changes

**Systematic Renaming Campaign:**
- **Freedom Square** → **Lenin Square** (ideological reversal)
- **Myru Avenue** → **Lenin Avenue** (Soviet symbolic imposition)
- **Azovstalska Street** → **Tula Street** (Russian geographic appropriation)
- **Administrative Authority**: Denis Pushilin (DPR Head) issued systematic renaming decrees

**Timeline of Changes:**
- May 2022: Russian forces gain control
- August 2023: Systematic street renaming implementation
- Ongoing: Continued cultural marker replacement

## Geographic Coordinates and Mapping Solutions

### Ukrainian Coordinate System: UCS-2000
- **EPSG Code**: 6387 for Mariupol (Zone 13, central meridian 39°E)
- **Transformation**: dx=24, dy=-121, dz=-76 meters to WGS84  
- **Accuracy**: ±1 meter for regional applications

### Recommended Open-Source Tools
**QGIS Platform** with specialized plugins:
- QuickOSM for historical street data integration
- TimeManager for temporal analysis of changes
- Sentinel Hub API for satellite imagery verification

**Database Architecture:**
```sql
CREATE TABLE street_changes (
    id SERIAL PRIMARY KEY,
    osm_way_id BIGINT,
    old_name_ukrainian VARCHAR(255),
    new_name_russian VARCHAR(255),
    change_date DATE,
    coordinates GEOMETRY(LINESTRING, 4326),
    evidence_links TEXT[]
);
```

## Address Manipulation Tactics

### Documented Case Study: Property Seizure Through Address Changes

**Specific Example**: Проспект Нахимова, 82 → Черноморский переулок 1б
- **Methodology**: Building demolished, new construction assigned different street address
- **Legal Impact**: Residents cannot prove ownership when fundamental address identifiers are altered
- **Victim Testimony**: "Our house, where we lived for many years, is gone. We've been abandoned—they're not giving us apartments"

**Systematic Pattern**: 
- **459 buildings** officially marked for demolition as of May 2023
- **Prime real estate** near sea targeted for Russian settler housing
- **30-day requirement** with Russian passports to reclaim property

### Criminal Implications

**War Crimes Classification:**
- Systematic property appropriation constitutes "pillage" under Rome Statute
- Violations of Fourth Geneva Convention regarding occupied territories
- Potential crimes against humanity under forced displacement provisions

## Official Ukrainian Sources for Baseline Data

### Primary Government Portals
- **State Land Cadastre** (cadastral.gov.ua): Official property registration system
- **National Data Portal** (data.gov.ua): 80,000+ datasets pre-2022 (limited wartime access)
- **Ukrainian Institute of National Memory**: Decommunization documentation

### Academic Documentation
- **Comprehensive studies** by Oleksiy Gnatiuk and Anatoliy Melnychuk covering 36 Ukrainian cities
- **2,897 renamed objects** documented during 2014-2017 decommunization period
- **Municipal council resolutions** providing legal framework for name changes

## Russian Occupation Administration Decrees

### Key Administrative Actions
- **March 31, 2022**: Pushilin Decree establishing Mariupol administration under DPR control
- **April 26, 2022**: Medal creation decree for "Liberation of Mariupol"
- **Systematic implementation**: Reversal of Ukrainian decommunization efforts from 2016

### Cultural Replacement Strategy
- **Soviet nostalgia**: Heavy emphasis on Lenin and Soviet-era figures
- **Russian geographic names**: Tula and other Russian cities
- **Ideological markers**: Removal of democratic concepts (Freedom → Lenin)

## Patterns of Cultural Erasure

### Systematic Toponymic Manipulation

**Three-Stage Process:**
1. **Deconstruction**: Removing Ukrainian cultural markers
2. **Displacement**: Installing Russian/Soviet replacements
3. **Naturalization**: Making new names administratively necessary

**Targeted Categories:**
- **Industrial heritage**: Azovstal (symbol of Ukrainian resistance)
- **Linguistic identity**: Ukrainian language street names
- **Democratic values**: Freedom, Peace concepts
- **Local history**: Mariupol-specific cultural markers

### Historical Precedents
- **Francoist Spain**: Systematic renaming from regional languages to Spanish
- **Nazi/Soviet Europe**: Successive regime toponymic impositions
- **Palestine/Israel**: Superimposition of dominant cultural names
- **Post-Yugoslav conflicts**: Ethnic cleansing accompanied by systematic renaming

## Property Seizure Database Correlations

### Documented Correlation Patterns
- **Address changes coincide** with property seizures from Ukrainian owners
- **Premium locations** (sea views, central districts) systematically targeted
- **New addresses assigned** to properties sold to Russian buyers
- **Bureaucratic warfare**: Russian passport requirements for property claims

### Legal Circumvention Tactics
- **Properties declared "ownerless"** through administrative manipulation
- **Original addresses erased** from official records
- **Lawsuits invalidated** when "original address no longer exists"
- **Compensation claims denied** due to inability to prove ownership

## Implementation Recommendations

### Technical Infrastructure
**Database Platform**: PostgreSQL with PostGIS extension
**Coordinate System**: UCS-2000 (EPSG:6387) with WGS84 transformation
**API Integration**: Sentinel Hub for satellite verification, OSM Overpass for historical data

### Evidence Collection Framework
**Multiple Source Verification**: Cross-reference OSM, satellite imagery, and field reports
**Temporal Consistency**: Validate change dates across sources
**Chain of Custody**: Maintain audit trail for legal admissibility
**Digital Forensics**: Cryptographic verification of data integrity

### Quality Assurance
- **Witness Documentation**: Interview displaced residents for name confirmation
- **Photographic Evidence**: Collect pre-2022 street sign imagery
- **Academic Validation**: Cross-reference with Ukrainian toponymic research
- **International Monitoring**: Coordinate with human rights organizations

## Conclusion

The systematic street renaming in occupied Mariupol represents a sophisticated campaign of cultural genocide operating across legal, administrative, and cultural domains. The documented address manipulation tactics facilitate property seizures while erasing Ukrainian identity markers. This comprehensive framework provides the foundation for building evidence databases that can support legal accountability, property rights restoration, and cultural preservation efforts.

The technical infrastructure outlined—combining Ukrainian coordinate systems, open-source GIS tools, and forensic documentation methods—creates a robust foundation for systematic evidence collection. The correlation between address changes and property seizures reveals criminal implications that extend beyond cultural erasure to systematic theft of Ukrainian property rights.

This documentation serves as both a historical record and a practical framework for future accountability efforts when Ukrainian sovereignty is restored to occupied territories.