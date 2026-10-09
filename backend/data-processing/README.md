# Data processing boundary
Keep geospatial processing separate from the frontend. Future jobs should publish validated GeoJSON FeatureCollections and normalized JSON statistics.
GeoJSON layers need properties.source and properties.isDemo plus stable feature IDs, provenance, acquisition dates, processing version, and uncertainty.
Result JSON needs region, settlement, dates.before/after, exposure.settlement, exposure.road, uncertainty[], missingData[], analysisStatus, sourceLabel, and roads[]. Keep missingData distinct from processed status none.
Do not add real NISAR identifiers or measurements until a reproducible processing pipeline and provenance are available.
