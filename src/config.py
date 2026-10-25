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
    "serpavi": "https://cdn.mivau.gob.es/portal-web-mivau/vivienda/serpavi/2026-03_09_bd_SERPAVI_2011-2024%20-%20DEFINITIVO%20WEB_v2.xlsx",
    "ua_codes_json": "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/69330?nult=1&tip=AM",
    # Comparative chapter: country prices (OECD), country supply (Eurostat),
    # city prices and rents (Eurostat Urban Audit).
    "oecd_house_prices": (
        "https://sdmx.oecd.org/public/rest/data/"
        "OECD.ECO.MPD,DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES,1.0/.A.."
        "?startPeriod=1990&format=csvfile"
    ),
    "eurostat_permits": (
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
        "sts_cobp_a?format=JSON&lang=EN&indic_bt=BPRM_DW"
        "&cpa2_1=CPA_F41001_X_410014&unit=THS"
    ),
    "eurostat_population": (
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
        "demo_pjan?format=JSON&lang=EN&sex=T&age=TOTAL&unit=NR"
    ),
    "eurostat_urban_audit": (
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
        "urb_clivcon?format=JSON&lang=EN"
        "&indic_ur=SA1053V&indic_ur=SA1049V&indic_ur=DE3017V"
    ),
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

# ---------------------------------------------------------------------------
# Comparative chapter: country and city layers
# ---------------------------------------------------------------------------

# OECD series are annual. These codes are aggregates, not countries.
OECD_AGGREGATES = {"EA", "EA17", "EA19", "EA20", "EU27_2020", "OECD"}

# Eurostat uses ISO2 for countries; the OECD uses ISO3. Only the countries
# that appear in at least one of the two sources are listed.
ISO2_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CH": "CHE", "CY": "CYP",
    "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "EL": "GRC",
    "ES": "ESP", "FI": "FIN", "FR": "FRA", "HR": "HRV", "HU": "HUN",
    "IE": "IRL", "IS": "ISL", "IT": "ITA", "LT": "LTU", "LU": "LUX",
    "LV": "LVA", "MT": "MLT", "NL": "NLD", "NO": "NOR", "PL": "POL",
    "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN", "SK": "SVK",
    "TR": "TUR", "UK": "GBR", "RS": "SRB", "ME": "MNE", "MK": "MKD",
    "AL": "ALB", "XK": "XKX", "BA": "BIH",
}

COUNTRY_NAMES = {
    "ALB": "Albania", "AUS": "Australia", "AUT": "Austria", "BEL": "Belgium",
    "BGR": "Bulgaria", "BIH": "Bosnia and Herzegovina", "BRA": "Brazil",
    "CAN": "Canada", "CHE": "Switzerland", "CHL": "Chile", "CHN": "China",
    "COL": "Colombia", "CYP": "Cyprus", "CZE": "Czechia", "DEU": "Germany",
    "DNK": "Denmark", "ESP": "Spain", "EST": "Estonia", "FIN": "Finland",
    "FRA": "France", "GBR": "United Kingdom", "GRC": "Greece", "HRV": "Croatia",
    "HUN": "Hungary", "IDN": "Indonesia", "IND": "India", "IRL": "Ireland",
    "ISL": "Iceland", "ISR": "Israel", "ITA": "Italy", "JPN": "Japan",
    "KOR": "Korea", "LTU": "Lithuania", "LUX": "Luxembourg", "LVA": "Latvia",
    "MEX": "Mexico", "MKD": "North Macedonia",
    "MLT": "Malta", "MNE": "Montenegro", "NLD": "Netherlands",
    "NOR": "Norway", "NZL": "New Zealand", "POL": "Poland", "PRT": "Portugal",
    "ROU": "Romania", "RUS": "Russia", "SAU": "Saudi Arabia", "SRB": "Serbia",
    "SVK": "Slovak Republic", "SVN": "Slovenia", "SWE": "Sweden",
    "TUR": "Türkiye", "USA": "United States", "XKX": "Kosovo",
    "ZAF": "South Africa",
}

# Countries shown in the comparative figures. Spain is always highlighted.
PEER_COUNTRIES = [
    "ESP", "PRT", "FRA", "DEU", "ITA", "NLD", "IRL", "USA",
    "CAN", "POL", "SWE", "DNK", "FIN", "BEL", "AUT", "GBR",
]

# Urban Audit rent unit rule. The label says "annual rent per m2", but some
# countries report monthly values. The raw country medians separate cleanly:
# monthly reporters sit near 8.5 EUR/m2, annual reporters at 41 EUR/m2 or more.
CITY_RENT_MONTHLY_THRESHOLD = 20.0

# Latvia is excluded from the comparable city sample: its four cities imply
# yields from 2.3% to 17.8% under a single unit, so the series is internally
# inconsistent rather than merely mislabelled.
CITY_COUNTRY_EXCLUDE = {"LV"}
