from flask import Flask, request, jsonify
from coleta_service import ler_pontos_por_tipo_lixo

app = Flask(__name__)


@app.route('/api/coleta-pontos', methods=['GET'])
def coleta_pontos():
    """
    Endpoint REST GET para gerenciar pontos de coleta.
    
    Query Parameters:
        tipos: Lista de tipos de lixo separados por vírgula (opcional)
               Exemplo: ?tipos=eletroeletronicos,pilhas
        page: Número da página (padrão: 1)
              Cada página contém 10 resultados
        limit: Número máximo de resultados (padrão: todos, ignorado se page for fornecido)
    
    Returns:
        JSON com pontos de coleta (filtrados ou todos)
        
    Status Codes:
        200: Sucesso
        500: Erro interno do servidor
    """
    try:
        import csv
        
        PAGE_SIZE = 10
        
        # Se tipos foi fornecido, filtrar por tipo
        tipos_param = request.args.get('tipos')
        if tipos_param:
            tipos_lixo = [t.strip() for t in tipos_param.split(',')]
            pontos_dict = ler_pontos_por_tipo_lixo(tipos_lixo)
            pontos = list(pontos_dict.values()) if pontos_dict else []
            
            # Aplicar paginação se solicitado
            page = request.args.get('page', default=1, type=int)
            total = len(pontos)
            start = (page - 1) * PAGE_SIZE
            end = start + PAGE_SIZE
            pontos_paginated = pontos[start:end]
            
            response = {
                'total': total,
                'page': page,
                'page_size': PAGE_SIZE,
                'total_pages': (total + PAGE_SIZE - 1) // PAGE_SIZE,
                'tipos_filtrados': tipos_lixo,
                'pontos': pontos_paginated
            }
        else:
            # Caso contrário, listar todos os pontos
            pontos = []
            
            with open('pontos-de-coleta.csv', newline='', encoding='utf-8') as arquivo:
                leitor = csv.DictReader(arquivo, skipinitialspace=True)
                for row in leitor:
                    if row['tipo_lixo']:
                        pontos.append({
                            'id': row['id'],
                            'nome': row['nome'],
                            'tipo_lixo': row['tipo_lixo'],
                            'latitude': float(row['latitude']),
                            'longitude': float(row['longitude']),
                            'endereco': row['endereco']
                        })
            
            # Aplicar paginação se solicitado
            page = request.args.get('page', default=1, type=int)
            total = len(pontos)
            start = (page - 1) * PAGE_SIZE
            end = start + PAGE_SIZE
            pontos_paginated = pontos[start:end]
            
            response = {
                'total': total,
                'page': page,
                'page_size': PAGE_SIZE,
                'total_pages': (total + PAGE_SIZE - 1) // PAGE_SIZE,
                'pontos': pontos_paginated
            }
        
        return jsonify(response), 200
        
    except FileNotFoundError:
        return jsonify({'error': 'Arquivo CSV não encontrado'}), 500
    except Exception as e:
        return jsonify({'error': f'Erro ao processar requisição: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
