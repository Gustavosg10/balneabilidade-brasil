import json
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.parse

# Novo endpoint oficial e atualizado da CETESB
BASE_URL = "https://arcgis.cetesb.sp.gov.br/server/rest/services/Hosted/Praias/FeatureServer/0/query"

PARAMS = {
    "where": "1=1",
    "outFields": "municipio,praia,ugrhi,classificacao_texto,qualidade,data_amostra_inicio,data_amostra_final,data_atual,ordem,id_praia",
    "orderByFields": "ordem ASC",
    "returnGeometry": "false",
    "f": "json",
}

FUSO_BR = timezone(timedelta(hours=-3))


def formatar_data_ms(timestamp_ms):
    """Converte timestamp em milissegundos do ArcGIS para DD/MM/YYYY (UTC-3)."""
    if not timestamp_ms:
        return None
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=FUSO_BR)
    return dt.strftime("%d/%m/%Y")


def coletar_balneabilidade():
    query_string = urllib.parse.urlencode(PARAMS)
    url_completa = f"{BASE_URL}?{query_string}"

    req = urllib.request.Request(
        url_completa,
        headers={"User-Agent": "Mozilla/5.0 (DestinoABordo-Bot/1.0)"},
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    features = payload.get("features", [])
    if not features:
        raise RuntimeError("A API da CETESB retornou 0 registros. Abortando para manter o JSON anterior intacto.")

    municipios = {}
    data_boletim = None

    for item in features:
        attr = item.get("attributes", {})
        municipio = (attr.get("municipio") or "").strip()
        if not municipio:
            continue

        data_pub = formatar_data_ms(attr.get("data_atual"))
        if data_pub and not data_boletim:
            data_boletim = data_pub

        registro_praia = {
            "id": attr.get("id_praia"),
            "ordem": attr.get("ordem"),
            "praia": (attr.get("praia") or "").strip(),
            "ugrhi": (attr.get("ugrhi") or "").strip(),
            "status": (attr.get("classificacao_texto") or "").strip(),
            "propria": bool(attr.get("qualidade") == 1),
            "amostra_inicio": formatar_data_ms(attr.get("data_amostra_inicio")),
            "amostra_final": formatar_data_ms(attr.get("data_amostra_final")),
            "atualizado_em": data_pub,
        }

        municipios.setdefault(municipio, []).append(registro_praia)

    saida = {
        "fonte": "CETESB - Companhia Ambiental do Estado de São Paulo",
        "boletim_data": data_boletim,
        "gerado_em_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_praias": len(features),
        "municipios": municipios,
    }

    with open("balneabilidade.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"Sucesso! {len(features)} praias salvas em balneabilidade.json (Boletim: {data_boletim}).")


if __name__ == "__main__":
    coletar_balneabilidade()
