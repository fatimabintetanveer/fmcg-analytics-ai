# Default Settings
DEFAULT_ORG_ID = 4
DEFAULT_DATA_TYPE_ID = 104
DEFAULT_REPORTED_DATA_END = "2026-03-01"

# Database to Frontend Column Mapping
COLUMN_MAPPING = {
    "DimProduct__ph_5": "Brand",
    "DimProduct__ph_2": "Category",
    "DimProduct__ph_13": "Pack Size",
    "DimGeography__h1_6": "City",
    "DimGeography__h1_4": "Retailer",
    "Fact__reporteddate": "Date",
    "DimTimePeriod__label": "Time Period"
}
