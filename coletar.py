import json
from datetime import datetime
import requests

# Endpoint oficial da CETESB (Mapa de Balneabilidade SP)
URL_CETESB = "https://services2.arcgis.com/24782468/arcgis/rest/services/Balneabilidade/FeatureServer/0/query?where=1%3D1&outFields=*&f=json"


def limpar_slug(texto):
  substituicoes = {
      "ã": "a",
      "á": "a",
      "à": "a",
      "â": "a",
      "é": "e",
      "ê": "e",
      "í": "i",
      "ó": "o",
      "ô": "o",
      "õ": "o",
      "ú": "u",
      "ü": "u",
      "ç": "c",
      " ": "-",
  }
  texto = texto.lower().strip()
  for k, v in substituicoes.items():
    texto = texto.replace(k, v)
  return texto


def coletar_sp():
  try:
    response = requests.get(URL_CETESB, timeout=30)
    dados = response.json()
    praias = []

    for item in dados.get("features", []):
      attr = item.get("attributes", {})
      municipio = str(attr.get("MUNICIPIO", "")).strip()
      praia = str(attr.get("PRAIA", "")).strip()
      local = str(attr.get("LOCAL_COLETA", "")).strip()
      status = str(attr.get("CLASSIFICACAO", "")).strip()

      if municipio and praia:
        praias.append({
            "estado": "SP",
            "cidade_slug": limpar_slug(municipio),
            "cidade": municipio,
            "praia": praia,
            "ponto": local,
            "status": status,
        })
    return praias
  except Exception as e:
    print(f"Erro ao coletar SP: {e}")
    return []


if __name__ == "__main__":
  resultado = {
      "atualizado_em": datetime.now().strftime("%d/%m/%Y às %H:%M"),
      "fonte": "CETESB / Órgãos Estaduais",
      "dados": coletar_sp(),
  }

  with open("balneabilidade.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)
