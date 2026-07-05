# Relatório — Playlist Colaborativa P2P

**MC714 — Sistemas Distribuídos**
Instituto de Computação — UNICAMP
Prof. Luiz Fernando Bittencourt — 2º Trabalho

| | |
|---|---|
| **Integrante** | Guilherme Marconi Mugnai — RA 241277 |
| **Integrante** | Jonatas Santos Da Silva — RA 225334 |
| **Vídeo**        | https://youtu.be/I36wsJ20EJs |

---

## Sumário

1. [Introdução](#1-introdução)
2. [Como executar localmente](#2-como-executar-localmente)
3. [Detalhes técnicos](#3-detalhes-técnicos)

---

## 1. Introdução

### 1.1 O problema escolhido

O trabalho pede a implementação de três algoritmos clássicos de sistemas distribuídos: relógio lógico de **Lamport**, um algoritmo de **exclusão mútua** e um algoritmo de **eleição de líder**.
Escolhemos um problema único que exige os três ao mesmo tempo: uma **playlist colaborativa peer-to-peer (P2P)**.
A ideia é: **três usuários, cada um em um nó (contêiner) diferente, controlam a mesma fila de músicas simultaneamente, sem servidor central**. Qualquer usuário pode adicionar música, remover música e dar play/pause. Não há um "dono" fixo da fila.
Os nós conversam entre si por troca de mensagens (HTTP) e precisam se coordenar para que o estado permaneça coerente nas três telas.

### 1.2 Por que a playlist demonstra os três algoritmos

Cada requisito do enunciado mapeia naturalmente para uma necessidade concreta da
playlist:

| Algoritmo | Necessidade na playlist |
|---|---|
| **Relógio de Lamport** | Ordenar eventos (adições, remoções, play/pause) que acontecem em nós diferentes, sem relógio físico global. |
| **Exclusão mútua (Ricart–Agrawala)** | Impedir que dois usuários modifiquem a fila ao mesmo tempo e a deixem inconsistente (ex.: os dois removendo a mesma música, ou inserindo na mesma posição). Só um nó por vez entra na "seção crítica" que altera a fila. |
| **Eleição de líder (Bully)** | Escolher **um** nó responsável por confirmar o estado do player (play/pause). Isso evita que o "tocando agora" divirja entre os nós. Se o líder cair, os outros elegem um novo automaticamente. |

Em outras palavras:

- **Lamport** responde *"em que ordem as coisas aconteceram?"*
- **Exclusão mútua** responde *"quem pode mexer na fila agora?"*
- **Eleição** responde *"quem é a autoridade que confirma o play/pause?"*

Os três operam sobre o **mesmo estado replicado** (a fila de músicas), então o problema não é forçado: remover a coordenação de qualquer um deles quebra a aplicação de um jeito observável.

### 1.3 Visão geral da stack

- **Backend:** Python 3.11 + **FastAPI** (servidor HTTP/REST) executado com **uvicorn**, na porta `8000` dentro de cada contêiner.
- **Comunicação entre nós:** **troca de mensagens via HTTP** (biblioteca `requests`).
  Cada mensagem de algoritmo (pedido de exclusão mútua, OK, mensagem de eleição, anúncio de coordenador, replicação de estado) é uma requisição `POST` para um endpoint do outro nó. 
- **Frontend:** **Streamlit** (porta `8501`), um painel web que mostra o estado dos três nós lado a lado e uma *timeline* de eventos em tempo real.
- **Orquestração:** **Docker + Docker Compose**. Cada nó é um contêiner; o Compose sobe os três (`node1`, `node2`, `node3`) em uma rede bridge dedicada.

### 1.4 Comentários adicionais

Alguns pontos de projeto que valem destacar já na introdução:

- **Arquitetura simétrica (P2P):** todos os nós rodam exatamente o mesmo código e a mesma imagem Docker. O que os diferencia é apenas a variável de ambiente `NODE_ID` e a lista de vizinhos `PEERS`. Não há papéis fixos no código — o "líder" é decidido em tempo de execução pela eleição.
- **Observabilidade:** para o algoritmo ser demonstrável (e não uma caixa-preta), cada passo relevante gera um evento (`backend/eventos.py`) que aparece rotulado na timeline da interface (`REQUEST`, `DEFER`, `ENTER`, `RELEASE`, `START`, `LEADER`, etc.), sempre com o timestamp de Lamport associado.
- **Ferramentas de demonstração:** implementamos um "kill" simulado e um modo "câmera-lenta" (delay artificial por operação). O câmera-lenta é o que permite *enxergar* a exclusão mútua acontecendo: sem ele, a seção crítica é curta demais para observar um `DEFER`.
- **Frontend feito com IA generativa:** como a interface **não é o foco da disciplina**, optamos por gerá-la com auxílio de IA generativa e concentrar o esforço no backend distribuído. Detalhes na [Seção 3.6](#36-frontend-frontendapppy).

---

## 2. Como executar localmente

Esta seção é um roteiro para que o avaliador reproduza o trabalho do zero na própria máquina.

### 2.1 Pré-requisitos

- **Docker** (Docker Desktop no macOS/Windows já inclui tudo).
- **Docker Compose** (vem junto com o Docker Desktop; no Linux, `docker compose` v2).

Não é necessário instalar Python nem nenhuma dependência na máquina host: tudo é construído dentro da imagem Docker.

### 2.2 Subir o sistema (caminho recomendado, com Docker)

Na raiz do projeto:

```bash
docker compose up --build
```

O Compose vai:

1. Construir a imagem a partir do `Dockerfile` (uma vez).
2. Subir três contêineres: `node1`, `node2` e `node3`.
3. Dentro de cada contêiner, o script `start.sh` inicia **o backend (uvicorn)** e **o frontend (Streamlit)** em paralelo.

Aguarde aparecerem os logs de inicialização dos três nós.

### 2.3 Portas e URLs

Cada contêiner expõe seu frontend Streamlit em uma porta diferente do host:

| Nó | Frontend (navegador) | Backend (interno na rede Docker) |
|---|---|---|
| node1 | http://localhost:8501 | `http://node1:8000` |
| node2 | http://localhost:8502 | `http://node2:8000` |
| node3 | http://localhost:8503 | `http://node3:8000` |

Abra uma aba do navegador para cada porta (8501, 8502 e 8503). Cada aba é um painel completo que já mostra os três nós; abrir as três só reforça que o estado converge em qualquer ponto de entrada.

### 2.4 Roteiro de demonstração (validar cada algoritmo)

1. **Fila compartilhada + replicação:** na barra lateral, escolha um nó de destino, preencha *Title* e *Artist* e clique **Add**. A música aparece nas três colunas — é a replicação funcionando por baixo da exclusão mútua.

2. **Exclusão mútua (conflito):** abra o expander **"⚔️ Teste de conflito"**. Escolha dois nós diferentes, um valor de câmera-lenta (ex.: 2 s) e clique **"Disparar conflito"**. A interface envia dois pedidos **no mesmo instante**. Na timeline você verá `REQUEST` dos dois, um `ENTER` (quem ganhou a prioridade) e um `DEFER` (quem esperou), seguido de `RELEASE` e do segundo `ENTER`. Isso mostra o Ricart–Agrawala serializando o acesso.

3. **Eleição de líder:** observe o selo **★ LEADER** no topo das colunas — os três nós concordam no mesmo líder (por padrão, o `node3`, de maior id). Agora derrube o líder:

   ```bash
   docker stop node3
   ```
   Em poucos segundos os nós restantes detectam a ausência (via *health check*) e elegem um novo líder sozinhos (`START` → `LEADER`/`COORDINATOR` na timeline).
   Para trazê-lo de volta: `docker start node3`.

   > Alternativamente, sem parar o contêiner, use os botões **Kill / Revive** da barra lateral — eles simulam a falha marcando o nó como "morto" (retorna 503 nas rotas internas), útil para gravar a demonstração sem derrubar o processo.

4. **Play/Pause via líder:** clique **Play** em um nó qualquer. Se ele não for o líder, o pedido é **encaminhado ao líder**, que confirma e replica para todos. O "tocando agora" fica igual nas três colunas.

5. **Relógio de Lamport:** acompanhe o campo `clock` de cada nó e os marcadores `[L…]` na timeline: o valor cresce a cada ação e é atualizado quando um nó recebe mensagem de outro, dando uma ordem consistente aos eventos.

### 2.5 Encerrar

```
Ctrl+C        # interrompe os logs
docker compose down   # remove os contêineres e a rede
```

---

## 3. Detalhes técnicos

### 3.1 Arquitetura geral

Cada nó é um contêiner idêntico contendo **dois processos**:

```
                    Rede Docker (bridge "playlist_net")
  ┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
  │        node1          │  │        node2          │  │        node3          │
  │ ┌───────────────────┐ │  │ ┌───────────────────┐ │  │ ┌───────────────────┐ │
  │ │ Frontend Streamlit│ │  │ │ Frontend Streamlit│ │  │ │ Frontend Streamlit│ │
  │ │      :8501        │ │  │ │      :8501        │ │  │ │      :8501        │ │
  │ └─────────┬─────────┘ │  │ └─────────┬─────────┘ │  │ └─────────┬─────────┘ │
  │           │ HTTP      │  │           │           │  │           │           │
  │ ┌─────────▼─────────┐ │  │ ┌─────────▼─────────┐ │  │ ┌─────────▼─────────┐ │
  │ │ Backend FastAPI   │◄─┼──┼─│ Backend FastAPI  │◄┼──┼─│ Backend FastAPI   │ │
  │ │      :8000        │─┼──┼─►      :8000        │─┼──┼─►      :8000        │ │
  │ │  Lamport / Mutex  │ │  │ │  Lamport / Mutex  │ │  │ │  Lamport / Mutex  │ │
  │ │  Eleição / Fila   │ │  │ │  Eleição / Fila   │ │  │ │  Eleição / Fila   │ │
  │ └───────────────────┘ │  │ └───────────────────┘ │  │ └───────────────────┘ │
  └──────────┬────────────┘  └───────────────────────┘  └───────────────────────┘
   host :8501│         host :8502                host :8503
             ▼ (navegador do avaliador)
```

- O **frontend** só faz chamadas HTTP de leitura/ação para os **backends** (o seu e os dos vizinhos, via `NODES_JSON`). Ele é um observador/controle: não participa dos algoritmos.
- Os **backends** são os nós de verdade do sistema distribuído. É entre eles que
  ocorrem as trocas de mensagens dos três algoritmos.

### 3.2 Como os algoritmos se conectam

Os três algoritmos não vivem isolados — eles se encadeiam em cada ação do usuário. O **relógio de Lamport é a base**: tanto a exclusão mútua quanto a replicação usam seus timestamps. Fluxos principais:

**Adicionar/Remover música (usa Lamport + Exclusão Mútua):**

```
usuário → /actions/add no nó X
  1. X pede EXCLUSÃO MÚTUA (Ricart–Agrawala): envia /mutex/request a todos os vizinhos
     └─ o pedido carrega um timestamp de LAMPORT (clock.tick())
  2. X espera os OKs de todos → entra na seção crítica
  3. X aplica a mudança na sua fila local e a REPLICA (/replicate) para os vizinhos
  4. X libera a exclusão mútua (envia OK a quem ficou adiado)
```

**Play/Pause (usa Lamport + Eleição):**

```
usuário → /actions/play no nó X
  - se X é o LÍDER:  aplica play, gera timestamp de Lamport, replica a todos
  - se X não é líder: ENCAMINHA /actions/play para o líder eleito, que confirma e replica
```

**Eleição (roda em segundo plano, independente das ações do usuário):**

```
- Ao subir, cada nó dispara uma eleição (Bully).
- Uma thread monitora o líder a cada 3 s (health check).
- Se o líder some, um novo é eleito automaticamente.
```

### 3.3 Modelo de comunicação (endpoints HTTP)

Toda a coordenação é feita por estes endpoints do backend (FastAPI). Os de "ação" são
disparados pelo usuário via frontend; os "internos" são a troca de mensagens
**nó-a-nó**:

| Método | Rota | Tipo | Função |
|---|---|---|---|
| POST | `/actions/add` | ação | Adiciona música (entra na exclusão mútua) |
| POST | `/actions/remove` | ação | Remove música (entra na exclusão mútua) |
| POST | `/actions/play` | ação | Play (confirmado/encaminhado ao líder) |
| POST | `/actions/pause` | ação | Pause (confirmado/encaminhado ao líder) |
| POST | `/replicate` | interno | Aplica uma alteração vinda de outro nó |
| POST | `/mutex/request` | interno | Pedido de acesso à seção crítica |
| POST | `/mutex/ok` | interno | Concessão de acesso |
| POST | `/election` | interno | Mensagem de eleição (Bully) |
| POST | `/coordinator` | interno | Anúncio de novo líder |
| GET  | `/health` | interno | *Health check* usado pelo monitor de líder |
| GET  | `/state` | leitura | Estado atual do nó (fila, líder, clock…) |
| GET  | `/events` | leitura | Log de eventos para a timeline |
| POST | `/admin/kill` · `/admin/revive` · `/admin/config` | demo | Falha simulada e câmera-lenta |

### 3.4 Papel do Docker

O Docker resolve a parte "sistema distribuído de verdade" sem precisar de várias
máquinas:

- Cada nó é um **contêiner isolado**, com seu próprio processo, memória e estado de fila. Não há memória compartilhada — a única forma de um nó influenciar o outro é **pela rede**, exatamente como exige o enunciado.
- O **Docker Compose** cria uma rede bridge (`playlist_net`) e um **DNS interno**: dentro dessa rede, `http://node2:8000` resolve para o contêiner `node2`. Por isso os nós se encontram pelo nome, sem IPs fixos.
- A topologia (quem são os vizinhos de cada nó) é injetada por variáveis de ambiente (`PEERS`, `NODES_JSON`), então o mesmo código serve para qualquer nó.

### 3.5 Backend

Todo o backend está em `backend/`. A seguir, uma subseção por arquivo.

#### 3.5.1 `lamport.py` — Relógio lógico de Lamport

Implementa a classe `LamportClock`, que mantém um inteiro `_time` protegido por um `threading.Lock` (o backend é multithread — várias requisições HTTP podem tocar o relógio ao mesmo tempo). Segue exatamente as três regras de Lamport:

- **`tick()`** — evento **local**. Incrementa o relógio em 1 e devolve o valor. É chamado sempre que o nó faz algo por conta própria (pedir a seção crítica, aplicar um play/pause como líder, etc.).
- **`update(received_time)`** — **recepção de mensagem**. Faz `_time = max(_time, received_time) + 1`, garantindo que o relógio local nunca fique atrás do remetente. É chamado ao receber um pedido de mutex ou uma replicação.
- **`now()`** — apenas lê o valor atual (para exibir no `/state`).

Cada operação também registra um evento (`eventos.log_lamport`), o que alimenta os marcadores `[L…]` na timeline.

#### 3.5.2 `exclusao_mutua.py` — Exclusão mútua (Ricart–Agrawala)

Implementa o algoritmo **Ricart–Agrawala**, baseado em mensagens e em timestamps de Lamport (não usa token nem coordenador central). A classe `ExclusaoMutua` guarda um estado que é um de três valores:

- `RELEASED` — não quer a seção crítica;
- `WANTED` — pediu e está esperando os OKs;
- `HELD` — está dentro da seção crítica.

**Prioridade entre pedidos concorrentes** (`has_priority`): vence o pedido de **menor timestamp**; havendo empate, vence o de **menor `node_id`** (desempate determinístico). Isso garante uma ordem total entre pedidos simultâneos.

Fluxo:

- **`request_access()`** — marca `WANTED`, gera o timestamp do pedido com `clock.tick()`, zera os OKs recebidos e envia `/mutex/request` (com timestamp e id) a **todos os vizinhos**. Em seguida **bloqueia** em um `threading.Event` até ter recebido OK de todos; então passa para `HELD` e entra na seção crítica.
- **`on_request(sender_id, timestamp)`** — ao receber um pedido: primeiro faz
  `clock.update(timestamp)`. Depois decide:
  - se está `HELD` → **adia** (guarda o remetente em `_deferred`);
  - se está `WANTED` e tem prioridade sobre o remetente → **adia**;
  - caso contrário → **concede** na hora (envia `/mutex/ok`).
- **`on_ok(sender_id)`** — registra o OK; quando o conjunto de OKs cobre todos os
  vizinhos, libera o `Event` e o nó entra na seção crítica.
- **`release_access()`** — volta a `RELEASED` e envia os OKs **adiados** para todos os nós que ficaram na fila `_deferred`.

No `main.py`, `request_access()`/`release_access()` envolvem as operações que alteram a fila (`add`/`remove`), garantindo que **apenas um nó por vez** modifique a playlist.

#### 3.5.3 `eleicao.py` — Eleição de líder (Bully)

Implementa o algoritmo **Bully** ("valentão"): o nó de **maior id** tende a se tornar líder. A classe `Election` guarda `leader` e uma flag `_in_election`.

- **`start_election()`** — envia `/election` para todos os vizinhos com **id maior** que o seu. Se **nenhum** responder (todos os maiores estão fora), o nó se declara líder (`become_leader`). Se algum responder, ele recua e aguarda o anúncio do coordenador.
- **`become_leader()`** — define a si mesmo como líder e envia `/coordinator` para todos os nós de **id menor**, anunciando a nova liderança.
- **`receive_election(sender_id)`** — ao receber um `/election` de um nó menor, responde (o simples `HTTP 200` já sinaliza "estou vivo, assumo daqui") e dispara a **própria** eleição.
- **`receive_coordinator(leader_id)`** — registra o novo líder anunciado.
- **`monitor_leader()`** — thread em laço infinito que, a cada **3 s**, faz *ping* (`GET /health`) no líder atual. Se o líder for `None` ou não responder, dispara uma nova eleição. É esse monitor que dá a **tolerância a falhas**: derrubar o líder faz o sistema se reorganizar sozinho.
- **`start()`** — sobe o monitor e uma eleição inicial em *threads daemon* assim que o backend inicia (`election.start()` no fim do `main.py`).

As mensagens de eleição usam timeout curto (2 s), então um nó ausente é percebido
rapidamente.

#### 3.5.4 `controle.py` — Estado do nó (falha simulada + câmera-lenta)

Módulo utilitário que guarda dois controles de demonstração num dicionário protegido por lock:

- **`alive`** — quando `False`, o nó é tratado como "morto": as rotas internas do
  `main.py` respondem `503` (via `_exige_vivo`). Alternado por `matar()`/`reviver()` (endpoints `/admin/kill` e `/admin/revive`). 
  Serve para simular a queda de um nó — em especial do líder — **sem** derrubar o contêiner.
- **`step_delay`** — atraso artificial (em segundos) aplicado por `esperar()` no meio das operações. É a **"câmera-lenta"**: aumenta o tempo dentro da seção crítica para que dê para observar, na timeline, um nó sendo adiado (`DEFER`) enquanto o outro segura o acesso. Configurado por `/admin/config`.

Esses controles são exclusivamente para tornar os algoritmos **visíveis** durante a apresentação; não fazem parte da lógica distribuída em si.

#### 3.5.5 `playlist.py` — Estado da fila

Define o `dataclass` **`Song`** (`id`, `title`, `artist`) e a classe **`Playlist`**, que mantém a lista de músicas, o `is_playing` e o `current_song_id`, tudo protegido por lock. Métodos: `add_song` (no fim ou numa posição), `remove_song` (por id) e `set_playing`.

Ponto conceitual importante: **cada nó tem a sua própria cópia** da fila em memória. A classe não sabe nada de rede — manter as três cópias coerentes é responsabilidade dos algoritmos distribuídos (exclusão mútua para não corromper + replicação para propagar). 
A função `_mock_songs()` popula uma fila inicial idêntica nos três nós, para começar a demonstração já com conteúdo.

#### 3.5.6 `eventos.py` — Log de eventos (observabilidade)

`EventLog` é um *buffer* em memória (limitado a `MAX_EVENTS = 500`) que registra cada passo dos algoritmos com: número de sequência, timestamp físico, timestamp de **Lamport**, `node_id`, *tipo* (`lamport`, `mutex`, `election`, `playlist`, `admin`) e um detalhe textual.
As funções auxiliares (`log_lamport`, `log_mutex`, `log_eleicao`, `log_playlist`, `log_admin`) são chamadas de dentro dos algoritmos. O endpoint `/events` expõe o log (com filtro `since`) e o frontend agrega os eventos dos três nós para montar a timeline única e colorida. É o que transforma o algoritmo em algo demonstrável.

#### 3.5.7 `main.py` — API e orquestração (FastAPI)

É o ponto de entrada do backend e o "cola" de tudo. Na inicialização, instancia os
objetos globais compartilhados pelas requisições: `clock` (Lamport), `playlist`, `mutex`
(exclusão mútua) e `election`, lendo `NODE_ID` e `PEERS` do ambiente.
Define os modelos
de requisição (Pydantic) e todas as rotas da [tabela da Seção 3.3](#33-modelo-de-comunicação-endpoints-http).
Destaques:

- **`/actions/add` e `/actions/remove`** — o corpo é envolvido por `mutex.request_access()` … `mutex.release_access()` (bloco `try/finally`). Dentro da seção crítica: `clock.tick()`, altera a fila local e chama `replicate_to_peers(...)` para propagar a mudança.
- **`_player_command(playing)`** (usado por `/actions/play` e `/actions/pause`) — implementa a regra do líder: se o nó **é** o líder, ele confirma (tick + `set_playing` + replicação); se **não é**, encaminha a ação para o líder via HTTP. Se não houver líder eleito, responde `503`.
- **`/replicate`** — recebe uma alteração de outro nó, faz `clock.update(...)` e aplica na fila local (add/remove/play/pause). É o mecanismo que mantém as três cópias convergentes.
- **`_exige_vivo()`** — *guard* chamado nas rotas para honrar o "kill" simulado.
- **`replicate_to_peers()`** — envia o `POST /replicate` para todos os vizinhos, ignorando os que estiverem fora (falha silenciosa com timeout).
- No fim do arquivo, **`election.start()`** dispara a eleição inicial e o monitor de
  líder.

### 3.6 Frontend (`frontend/app.py`)

> **Nota sobre autoria:** como a interface **não é o foco da disciplina** (o objetivo é a implementação dos algoritmos distribuídos), optamos por **construir o frontend com auxílio de IA generativa**. 
> Isso nos permitiu investir o tempo no backend distribuído e, ainda assim, entregar um painel que **evidencia** o funcionamento dos algoritmos.

O frontend é um painel **Streamlit** que atua como observador e controle remoto — ele não participa dos algoritmos, apenas conversa com os backends por HTTP. Principais responsabilidades:

- **Descoberta dos nós:** lê `NODES_JSON` (injetado pelo Compose) para saber a URL do backend de cada nó; sem essa variável, usa `DEFAULT_NODES` (localhost).
- **Leitura de estado:** `fetch_state()` (`GET /state`) e `fetch_events()` (`GET /events`) para cada nó.
- **Ações do usuário:** `post_action()` envia `POST` para `/actions/*`, `/admin/*`, etc. A barra lateral concentra os controles: adicionar/remover música, play/pause, kill/revive e o slider de câmera-lenta.
- **Painel ao vivo:** a função `live_panel()`, decorada com `@st.fragment(run_every=1)`, redesenha a cada segundo os **três cartões de nó** (um por coluna, com selo de líder, clock e fila) e a **timeline** unificada de eventos, ordenada por chegada e colorida por tipo.
- **Teste de conflito:** `disparar_em_paralelo()` usa um `threading.Barrier` para disparar dois pedidos `/actions/*` **exatamente no mesmo instante** (um por nó), forçando a disputa que a exclusão mútua precisa resolver. É a forma mais didática de provocar um `DEFER` visível.

---
