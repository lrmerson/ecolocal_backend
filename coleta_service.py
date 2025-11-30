import csv


def ler_pontos_por_tipo_lixo(tipos_lixo, user_lat=None, user_lon=None, n=None, csv_file="pontos-de-coleta.csv"):
    """
    Filtra pontos de coleta pelos tipos de lixo especificados.
    
    Args:
        tipos_lixo: Lista de tipos de lixo para filtrar
        csv_file: Caminho do arquivo CSV
        
    Returns:
        Dicionário com pontos de coleta filtrados, chaveado por ID
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
                        ########################TODO CHAMAR API GOOGLE DISTANCE MATRIX AQUI ########################
                        pontos[row['id']] = {
                            'id': row['id'],
                            #TODO 'distancia': RESULTADO DA API AQUI,
                            #TODO 'duracao': RESULTADO DA API AQUI,
                            'nome': row['nome'],
                            'tipo_lixo': row['tipo_lixo'],
                            'latitude': float(row['latitude']),
                            'longitude': float(row['longitude']),
                            'endereco': row['endereco']
                        }
        # Se user_lat e user_lon forem fornecidos, ordenar pelos mais próximos
        if user_lat and user_lon and n:
            pontos = pontos_mais_proximos(pontos, n)
                        
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_file}")
    except Exception as e:
        raise Exception(f"Erro ao ler arquivo CSV: {str(e)}")
    
    return pontos

def pontos_mais_proximos(pontos, n):
    """
    Ordena pontos pela distância (quando disponível) e retorna os N mais próximos.
    
    Args:
        pontos: Dicionário de pontos com distância calculada
        n: Número de pontos a retornar
        
    Retorna:
        Dicionário com até N pontos ordenados por proximidade
    """
    if not pontos or n <= 0:
        return {}
    
    def ordem_dist(tupla):
        return tupla[1]
    
    def pontos_ordenados(pontos, n):
        pontos_ordem = []
        for id in pontos:
            dist_ponto = (id, pontos[id].get('duracao', float('inf')))
            pontos_ordem.append(dist_ponto)
        pontos_ordem.sort(key= ordem_dist)
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