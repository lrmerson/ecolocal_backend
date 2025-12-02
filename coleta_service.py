import csv
import requests
import os
import json
import socket

# Forçar uso de IPv4 apenas para resolver problemas de lentidão no Windows
original_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4_only

# Tentar obter a chave de variável de ambiente, senão usar placeholder
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY")

# Avisar se a chave não foi configurada
if GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY":
    print("\n⚠️  AVISO: Chave de API do Google não configurada!")
    print("   Configure a variável de ambiente GOOGLE_API_KEY com sua chave real.")
    print("   Sem a chave, a função de proximidade não funcionará.\n")


def get_distances_from_google(origin_lat, origin_lon, destinations):
    """
    Chama a Google Routes API v2 (Distance Matrix endpoint) para obter distância e tempo de direção.
    
    Args:
        origin_lat: Latitude do usuário
        origin_lon: Longitude do usuário
        destinations: Lista de tuplas (lat, lon)
    
    Retorna:
        Lista de dicionários com distance_km e duration_min
    """
    if not destinations:
        return []
    
    # Verificar se a chave de API foi configurada
    if GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY":
        print("❌ Erro: Chave de API do Google não configurada!")
        return [{"distance_km": None, "duration_min": None}] * len(destinations)
    
    url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "originIndex,destinationIndex,distanceMeters,duration"
    }

    results = []
    
    # Processar cada destino individualmente
    for dest_lat, dest_lon in destinations:

        payload = {
            "origins": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": {
                                "latitude": origin_lat,
                                "longitude": origin_lon
                            }
                        }
                    }
                }
            ],
            "destinations": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": {
                                "latitude": dest_lat,
                                "longitude": dest_lon
                            }
                        }
                    }
                }
            ],
            "travelMode": "DRIVE"
        }
        
        print(f"Debug - Payload enviado:")
        print(f"  Origin: lat={origin_lat}, lon={origin_lon}")
        print(f"  Destination: lat={dest_lat}, lon={dest_lon}")
        print(f"  Payload completo: {json.dumps(payload, indent=2)}")

        try:
            resposta = requests.post(
                url, 
                headers=headers, 
                data=json.dumps(payload), 
                timeout=10,
                proxies={'http': None, 'https': None}  # Desabilita detecção automática de proxy
            ).json()
            print(f"Debug - Resposta API para destino ({dest_lat}, {dest_lon}): {resposta}")
            
            # A resposta é uma lista de elementos no formato:
            # [{'originIndex': 0, 'destinationIndex': 0, 'distanceMeters': 21443, 'duration': '1708s'}]
            if resposta and isinstance(resposta, list) and len(resposta) > 0:
                elemento = resposta[0]
                
                # Distância em metros
                dist_m = elemento.get("distanceMeters", 0)
                
                # Duração em segundos (formato "1234s")
                dur_s = elemento.get("duration", "0s")
                # Converter string de duração (ex: "1708s") para segundos
                dur_seconds = float(dur_s.rstrip('s')) if isinstance(dur_s, str) else dur_s
                
                results.append({
                    "distance_km": dist_m / 1000,
                    "duration_min": dur_seconds / 60
                })
                print(f"✅ Sucesso: {dist_m/1000:.2f} km, {dur_seconds/60:.1f} min")
            else:
                # Se não houver resultado válido, retornar None
                print(f"⚠️  Aviso: resposta vazia ou inválida da API para destino ({dest_lat}, {dest_lon})")
                results.append({
                    "distance_km": None,
                    "duration_min": None
                })
        
        except Exception as e:
            print(f"❌ Erro ao chamar API Google Routes: {str(e)}")
            results.append({
                "distance_km": None,
                "duration_min": None
            })
    
    return results




def enriquecer_pontos_com_distancias(pontos, user_lat, user_lon):
    """
    Adiciona distance_km e duration_min a cada ponto usando Google Routes API v2.
    
    Args:
        pontos: Dicionário de pontos {id: {latitude, longitude, ...}}
        user_lat: Latitude do usuário
        user_lon: Longitude do usuário
    
    Retorna:
        Dicionário pontos atualizado com distance_km e duration_min adicionados
    """
    if not pontos or not user_lat or not user_lon:
        return pontos
    
    # Extrair destinos como lista de tuplas (lat, lon)
    destinations = [(ponto['latitude'], ponto['longitude']) for ponto in pontos.values()]
    
    # Obter distâncias da API Google Routes v2
    print(f"Chamando Google Routes API v2 para {len(destinations)} pontos...")
    results = get_distances_from_google(user_lat, user_lon, destinations)
    
    # Adicionar distância e duração a cada ponto
    ponto_list = list(pontos.items())
    for (id_ponto, ponto), result in zip(ponto_list, results):
        ponto['distance_km'] = result['distance_km']
        ponto['duration_min'] = result['duration_min']
    
    return pontos


