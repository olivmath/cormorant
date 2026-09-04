# Cormorant Backend

Backend do Cormorant, responsável por capturar vídeo, detectar pessoas, identificar cruzamentos da linha virtual, persistir eventos e disponibilizar os dados ao dashboard.

## Stack

- Python 3.11+
- FastAPI e Uvicorn
- Ultralytics YOLO, Supervision e OpenCV
- SQLite com modo WAL
- Pydantic Settings
- pytest, pytest-asyncio e HTTPX para testes

## Estrutura

| Arquivo | Responsabilidade |
| --- | --- |
| `src/main.py` | Cria a aplicação e inicia ou encerra os workers das câmeras. |
| `src/routes.py` | Define endpoints REST e WebSocket. |
| `src/capture.py` | Gerencia captura, reconexão e processamento dos frames. |
| `src/counter.py` | Executa detecção, tracking e contagem da linha. |
| `src/database.py` | Inicializa o SQLite e consulta ou grava eventos. |
| `src/config.py` | Define configurações e câmeras. |
| `src/schemas.py` | Modelos de resposta da API. |
| `src/ws_manager.py` | Gerencia clientes conectados ao WebSocket. |
| `tests/` | Testes unitários dos componentes do backend. |

## Instalação

Na raiz do repositório, a instalação completa é feita por:

```bash
./scripts/setup.sh
```

Para configurar apenas o backend com `uv`:

```bash
cd backend
uv sync
uv run python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
```

Alternativamente:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
```

O carregamento do modelo pode baixar arquivos na primeira execução. O projeto usa `CAP_AVFOUNDATION`, portanto a captura em produção pressupõe macOS e câmeras acessíveis pelo sistema.

## Executar a API

```bash
cd backend
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Com `venv`, ative o ambiente e execute `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`.

A documentação interativa fica em http://localhost:8000/docs.

Na inicialização, a aplicação cria o banco definido por `CORMORANT_DB_PATH` e inicia um worker para cada câmera configurada. Um worker marca a câmera como offline e tenta reconectar após cinco segundos quando a captura falha.

## Configuração

As configurações usam o prefixo `CORMORANT_`:

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `CORMORANT_DB_PATH` | `footfall.db` | Arquivo do banco SQLite. |
| `CORMORANT_YOLO_MODEL` | `yolov8s.pt` | Caminho ou nome do modelo YOLO. |
| `CORMORANT_CONFIDENCE_THRESHOLD` | `0.4` | Confiança mínima para uma pessoa ser considerada. |
| `CORMORANT_PROCESS_EVERY_N_FRAMES` | `3` | Processa um a cada N frames. |
| `CORMORANT_CORS_ORIGINS` | `http://localhost:3000` e frontend público do Codespaces | Origens permitidas, separadas por vírgula. |
| `CORMORANT_LIVEKIT_URL` | vazio | URL `wss://` do projeto LiveKit. |
| `CORMORANT_LIVEKIT_API_KEY` | vazio | Chave da API LiveKit. |
| `CORMORANT_LIVEKIT_API_SECRET` | vazio | Segredo da API LiveKit. |

As variáveis podem ser definidas no ambiente ou em `backend/.env`. Ao executar a API a partir de `backend/`, esse arquivo é carregado automaticamente. Não versione o arquivo `.env`.

As câmeras são configuradas em `src/config.py` por meio de `CameraConfig`:

```python
CameraConfig(
    camera_id=0,
    index=0,
    label="Mac Built-in",
    line_start=(320, 400),
    line_end=(960, 400),
)
```

`line_start` e `line_end` definem a linha virtual. Use `uv run --directory backend python ../scripts/calibrate.py` para obter coordenadas adequadas ao enquadramento. Com `venv`, use `backend/.venv/bin/python scripts/calibrate.py` a partir da raiz.

## API

Todos os endpoints ficam sob `/api`.

| Método | Endpoint | Resposta |
| --- | --- | --- |
| `GET` | `/api/stats?period=today` | Contagens `count_in`, `count_out`, `net`, `from_time` e `to_time`. Períodos: `hour`, `today`, `week`, `month`. |
| `GET` | `/api/stats/hourly` | Buckets horários com `count_in` e `count_out`. |
| `GET` | `/api/stats/daily` | Buckets diários com `count_in` e `count_out`. |
| `GET` | `/api/events?limit=50` | Eventos recentes; `limit` aceita de 1 a 500. |
| `GET` | `/api/cameras` | Status, rótulo e último sinal de cada câmera. |
| `WS` | `/api/ws/live` | Atualizações de cruzamento em tempo real. |

Uma mensagem do WebSocket tem o formato:

```json
{
  "type": "crossing",
  "direction": "IN",
  "camera_id": 0,
  "timestamp": "2026-09-04T12:00:00+00:00",
  "today_in": 12,
  "today_out": 7
}
```

## Banco de dados

O SQLite é criado automaticamente com as tabelas `crossing_events` e `camera_status`. As conexões usam WAL para permitir leitura enquanto eventos são gravados. O arquivo padrão `footfall.db` fica no diretório em que a API é iniciada e pode ser alterado com `CORMORANT_DB_PATH`.

## Testes e validação

```bash
cd backend
uv run pytest -v
uv run python -m compileall src
```

Os testes substituem câmera, inferência, banco e conexões WebSocket quando necessário. Não é preciso conectar uma câmera nem executar o dashboard para rodá-los.