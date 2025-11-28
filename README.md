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
```

## Notas

- Os valores de latitude/longitude são retornados como números (float)
- Os tipos de lixo no CSV usam `\,` como separador (vírgula escapada)
- O filtro é case-insensitive
- O filtro usa lógica AND: retorna apenas pontos que têm TODOS os tipos especificados