def ler_pontos_por_tipo_lixo(tipos_lixo, user_lat=None, user_lon=None, n=None, csv_file="pontos-de-coleta.csv"):
    """
    Filtra pontos de coleta pelos tipos de lixo especificados.
    Opcionalmente, calcula distância e tempo de direção do usuário e retorna os N mais próximos.
    
    Args:
        tipos_lixo: Lista de tipos de lixo para filtrar
        user_lat: Latitude do usuário (opcional, para calcular proximidade)
        user_lon: Longitude do usuário (opcional, para calcular proximidade)
        n: Número de pontos mais próximos a retornar (opcional)
        csv_file: Caminho do arquivo CSV
        
    Retorna:
        Dicionário com pontos de coleta filtrados, chaveado por ID
        Se user_lat/user_lon fornecidos: inclui distance_km e duration_min
    """
    if not tipos_lixo:
        return {}
    
    # Limpar e normalizar os tipos de lixo da entrada
    tipos_lixo_normalizados = [t.strip().lower() for t in tipos_lixo]
    
    pontos = {}
    try:
        with open(csv_file, newline='', encoding='utf-8') as arquivo:
            leitor = csv.DictReader(arquivo, skipinitialspace=True)
            for row in leitor:
                if row['tipo_lixo']:
                    # Dividir os tipos pelo separador \,
                    tipos_do_ponto = [t.strip().lower() for t in row['tipo_lixo'].split(r"\,")]
                    
                    # Verificar se todos os tipos solicitados estão presentes no ponto
                    if all(t in tipos_do_ponto for t in tipos_lixo_normalizados):
                        pontos[row['id']] = {
                            'id': row['id'],
                            'nome': row['nome'],
                            'tipo_lixo': row['tipo_lixo'],
                            'latitude': float(row['latitude']),
                            'longitude': float(row['longitude']),
                            'endereco': row['endereco']
                        }
        # Se user_lat e user_lon forem fornecidos, enriquecer com distâncias do Google API
        if user_lat and user_lon:
            pontos = enriquecer_pontos_com_distancias(pontos, user_lat, user_lon)
        
        # Ordenar pelos N mais próximos se solicitado
        if user_lat and user_lon and n:
            pontos = pontos_mais_proximos(pontos, n)
                        
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_file}")
    except Exception as e:
        raise Exception(f"Erro ao ler arquivo CSV: {str(e)}")
    
    return pontos

def pontos_mais_proximos(pontos, n):
    """
    Ordena pontos pelo tempo de direção (quando disponível) e retorna os N mais próximos.
    
    Args:
        pontos: Dicionário de pontos com duração calculada
        n: Número de pontos a retornar
        
    Retorna:
        Dicionário com até N pontos ordenados por proximidade
    """
    if not pontos or n <= 0:
        return {}
    
    def ordem_dist(tupla):
        # Se duration_min for None, colocar no final (infinito)
        duration = tupla[1]
        return duration if duration is not None else float('inf')
    
    def pontos_ordenados(pontos, n):
        pontos_ordem = []
        for id in pontos:
            dist_ponto = (id, pontos[id].get('duration_min', float('inf')))
            pontos_ordem.append(dist_ponto)
        pontos_ordem.sort(key=ordem_dist)
        if len(pontos_ordem) < n:
            return pontos_ordem
        return pontos_ordem[:n]
                        
    def refinar_pontos(pontos, pontos_ordenados):
        pontos_refinados = {}
        for tupla in pontos_ordenados:
            id_ponto = tupla[0]
            pontos_refinados[id_ponto] = pontos[id_ponto]
        return pontos_refinados
    return refinar_pontos(pontos, pontos_ordenados(pontos, n))


def ler_todos_pontos(csv_file="pontos-de-coleta.csv"):
    """
    Lê todos os pontos do CSV sem filtros.
    
    Args:
        csv_file: Caminho do arquivo CSV
        
    Retorna:
        Dicionário com todos os pontos, chaveado por ID
    """
    pontos = {}
    try:
        with open(csv_file, newline='', encoding='utf-8') as arquivo:
            leitor = csv.DictReader(arquivo, skipinitialspace=True)
            for row in leitor:
                if row['tipo_lixo']:
                    pontos[row['id']] = {
                        'id': row['id'],
                        'nome': row['nome'],
                        'tipo_lixo': row['tipo_lixo'],
                        'latitude': float(row['latitude']),
                        'longitude': float(row['longitude']),
                        'endereco': row['endereco']
                    }
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_file}")
    except Exception as e:
        raise Exception(f"Erro ao ler arquivo CSV: {str(e)}")
    
    return pontos