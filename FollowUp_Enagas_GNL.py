from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import os
import pandas as pd
import requests

CSV_FILE = "historico_gnl.csv"

BASE_URL = (
    "https://www.enagas.es/content/enagas/es/gestion-tecnica-sistema/"
    "energy-data/parametros-fisicos/capacidades-tecnicas-flujos-fisicos/"
    "seguimiento-diario-sistema/jcr:content/responsiveGrid/"
    "dailysystemtracking.dailysystemtrackingdto.xls"
)


def obtener_fecha_fin():

    hoy = datetime.now(
        ZoneInfo("Europe/Madrid")
    ).date()

    return hoy - timedelta(days=1)


def obtener_fecha_inicio():

    historico = pd.read_csv(CSV_FILE)

    if historico.empty:
        return datetime(2025, 1, 1).date()

    historico["Fecha"] = pd.to_datetime(
        historico["Fecha"]
    )

    return (
        historico["Fecha"].max().date()
        + timedelta(days=1)
    )


def construir_url(fecha):

    return (
        f"{BASE_URL}?date="
        f"{fecha.strftime('%d/%m/%Y')}"
    )

def descargar_y_extraer(fecha):

    fecha_txt = fecha.strftime("%Y-%m-%d")

    url = construir_url(fecha)

    print(f"Procesando {fecha_txt}")

    r = requests.get(url, timeout=60)
    r.raise_for_status()

    with open("temp.xls", "wb") as f:
        f.write(r.content)

    df = pd.read_excel(
        "temp.xls",
        header=None
    )

    registro = {
        "Fecha": fecha_txt
    }

    terminales = {
        "TOTAL": 4,
        "BARCELONA": 5,
        "CARTAGENA": 6,
        "HUELVA": 7,
        "BBG": 8,
        "SAGUNTO": 9,
        "REGANOSA": 10,
        "MUSEL": 11
    }

    for terminal, col in terminales.items():

        registro[f"{terminal}_Exist_Inicial_GWh"] = df.iloc[23, col]
        registro[f"{terminal}_Exist_Inicial_m3"] = df.iloc[24, col]

        registro[f"{terminal}_Cargas_GNL"] = df.iloc[25, col]

        registro[f"{terminal}_Descargas_GNL"] = df.iloc[26, col]

        registro[f"{terminal}_Regasificacion_GWh"] = df.iloc[27, col]
        registro[f"{terminal}_Regasificacion_m3"] = df.iloc[28, col]

        registro[f"{terminal}_Carga_Cisternas"] = df.iloc[29, col]

        registro[f"{terminal}_Exist_Final_GWh"] = df.iloc[30, col]
        registro[f"{terminal}_Exist_Final_m3"] = df.iloc[31, col]

        registro[f"{terminal}_Pct_Llenado"] = df.iloc[32, col]

    return registro

def guardar_historico(historico):

    historico = historico.loc[
        :,
        ~historico.columns.str.contains("^Unnamed")
    ]

    historico.to_csv(
        CSV_FILE,
        index=False,
        encoding="utf-8-sig"
    )


def main():

    inicio = obtener_fecha_inicio()

    fin = obtener_fecha_fin()

    if inicio > fin:
        print("No hay fechas nuevas")
        return

    historico = pd.read_csv(CSV_FILE)

    nuevos = []

    fecha = inicio

    while fecha <= fin:

        try:

            nuevos.append(
                descargar_y_extraer(fecha)
            )

        except Exception as e:

            print(
                f"Error {fecha}: {e}"
            )

        fecha += timedelta(days=1)

    if nuevos:

        nuevos_df = pd.DataFrame(nuevos)

        resultado = pd.concat(
            [
                historico,
                nuevos_df
            ],
            ignore_index=True
        )

        resultado = resultado.drop_duplicates(
            subset=["Fecha"],
            keep="last"
        )

        resultado = resultado.sort_values("Fecha")

        resultado.to_csv(
            CSV_FILE,
            index=False,
            encoding="utf-8-sig"
        )


if __name__ == "__main__":
    main()
