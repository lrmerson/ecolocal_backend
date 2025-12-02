# API REST de Pontos de Coleta

API REST para gerenciar e filtrar pontos de coleta de lixo eletrônico no Distrito Federal.

## Instalação

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Executar a aplicação

```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`

## Arquitetura e Fluxo da Aplicação

![Diagrama de Fluxo](docs/fluxo-aplicacao.png)

O diagrama acima ilustra o fluxo completo da aplicação:

1. **Usuário** acessa a página inicial e interage via navegador
2. **Frontend** (Flask/HTML) processa a solicitação via HTTP
3. **Backend** (Python) filtra pontos do CSV e cria dicionário
4. **Google Routes API v2** calcula distâncias e durações de rotas
5. **Resposta** enriquecida com informações de distância/duração
6. **Mapa interativo** exibido ao usuário com pontos mais próximos

## Endpoint

### Gerenciar Pontos de Coleta

**Método:** `GET`  
**URI:** `/api/coleta-pontos`

**Descrição:**  
Retorna pontos de coleta com opções de filtro por tipo e paginação.

**Parâmetros de Query (Todos Opcionais):**
- `tipos`: Lista de tipos de lixo separados por vírgula (retorna pontos com TODOS os tipos)
  - Exemplo: `?tipos=eletroeletronicos,pilhas`
- `page`: Número da página (padrão: 1)
  - Cada página contém 10 resultados
  - Exemplo: `?page=2`
- `lat`: Latitude do usuário (para calcular pontos próximos por tempo de direção)
- `lon`: Longitude do usuário (para calcular pontos próximos por tempo de direção)
- `n`: Número de pontos mais próximos a retornar (padrão: 5, usado com lat/lon)

**Exemplos de Requisição:**
```bash
# Listar todos os pontos (página 1)
curl "http://localhost:5000/api/coleta-pontos"

# Filtrar por tipo(s) (página 1)
curl "http://localhost:5000/api/coleta-pontos?tipos=eletroeletronicos,pilhas"

# Ir para página 2
curl "http://localhost:5000/api/coleta-pontos?page=2"

# Filtrar e ir para página 3
curl "http://localhost:5000/api/coleta-pontos?tipos=pilhas&page=3"

# Encontrar 3 pontos mais próximos (via Google Routes API v2)
curl "http://localhost:5000/api/coleta-pontos?tipos=pilhas&lat=-23.5505&lon=-46.6333&n=3"

# Encontrar 5 pontos mais próximos de qualquer tipo
curl "http://localhost:5000/api/coleta-pontos?lat=-23.5505&lon=-46.6333&n=5"
```

**Respostas (200 OK):**

Sem filtro:
```json
{
  "total": 119,
  "page": 1,
  "page_size": 10,
  "total_pages": 12,
  "pontos": [
    {
      "id": "001",
      "nome": "Zero Impacto Logística Reversa",
      "tipo_lixo": "eletroeletronicos\\,eletrodomesticos\\,pilhas",
      "latitude": -15.762421707078582,
      "longitude": -47.935475219000324,
      "endereco": "Saa Q 2 SETOR DE ABASTECIMENTO..."
    },
    ...
  ]
}
```

Com filtro por tipo:
```json
{
  "total": 2,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "tipos_filtrados": ["eletroeletronicos", "pilhas"],
  "pontos": [
    {
      "id": "001",
      "nome": "Zero Impacto Logística Reversa",
      "tipo_lixo": "eletroeletronicos\\,eletrodomesticos\\,pilhas",
      "latitude": -15.762421707078582,
      "longitude": -47.935475219000324,
      "endereco": "Saa Q 2 SETOR DE ABASTECIMENTO..."
    },
    {
      "id": "003",
      "nome": "Carrefour Hipermercado",
      "tipo_lixo": "eletroeletronicos\\,eletrodomesticos\\,pilhas",
      "latitude": -15.733847664170918,
      "longitude": -47.899207515917645,
      "endereco": "Boulevard Shopping ST Setor..."
    }
  ]
}
```

Com filtro por proximidade (Google Routes API v2):
```json
{
  "total": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "tipos_filtrados": ["pilhas"],
  "pontos": [
    {
      "id": "001",
      "nome": "Zero Impacto Logística Reversa",
      "tipo_lixo": "eletroeletronicos\\,eletrodomesticos\\,pilhas",
      "latitude": -15.762421707078582,
      "longitude": -47.935475219000324,
      "endereco": "Saa Q 2 SETOR DE ABASTECIMENTO...",
      "distance_km": 12.5,
      "duration_min": 18.3
    },
    {
      "id": "003",
      "nome": "Carrefour Hipermercado",
      "tipo_lixo": "eletroeletronicos\\,eletrodomesticos\\,pilhas",
      "latitude": -15.733847664170918,
      "longitude": -47.899207515917645,
      "endereco": "Boulevard Shopping ST Setor...",
      "distance_km": 8.2,
      "duration_min": 12.1
    },
    {
      "id": "005",
      "nome": "Outro Ponto de Coleta",
      "tipo_lixo": "pilhas\\,lampadas",
      "latitude": -15.791111,
      "longitude": -47.888888,
      "endereco": "Endereço...",
      "distance_km": 15.7,
      "duration_min": 22.5
    }
  ]
}
```

