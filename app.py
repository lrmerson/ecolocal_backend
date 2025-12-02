from flask import Flask, request, jsonify, render_template, send_from_directory
from coleta_service import ler_pontos_por_tipo_lixo, ler_todos_pontos
import folium
from folium.plugins import LocateControl
import os

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')

@app.route('/')
def home():
    """Página inicial com informações sobre o projeto."""
    return render_template('index.html')


@app.route('/api/coleta-pontos', methods=['GET'])
def coleta_pontos():
    """
    Endpoint REST GET para gerenciar pontos de coleta.
    
    Query Parameters:
        tipos: Lista de tipos de lixo separados por vírgula (opcional)
               Exemplo: ?tipos=eletroeletronicos,pilhas
        page: Número da página (padrão: 1)
              Cada página contém 10 resultados
        lat: Latitude do usuário (opcional, para cálculo de proximidade)
        lon: Longitude do usuário (opcional, para cálculo de proximidade)
        n: Número de pontos mais próximos a retornar (padrão: 5)
    
    Retorna:
        JSON com pontos de coleta (filtrados ou todos)
        Se lat/lon fornecidos: inclui distance_km e duration_min
        
    Códigos de Status:
        200: Sucesso
        500: Erro interno do servidor
    """
    try:
        import csv
        
        PAGE_SIZE = 10
        
        # Se tipos foi fornecido, filtrar por tipo
        tipos_param = request.args.get('tipos')
        if tipos_param:
            user_lat = request.args.get('lat', type=float)
            user_lon = request.args.get('lon', type=float)
            n = request.args.get('n', default=5, type=int)
            tipos_lixo = [t.strip() for t in tipos_param.split(',')]
            pontos_dict = ler_pontos_por_tipo_lixo(tipos_lixo, user_lat, user_lon, n)
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


