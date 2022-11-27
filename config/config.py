_config = {
    "DEFAULT": {
        "ServerAliveInterval": 45,
    },
    "table_path": {
        "FEATURE_TABLE": "./config/features.csv",
        "TRANSFORMATION_TABLE": "./config/transformation.csv"
    },
    "fhir_server": {
        "FHIR_SERVER_URL": "http://ming-desktop.ddns.net:8192/fhir",
    },
}

configObject = _config
