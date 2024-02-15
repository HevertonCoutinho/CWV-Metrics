import requests
import statistics
from tqdm import tqdm
from datetime import date
import csv
import math
from openpyxl import Workbook

# URLs das páginas que serão analisadas
urls = []

# Solicita a URL específica ao usuário
url_especifica = input("Digite uma URL de referência (ou deixe em branco para pular): ")

# Lê os URLs do arquivo CSV
with open("urls.csv", "r") as csv_file:
    csv_reader = csv.reader(csv_file)
    for row in csv_reader:
        url = row[0]
        urls.append(url)
        print(url)

# Chave de API do Page Speed Insights
api_key = input("Informe sua API: ")

# Parâmetros da API
params = {
    "strategy": "mobile",
    "key": api_key,
    "category": "performance",
    "locale": "pt_BR",
}

# Listas para armazenar as métricas de LCP e CLS de todas as URLs
lcp_values = []
cls_values = []

# Dicionário para armazenar os resultados de cada URL
results = {}

# Cria a barra de progresso
with tqdm(total=len(urls), desc="Analisando páginas") as pbar:
    # Loop para realizar as chamadas à API para cada URL
    for url in urls:
        params["url"] = url
        response = requests.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed", params=params)
        result = response.json()["lighthouseResult"]["audits"]
        lcp = result["largest-contentful-paint"]["displayValue"]
        cls = result["cumulative-layout-shift"]["displayValue"]
        results[url] = {"LCP": lcp, "CLS": cls}
        lcp_value = float(lcp.split()[0].replace(",", "."))  # converte para float
        cls_value = float(cls.split()[0].replace(",", "."))  # converte para float
        lcp_values.append(lcp_value)
        cls_values.append(cls_value)
        
        pbar.update(1)  # atualiza a barra de progresso

# Imprime os resultados
print("Resultados:\n")
for url, metrics in results.items():
    print(f"{url}: LCP = {metrics['LCP']}, CLS = {metrics['CLS']}")

# Verifica se as métricas de LCP e CLS da URL específica foram obtidas
if url_especifica not in results:
    print("Não foram obtidas métricas para a URL específica.")
else:
    # Calcula o desvio padrão das métricas de LCP e CLS de todas as URLs
    lcp_stddev = statistics.stdev(lcp_values)
    cls_stddev = statistics.stdev(cls_values)
    print(f"\nDesvio padrão Geral: LCP = {lcp_stddev}, CLS = {cls_stddev}")
    
    # Filtra os valores de LCP e CLS da URL específica, se fornecida
    if url_especifica:
        # Calcula a média das métricas de LCP e CLS de todas as URLs
        lcp_media = statistics.mean(lcp_values)
        cls_media = statistics.mean(cls_values)
        
        # Calcula a distância média dos tempos de carregamento da página (LCP)
        lcp_distance = math.sqrt(sum((lcp - lcp_media) ** 2 for lcp in lcp_values) / len(lcp_values))
        
        # Calcula a distância média dos shifts de layout cumulativos (CLS)
        cls_distance = math.sqrt(sum((cls - cls_media) ** 2 for cls in cls_values) / len(cls_values))

        # Calcula a distância média da página específica em relação à média de LCP
        url_especifica_lcp = float(results[url_especifica]["LCP"].split()[0].replace(",", "."))
        lcp_distance_from_mean = abs(url_especifica_lcp - lcp_media)

        # Imprime a distância média da página específica em relação à média de LCP
        print(f"Distância média da página {url_especifica} em relação à média de LCP: {lcp_distance_from_mean}")
        
        # Calcula a distância média da página específica em relação à média de LCP
        url_especifica_cls = float(results[url_especifica]["CLS"].split()[0].replace(",", "."))
        cls_distance_from_mean = abs(url_especifica_cls - cls_media)

        # Imprime a distância média da página específica em relação à média de LCP
        print(f"Distância média da página {url_especifica} em relação à média de CLS: {cls_distance_from_mean}")
    else:
        lcp_distance_from_mean = None
        cls_distance_from_mean = None
    
# Determina o vencedor com base nas métricas de LCP e CLS
winner = None
best_lcp = float("inf")
best_cls = float("inf")
for url, metrics in results.items():
    lcp_value = float(metrics["LCP"].split()[0].replace(",", "."))  # converte para float
    cls_value = float(metrics["CLS"].split()[0].replace(",", "."))  # converte para float
    if lcp_value < best_lcp:
        winner = url
        best_lcp = lcp_value
        best_cls = cls_value
    elif lcp_value == best_lcp and cls_value < best_cls:
        winner = url
        best_cls = cls_value

print(f"\nMelhor Resultado: {winner} (LCP = {best_lcp}, CLS = {best_cls})")

# Exporta os resultados para um arquivo Excel
wb = Workbook()
ws = wb.active
ws.title = "Resultados"

ws.append(["URL", "LCP", "CLS"])
for url, metrics in results.items():
    ws.append([url, metrics["LCP"], metrics["CLS"]])

ws.append([])  # Linha em branco

ws.append(["Melhor Resultado"])
ws.append([winner])

ws.append([])  # Linha em branco

ws.append(["Desvio Padrão Geral"])
ws.append(["LCP", lcp_stddev])
ws.append(["CLS", cls_stddev])

ws.append([])  # Linha em branco

if lcp_distance_from_mean is not None:
    ws.append(["Distância Média da Página de referência"])
    ws.append(["LCP", lcp_distance_from_mean])
    ws.append(["CLS", cls_distance_from_mean])

ws.append([])  # Linha em branco

ws.append(["Data da Exportação"])
ws.append([date.today()])

file_name = f"resultados_{date.today()}.xlsx"
wb.save(file_name)
print(f"\nOs resultados foram exportados para o arquivo: {file_name}")
input("Pressione 'Enter' para fechar o programa.")