@app.route('/mapa')
def mapa():
    """
    Rota para exibir mapa interativo com filtros.
    
    Query Parameters:
        tipos: Tipos de lixo separados por vírgula (opcional)
        lat: Latitude do usuário (opcional)
        lon: Longitude do usuário (opcional)
    """
    try:
        # Coordenadas padrão (Brasília)
        centro_lat, centro_lon = -15.793889, -47.882778
        
        # Criar mapa
        mapa = folium.Map(
            location=[centro_lat, centro_lon],
            zoom_start=13,
            tiles='OpenStreetMap'
        )
        
        # Adicionar controle de localização
        LocateControl(
            strings={"title": "Mostrar minha localização", "popup": "Você está aqui"},
            locateOptions={"enableHighAccuracy": True, "maxZoom": 16}
        ).add_to(mapa)
        
        # HTML para filtro
        filter_html = '''
            <div style="position: fixed; top: 10px; left: 50px; z-index:9999; font-size:14px; 
                        background-color: white; padding: 10px; border-radius: 5px; border: 2px solid rgba(0,0,0,0.2);">
                <b>🔍 Filtrar por:</b><br>
                <a href="/mapa" style="text-decoration: none; color: black; display: block; margin-bottom: 5px;">✓ Todos</a>
                <a href="/mapa?tipos=eletroeletronicos" style="text-decoration: none; color: black; display: block; margin-bottom: 5px;">💻 Eletrônicos</a>
                <a href="/mapa?tipos=eletrodomesticos" style="text-decoration: none; color: black; display: block; margin-bottom: 5px;">🔌 Eletrodomésticos</a>
                <a href="/mapa?tipos=pilhas" style="text-decoration: none; color: black; display: block; margin-bottom: 5px;">🔋 Pilhas</a>
                <a href="/mapa?tipos=lampadas" style="text-decoration: none; color: black; display: block;">💡 Lâmpadas</a>
            </div>
        '''
        mapa.get_root().html.add_child(folium.Element(filter_html))
        
        # HTML para botão "Sobre"
        sobre_html = '''
            <div style="position: fixed; top: 10px; right: 60px; z-index:9999;">
                <a href="/sobre" style="background-color: white; padding: 8px 12px; border-radius: 5px; 
                   text-decoration: none; border: 2px solid rgba(0,0,0,0.2); color: black; 
                   font-weight: bold; display: block; text-align: center;">ℹ️ Sobre</a>
            </div>
        '''
        mapa.get_root().html.add_child(folium.Element(sobre_html))
        
        # Obter parâmetros
        tipos_param = request.args.get('tipos')
        user_lat = request.args.get('lat', type=float)
        user_lon = request.args.get('lon', type=float)
        n = request.args.get('n', default=5, type=int)
        
        # Obter pontos - reutilizando funções de coleta_service.py
        if tipos_param:
            tipos_lixo = [t.strip() for t in tipos_param.split(',')]
            # Se lat/lon não foram obtidos, não enviar para evitar erro
            if user_lat and user_lon:
                pontos_dict = ler_pontos_por_tipo_lixo(tipos_lixo, user_lat, user_lon, n)
            else:
                # Se sem localização, retornar todos os pontos do tipo sem ordenar por proximidade
                pontos_dict = ler_pontos_por_tipo_lixo(tipos_lixo)
        else:
            # Se não houver filtro, listar todos
            pontos_dict = ler_todos_pontos()
        
        pontos = list(pontos_dict.values()) if pontos_dict else []
        
        # Adicionar mensagem se nenhum ponto foi encontrado com os filtros
        if tipos_param and len(pontos) == 0:
            tipos_texto = ', '.join(tipos_lixo)
            aviso_html = f'''
                <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                            z-index: 9999; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                            color: white; padding: 30px 40px; border-radius: 12px; 
                            box-shadow: 0 10px 40px rgba(0,0,0,0.3); text-align: center;
                            font-family: Arial, sans-serif; max-width: 500px;">
                    <div style="font-size: 48px; margin-bottom: 15px;">⚠️</div>
                    <h2 style="margin: 0 0 15px 0; font-size: 22px; font-weight: bold;">
                        Nenhum ponto encontrado
                    </h2>
                    <p style="margin: 0 0 10px 0; font-size: 16px; line-height: 1.5;">
                        Não há pontos de coleta que aceitem <b>todos</b> os tipos selecionados simultaneamente:
                    </p>
                    <p style="margin: 0; font-size: 15px; background: rgba(255,255,255,0.2); 
                              padding: 10px; border-radius: 6px; font-weight: 600;">
                        {tipos_texto}
                    </p>
                    <p style="margin: 15px 0 0 0; font-size: 14px; opacity: 0.9;">
                        💡 Tente selecionar menos tipos ou busque por tipos individualmente.
                    </p>
                </div>
            '''
            mapa.get_root().html.add_child(folium.Element(aviso_html))
        
        # Adicionar marcadores ao mapa
        for ponto in pontos:
            lat = ponto['latitude']
            lon = ponto['longitude']
            nome = ponto['nome']
            endereco = ponto.get('endereco', 'N/A')
            tipo_lixo = ponto['tipo_lixo']
            
            # Construir popup com informações
            distance_info = ""
            if 'distance_km' in ponto and ponto['distance_km'] is not None and 'duration_min' in ponto and ponto['duration_min'] is not None:
                distance_info = f"<br><b>Distância:</b> {ponto['distance_km']:.1f} km<br><b>Tempo:</b> {ponto['duration_min']:.0f} min"
            
            google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            popup_html = f'''
                <div style="min-width: 200px; font-family: Arial, sans-serif;">
                    <b style="font-size: 14px;">{nome}</b><br>
                    <small>{endereco}</small><br>
                    <b>Tipos:</b> {tipo_lixo}<br>
                    {distance_info}
                    <br><a href="{google_maps_url}" target="_blank" style="color: blue; text-decoration: none;">
                    📍 Ver no Google Maps</a>
                </div>
            '''
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(mapa)
        
        # Se usuário forneceu localização, adicionar marcador azul
        if user_lat and user_lon:
            folium.Marker(
                location=[user_lat, user_lon],
                popup='📍 Sua localização',
                icon=folium.Icon(color='blue', icon='user', prefix='fa')
            ).add_to(mapa)
        
        return mapa.get_root().render()
        
    except FileNotFoundError as e:
        return f"<h1>Erro</h1><p>Arquivo não encontrado: {str(e)}</p>", 500
    except Exception as e:
        return f"<h1>Erro ao gerar mapa</h1><p>{str(e)}</p>", 500


@app.route('/sobre')
def sobre():
    """Página sobre o projeto."""
    return render_template('sobre.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
