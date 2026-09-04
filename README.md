# Cormorant

Sistema de contagem de fluxo de pessoas para operações de varejo. O Cormorant captura vídeo, detecta e acompanha pessoas, registra cruzamentos de uma linha virtual e apresenta os indicadores em um dashboard.

```text
Câmeras -> YOLO + ByteTrack -> FastAPI + SQLite -> Dashboard Next.js
```

## Componentes

- `backend/`: API FastAPI, captura de vídeo, detecção, contagem e persistência SQLite.
- `frontend/`: dashboard operacional em Next.js, React e Recharts.
- `scripts/calibrate.py`: ferramenta para definir a linha de contagem de cada câmera.
- `scripts/setup.sh`: instala as dependências e prepara o modelo YOLO.
- `scripts/start.sh`: inicia backend e frontend juntos.

## Requisitos

- macOS com acesso às câmeras, pois a captura usa AVFoundation;
- Python 3.11 ou superior;
- [uv](https://docs.astral.sh/uv/) ou Python `venv` com `pip`;
- Node.js 20 ou superior e [pnpm](https://pnpm.io/) 10 ou superior;
- conexão com a internet na primeira instalação para obter dependências e o modelo YOLO.

## Instalação

Na raiz do repositório:

```bash
./scripts/setup.sh
```

O script instala as dependências do backend e do frontend. Quando `uv` está disponível, ele gerencia o ambiente Python; caso contrário, é criado `backend/.venv`.

## Configuração das câmeras

Calibre a linha virtual antes de iniciar a contagem:

```bash
uv run --directory backend python ../scripts/calibrate.py
```

Se o setup foi feito com `venv`, use `backend/.venv/bin/python scripts/calibrate.py`.

Clique nos dois pontos da linha, pressione `Enter` para confirmar, `R` para recomeçar ou `Q` para ignorar a câmera. Copie as coordenadas exibidas para `backend/src/config.py`.

As câmeras padrão são o dispositivo `0` (integrada) e o dispositivo `1` (iPhone via Continuity). Ajuste também o rótulo, o índice e os pontos da linha nessa configuração.

## Executar

```bash
./scripts/start.sh
```

| Serviço | URL |
| --- | --- |
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

Use `Ctrl+C` para encerrar os dois serviços.

Para executar manualmente:

```bash
cd backend
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Em outro terminal
cd frontend
pnpm dev
```

Sem `uv`, ative `backend/.venv` antes de iniciar o Uvicorn.

## Configuração por ambiente

O backend lê variáveis com o prefixo `CORMORANT_`:

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `CORMORANT_DB_PATH` | `footfall.db` | Caminho do banco SQLite. |
| `CORMORANT_YOLO_MODEL` | `yolov8s.pt` | Modelo usado na detecção. |
| `CORMORANT_CONFIDENCE_THRESHOLD` | `0.4` | Confiança mínima da detecção. |
| `CORMORANT_PROCESS_EVERY_N_FRAMES` | `3` | Intervalo de processamento dos frames. |
| `CORMORANT_CORS_ORIGINS` | `http://localhost:3000` e frontend público do Codespaces | Origens permitidas pelo backend, separadas por vírgula. |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL da API usada pelo frontend. |

No GitHub Codespaces, o frontend usa `https://congenial-fiesta-jqpq7gpqj7v35v99-8000.app.github.dev` e o backend permite a origem `https://congenial-fiesta-jqpq7gpqj7v35v99-3000.app.github.dev` por padrão. Para outro Codespace, ajuste `frontend/.env.local` e `CORMORANT_CORS_ORIGINS`.

## API

Os endpoints REST ficam sob `/api`:

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| `GET` | `/api/stats?period=today` | Totais de entrada, saída e saldo (`hour`, `today`, `week` ou `month`). |
| `GET` | `/api/stats/hourly` | Tendência horária do dia. |
| `GET` | `/api/stats/daily` | Tendência diária da semana. |
| `GET` | `/api/events?limit=50` | Eventos de cruzamento recentes. |
| `GET` | `/api/cameras` | Estado das câmeras configuradas. |
| `WS` | `/api/ws/live` | Atualizações de cruzamentos em tempo real. |

## Testes

```bash
cd backend
uv run pytest
python -m compileall src

cd ../frontend
pnpm test
pnpm lint
pnpm build
```

Os testes do backend usam mocks para câmeras, inferência e WebSocket; não exigem hardware conectado.

Para detalhes da API, consulte [backend/README.md](backend/README.md). O dashboard mantém instruções específicas em [frontend/README.md](frontend/README.md).