## Testes Unitários

Executar os testes unitários da lógica de negócio:

```bash
python -m unittest test_coleta_service.py -v
```

### Cobertura de Testes

Os testes unitários cobrem:
- ✓ Filtrar por um único tipo de lixo
- ✓ Filtrar por múltiplos tipos (AND logic)
- ✓ Filtrar por tipo inexistente
- ✓ Filtrar com lista vazia
- ✓ Estrutura de dados retornados
- ✓ Case-insensitive filtering
- ✓ Tratamento de espaços em branco
- ✓ Tratamento de arquivo não encontrado

## Tipos de Lixo Suportados

- `eletroeletronicos`: Eletrônicos em geral
- `eletrodomesticos`: Eletrodomésticos
- `pilhas`: Pilhas e baterias
- `lampadas`: Lâmpadas fluorescentes e LED

## Exemplos de Uso

### Python Requests

```python
import requests

# Listar todos os pontos (página 1)
response = requests.get('http://localhost:5000/api/coleta-pontos')
pontos = response.json()
print(f"Total: {pontos['total']} pontos")
print(f"Página {pontos['page']} de {pontos['total_pages']}")

# Filtrar por um tipo
response = requests.get(
    'http://localhost:5000/api/coleta-pontos',
    params={'tipos': 'pilhas'}
)
pontos = response.json()
print(f"Encontrados {pontos['total']} pontos com pilhas")

# Ir para página 2
response = requests.get(
    'http://localhost:5000/api/coleta-pontos',
    params={'page': 2}
)
pontos = response.json()
print(f"Mostrando página {pontos['page']} de {pontos['total_pages']}")

# Filtrar e paginar
response = requests.get(
    'http://localhost:5000/api/coleta-pontos',
    params={'tipos': 'eletroeletronicos,pilhas', 'page': 2}
)
pontos = response.json()
print(f"Encontrados {pontos['total']} pontos com ambos os tipos")

# Encontrar 3 pontos mais próximos (requer Google API key)
response = requests.get(
    'http://localhost:5000/api/coleta-pontos',
    params={
        'tipos': 'pilhas',
        'lat': -23.5505,
        'lon': -46.6333,
        'n': 3
    }
)
pontos = response.json()
for ponto in pontos['pontos']:
    print(f"{ponto['nome']}: {ponto['duration_min']:.1f} min de direção")
```

### JavaScript (Fetch)

```javascript
// Listar todos
fetch('http://localhost:5000/api/coleta-pontos')
  .then(res => res.json())
  .then(data => console.log(`Página ${data.page} de ${data.total_pages}`));

// Filtrar por tipo
const tipos = 'eletroeletronicos,pilhas';
fetch(`http://localhost:5000/api/coleta-pontos?tipos=${tipos}`)
  .then(res => res.json())
  .then(data => console.log(`${data.total} pontos encontrados`));

// Navegar para página 2
fetch('http://localhost:5000/api/coleta-pontos?page=2')
  .then(res => res.json())
  .then(data => console.log(`Mostrando ${data.pontos.length} pontos (página ${data.page} de ${data.total_pages})`))

// Encontrar pontos próximos (requer Google API key)
fetch('http://localhost:5000/api/coleta-pontos?tipos=pilhas&lat=-23.5505&lon=-46.6333&n=5')
  .then(res => res.json())
  .then(data => {
    data.pontos.forEach(ponto => {
      console.log(`${ponto.nome}: ${ponto.duration_min.toFixed(1)} min`);
    });
  });
```

## Integração com Google Routes API v2

### Configuração Necessária

1. Obtenha uma chave de API do Google:
   - Acesse [Google Cloud Console](https://console.cloud.google.com/)
   - Crie um novo projeto
   - Ative a API "Routes API"
   - Crie uma chave de API

2. Configure a chave como variável de ambiente:
   ```bash
   export GOOGLE_API_KEY="sua_chave_api_aqui"
   ```

3. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Como Funciona

- Quando `lat` e `lon` são fornecidos, a API chama Google Routes API v2 (computeRouteMatrix) para calcular:
  - `distance_km`: Distância em quilômetros via dirigindo
  - `duration_min`: Tempo de direção em minutos
- O parâmetro `n` retorna apenas os N pontos com menor `duration_min` (tempo de direção)
- Usa endpoint de Distance Matrix da Routes API v2 com configuração IPv4-only para melhor performance

## Notas

- Os valores de latitude/longitude são retornados como números (float)
- Os tipos de lixo no CSV usam `\,` como separador (vírgula escapada)
- O filtro é case-insensitive
- O filtro usa lógica AND: retorna apenas pontos que têm TODOS os tipos especificados
- Proximidade é calculada por tempo de direção (não distância em linha reta)
- Requer API key válida do Google para funcionalidade de proximidade
