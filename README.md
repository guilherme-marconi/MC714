# MC714 - Playlist Colaborativa P2P

Trabalho de Sistemas Distribuídos (MC714 - Unicamp).

A ideia: 3 usuários (3 contêineres) controlam a MESMA fila de música ao mesmo tempo,
sem servidor central. Cada contêiner é um nó P2P que fala com os outros por HTTP.

Pra funcionar a gente implementou 3 algoritmos:
- **Relógio de Lamport** (`backend/lamport.py`) -> dá um timestamp lógico pra cada ação.
- **Exclusão mútua** (`backend/exclusao_mutua.py`) -> Ricart-Agrawala. Garante que só um nó mexe na fila por vez (add/remove).
- **Eleição de líder** (`backend/eleicao.py`) -> algoritmo Bully. Escolhe o "host". Só o líder confirma o play/pause; os outros nós encaminham o pedido pra ele.

## Stack
- Backend: FastAPI + uvicorn (porta 8000 dentro do contêiner)
- Frontend: Streamlit (porta 8501 dentro do contêiner)
- Tudo sobe com Docker Compose

## O que você precisa ter instalado
- Docker
- Docker Compose (já vem no Docker Desktop)

## Como rodar (jeito fácil, com Docker)

1. Na pasta do projeto, sobe os 3 nós:

```bash
docker compose up --build
```

2. Espera aparecer os logs dos 3 contêineres (node1, node2, node3).

3. Abre no navegador, uma aba pra cada nó:
   - node1 -> http://localhost:8501
   - node2 -> http://localhost:8502
   - node3 -> http://localhost:8503

4. Pra parar: `Ctrl+C` e depois

```bash
docker compose down
```

## Como testar se os algoritmos funcionam

- **Fila compartilhada:** adiciona uma música no node1, dá F5 nas abas do node2 e node3.
  A música aparece nas 3 (isso é a replicação + exclusão mútua funcionando).
- **Eleição de líder:** olha o campo "Líder" no topo. Os 3 nós mostram o mesmo líder.
  Agora derruba o líder (ex: se o líder é o node3, roda `docker stop node3`).
  Em uns segundos os outros dois elegem um líder novo sozinhos.
- **Play/Pause:** clica em Tocar num nó qualquer. Se ele não for o líder, o pedido é
  encaminhado pro líder, que confirma e manda pros outros. O estado fica igual nas 3 abas.
- **Lamport:** o número "Relógio de Lamport" no topo aumenta a cada ação. Serve pra ordenar
  os eventos de forma consistente entre os nós.

## Estrutura
```
backend/
  main.py #rotas FastAPI (ações do usuário + mensagens entre nós)
  lamport.py # relógio de Lamport
  exclusao_mutua.py # Ricart-Agrawala
  eleicao.py # Bully
  playlist.py # estado da fila (em memória) + músicas iniciais
frontend/
  app.py # interface Streamlit (fala só com o backend do próprio nó)
docker-compose.yml # sobe node1, node2, node3
Dockerfile
requirements.txt
start.sh # sobe backend + frontend dentro do contêiner
```