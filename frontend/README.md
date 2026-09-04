# Cormorant

Contador de fluxo de pessoas para operações de varejo. O Cormorant recebe vídeo das câmeras, detecta e acompanha pessoas, registra cruzamentos de uma linha virtual e exibe os indicadores em tempo real.

```text
Câmeras → YOLO + ByteTrack → FastAPI + SQLite → Dashboard Next.js
```

| Camada | Tecnologia | Responsabilidade |
| --- | --- | --- |
| Visão computacional | YOLO, Supervision e OpenCV | Detecta pessoas e identifica entradas e saídas. |
| API | FastAPI | Expõe indicadores, tendências, câmeras e atualizações ao vivo. |
| Dados | SQLite (WAL) | Persiste eventos de cruzamento e o estado das câmeras. |
| Dashboard | Next.js, React e Recharts | Mostra KPIs, gráficos e disponibilidade das câmeras. |

## Executar localmente

### Pré-requisitos

- macOS com acesso à câmera (o capturador usa AVFoundation);
- Python 3.11+;
- [uv](https://docs.astral.sh/uv/) **ou** `venv` + `pip`;
- Node.js 20+ e [pnpm](https://pnpm.io/) 10+.

### 1. Instalar dependências

Na raiz do repositório:

```bash
./scripts/setup.sh
```

O script instala as dependências do backend e do dashboard. Na primeira execução, ele também baixa o modelo `yolov8s.pt`; isso requer conexão com a internet e pode levar alguns minutos.

### 2. Calibrar as linhas de contagem

Antes de iniciar a operação, defina a linha virtual que separa entrada de saída para cada câmera:

```bash
uv run --directory backend python ../scripts/calibrate.py
```

Se o setup foi feito com `venv`, use `backend/.venv/bin/python scripts/calibrate.py` a partir da raiz.

| Atalho | Ação |
| --- | --- |
| Clique | Define um dos dois pontos da linha. |
| `Enter` | Confirma a linha após escolher dois pontos. |
| `R` | Limpa os pontos e recomeça. |
| `Q` | Ignora a câmera atual. |

Copie as coordenadas exibidas para a configuração de câmeras em `backend/src/config.py`. Por padrão, o projeto considera a câmera integrada do Mac (`0`) e a câmera do iPhone via Continuity (`1`).

### 3. Iniciar o sistema

```bash
./scripts/start.sh
```

| Serviço | Endereço |
| --- | --- |
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Documentação da API | http://localhost:8000/docs |

Use `Ctrl+C` no terminal para encerrar os dois serviços.

## Execução manual

Útil para depurar cada parte separadamente:

```bash
# Terminal 1 — API
cd backend
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — dashboard
cd frontend
pnpm dev
```

Sem `uv`, ative o ambiente virtual criado no backend e execute `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`.

## Configuração

As configurações do backend usam o prefixo `CORMORANT_` e podem ser definidas no ambiente.

| Variável | Padrão | Uso |
| --- | --- | --- |
| `CORMORANT_DB_PATH` | `footfall.db` | Caminho do banco SQLite. |
| `CORMORANT_YOLO_MODEL` | `yolov8s.pt` | Modelo YOLO usado na detecção. |
| `CORMORANT_CONFIDENCE_THRESHOLD` | `0.4` | Confiança mínima para considerar uma detecção. |
| `CORMORANT_PROCESS_EVERY_N_FRAMES` | `3` | Processa um a cada N frames para equilibrar precisão e desempenho. |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL da API consumida pelo dashboard. |

Exemplo:

```bash
export CORMORANT_CONFIDENCE_THRESHOLD=0.5
export CORMORANT_PROCESS_EVERY_N_FRAMES=2
./scripts/start.sh
```

## API

Todos os endpoints REST ficam sob `/api`.

| Endpoint | Descrição |
| --- | --- |
| `GET /api/stats?period=today` | Totais de entrada, saída e saldo para `hour`, `today`, `week` ou `month`. |
| `GET /api/stats/hourly` | Tendência horária do dia. |
| `GET /api/stats/daily` | Tendência diária da semana. |
| `GET /api/events` | Eventos de cruzamento recentes. |
| `GET /api/cameras` | Estado das câmeras configuradas. |
| `WS /api/ws/live` | Atualizações de cruzamentos em tempo real. |

## Testes

```bash
# Backend
cd backend
uv run pytest

# Frontend
cd frontend
pnpm test
pnpm lint
pnpm build
```

Os testes do backend usam câmera, modelo e WebSocket simulados; não exigem uma câmera conectada nem baixam modelos.

## Estrutura

```text
backend/                 API, captura, detecção e persistência
frontend/                Dashboard operacional em Next.js
scripts/setup.sh         Instala dependências e baixa o modelo
scripts/start.sh         Inicia backend e dashboard juntos
scripts/calibrate.py     Ferramenta visual para definir linhas de contagem
```
