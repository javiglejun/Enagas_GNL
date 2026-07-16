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

    print(df.iloc[22:34, 2:12])

    datos = df.iloc[22:34, 2:12]

    registro = {
        "Fecha": fecha_txt
    }

    for fila in range(datos.shape[0]):

        concepto = str(
            datos.iloc[fila, 0]
        ).strip()

        unidad = str(
            datos.iloc[fila, 1]
        ).strip()

        nombre_fila = (
            concepto
            .replace(".", "")
            .replace(" ", "_")
            .replace("%", "Pct")
        )

        for col, terminal in zip(
            range(2, 10),
            [
                "TOTAL",
                "BARCELONA",
                "CARTAGENA",
                "HUELVA",
                "BBG",
                "SAGUNTO",
                "REGANOSA",
                "MUSEL",
            ]
        ):

            registro[
                f"{terminal}_{nombre_fila}_{unidad}"
            ] = datos.iloc[fila, col]

    return registro


def guardar_historico(df):

    df.to_csv(
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

        resultado.to_csv(
            CSV_FILE,
            index=False,
            encoding="utf-8-sig"
        )


if __name__ == "__main__":
    main()
