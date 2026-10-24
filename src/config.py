"""Shared configuration for the housing / land-classification project."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SIU = RAW / "siu"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"

for d in (RAW, SIU, PROC, OUT, TABLES, FIGURES):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

URLS = {
    "siu_zip": "https://cdn.mivau.gob.es/portal-web-mivau/urbanismo-suelo/Datos%20alfanumericos%20SIU%20-%20Excel%20-%2020260619.zip",
    "ua_69330": "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/69330.csv",
    "ipva_59060": "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/59060.csv",
    "dpop_29005": "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/29005.csv",
    "ua_codes_json": "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/69330?nult=1&tip=AM",
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) portfolio-research"

# ---------------------------------------------------------------------------
# INE Urban Indicators (table 69330): exact labels -> short names
# ---------------------------------------------------------------------------

UA_INDICATORS = {
    "Alquiler anual medio por metro cuadrado (Euros/m2)": "rent_m2_year",
    "Alquiler mensual medio (Euros)": "rent_month",
    "Mediana del alquiler anual por metro cuadrado (Euros/m2)": "rent_median_m2_year",
    "Mediana del alquiler mensual (Euros)": "rent_median_month",
    "Primer cuartil del alquiler anual por metro cuadrado (Euros/m2)": "rent_q1_m2_year",
    "Tercer cuartil del alquiler anual por metro cuadrado (Euros/m2)": "rent_q3_m2_year",
    "Precio medio de la vivienda (Euros)": "price_mean",
    "Precio medio por metro cuadrado de la vivienda (Euros/m2)": "price_m2",
    "Precio medio por metro cuadrado de la vivienda tipo piso (Euros/m2)": "price_flat_m2",
    "Número de viviendas convencionales según Catastro (Número)": "stock_catastro",
    "Número de viviendas convencionales según Censo (Número)": "stock_census",
    "Proporción de viviendas vacías (Porcentaje)": "vacancy_rate",
    "Número total de hogares (Número)": "households",
    "Tamaño medio de los hogares (Número)": "household_size",
    "Proporción de hogares de una persona sobre el total de hogares (Porcentaje)": "one_person_share",
}

# Names that do not match the Padrón list token-for-token. Verified by hand.
MANUAL_CODE = {
    "Castelló de la Plana": "12040",
    "Palma de Mallorca": "07040",
}

# ---------------------------------------------------------------------------
# Provinces
# ---------------------------------------------------------------------------

PROVINCES = {
    "01": "Álava", "02": "Albacete", "03": "Alicante", "04": "Almería",
    "05": "Ávila", "06": "Badajoz", "07": "Baleares", "08": "Barcelona",
    "09": "Burgos", "10": "Cáceres", "11": "Cádiz", "12": "Castellón",
    "13": "Ciudad Real", "14": "Córdoba", "15": "A Coruña", "16": "Cuenca",
    "17": "Girona", "18": "Granada", "19": "Guadalajara", "20": "Gipuzkoa",
    "21": "Huelva", "22": "Huesca", "23": "Jaén", "24": "León",
    "25": "Lleida", "26": "La Rioja", "27": "Lugo", "28": "Madrid",
    "29": "Málaga", "30": "Murcia", "31": "Navarra", "32": "Ourense",
    "33": "Asturias", "34": "Palencia", "35": "Las Palmas",
    "36": "Pontevedra", "37": "Salamanca", "38": "S. C. de Tenerife",
    "39": "Cantabria", "40": "Segovia", "41": "Sevilla", "42": "Soria",
    "43": "Tarragona", "44": "Teruel", "45": "Toledo", "46": "Valencia",
    "47": "Valladolid", "48": "Bizkaia", "49": "Zamora", "50": "Zaragoza",
    "51": "Ceuta", "52": "Melilla",
}

# Coastal provinces (for a robustness check on tourism / second homes).
COASTAL_PROVINCES = {
    "03", "04", "07", "08", "11", "12", "15", "17", "21", "27", "29",
    "35", "36", "38", "39", "43", "46", "51", "52",
}
