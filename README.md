# Simulação de N Corpos — Programação Paralela

Projeto acadêmico do IESB. A partir do código sequencial fornecido pelo professor
(`sequencial/06_nbody.cpp`), o projeto mede o baseline, faz o perfilamento, estima o
ganho pela Lei de Amdahl e produz versões paralelas em OpenMP (memória compartilhada)
e MPI (memória distribuída), validadas contra o baseline.

## Divisão de frentes

| Frente | Responsável | Pasta |    
|---|---|---| 
| 1 — Baseline e perfilamento | Caroline Lopes Martins | `sequencial/`, `scripts/`, `resultados/` |   
| 2 — OpenMP | João Miguel Luiz da Costa | `openmp/` |   
| 3 — MPI | Ian Melo Gonçalves | `mpi/` |   

Os responsáveis estão em `AUTORES.md`. Todos devem entender o projeto inteiro: a
apresentação faz arguição cruzada.

## Requisitos

- Windows com Docker Desktop, WSL2 ativo e VS Code com a extensão **Dev Containers**.
- Ambiente do professor (`ambiente_pp_CCO085.zip`, do Classroom), já com g++, OpenMP,
  OpenMPI e make.

## Como abrir o ambiente

1. Abra o Docker Desktop e espere ele iniciar por completo.
2. Abra a pasta do projeto no VS Code (`codigos/trabalho`, dentro do ambiente do professor).
3. Pressione **F1** e escolha **Dev Containers: Reopen in Container**.
4. Confirme o selo verde no canto inferior esquerdo e abra **View > Terminal**.
5. Teste o ambiente:

```bash
   g++ --version && make --version && mpirun --version
```

## Como reproduzir do zero

Todos os comandos são executados na raiz do projeto, dentro do contêiner:

```bash
make seq        # compila o sequencial de referência
make valid      # compila o validador de estado final
make refs       # gera as referências validacao/ref_N.txt (N = 1000, 2000, 4000, 8000)
make check      # confirma que as referências são reproduzíveis (deve dar IDENTICO)
make baseline   # mede o baseline: resultados/baseline.csv
make perfil     # mede forças x atualização: resultados/perfil.txt
```

Use `make help` para ver a lista de alvos e `make clean` para remover os binários.

### Versão MPI (frente 3)

Dentro do contêiner:

```bash
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1   # o usuário do contêiner é root
make check-mpi     # valida com -np 1, 2, 3, 4 (deve dar IDENTICO em todas)
make medicao-mpi   # mede seq + MPI, forte e fraca: resultados/mpi.csv (~2 min)
```

Os gráficos usam matplotlib, que não vem no contêiner. Gere-os fora dele:

```bash
python3 -m venv .venv && .venv/bin/pip install matplotlib   # só na primeira vez
.venv/bin/python scripts/graficos_mpi.py
```

Isso imprime um resumo (speedup, eficiência, % de comunicação) e gera
`resultados/mpi_resumo.csv` e os gráficos em `resultados/graficos/`.

Para rodar na mão: `mpirun -np 4 ./bin/06_nbody_mpi 8000 10`. Além de `checksum` e
`tempo`, a saída mostra `comm`, o tempo gasto no `MPI_Allgatherv` (comunicação + espera).

Observações:

- O aviso *"failed to bind memory"* é inofensivo: o Docker bloqueia a fixação de memória
  por padrão. Para eliminá-lo, suba o contêiner com `--cap-add SYS_NICE`. Exemplo, no
  Linux, sem o VS Code:
  `docker run -it --rm --cap-add SYS_NICE -v "$PWD":/w -w /w iesb/pp-lab:2026.2 bash`
- Não rode duas medições ao mesmo tempo, porque elas disputam os mesmos núcleos.
  Use `-np` até o número de núcleos físicos (4).

## Estrutura

```bash
progParalela/
├── sequencial/
│ ├── 06_nbody.cpp código original
│ └── 06_nbody_prof.cpp cópia com cronômetros em volta de cada laço
├── validacao/
│ ├── 06_nbody_valid.cpp cópia que grava o estado final com 17 dígitos
│ ├── compara.sh compara duas saídas (bit a bit e erro relativo)
│ └── ref_1000.txt ... ref_8000.txt
├── scripts/
│ ├── medicao.sh protocolo de medição do baseline
│ ├── medicao_mpi.sh mesmo protocolo para seq + MPI (forte e fraca)
│ └── graficos_mpi.py resumo e gráficos da versão MPI
├── resultados/
│ ├── baseline.csv
│ ├── perfil.txt
│ ├── mpi.csv medições brutas da versão MPI
│ ├── mpi_resumo.csv medianas, speedup, eficiência, % comunicação
│ └── graficos/ gráficos de tempo, speedup, eficiência, overhead e fraca
├── openmp/ frente 2
├── mpi/
│ └── 06_nbody_mpi.cpp versão MPI (blocos de i + MPI_Allgatherv)
├── Makefile
├── README.md
└── AUTORES.md
```


## Protocolo de medição

- Compilação: `g++ -O2`, sem alteração na lógica de cálculo.
- Tamanhos: N = 1000, 2000, 4000 e 8000, com 10 passos.
- Repetições: 6 execuções por tamanho. A primeira é aquecimento e é descartada.
  Reportamos a mediana das 5 restantes.
- Medição: `clock_gettime(CLOCK_MONOTONIC)`, que cobre só a simulação (sem compilação).
- Máquina: Intel Core i5-1035G1 (4 núcleos / 8 threads), 8 GB de RAM, Windows com WSL2.
  Medições feitas com outros programas fechados e notebook na tomada.

## Validação de corretude

O checksum impresso pelo programa original (6 casas decimais) não detecta diferenças
no resultado, porque as posições mudam pouco por passo. Por isso, a validação compara
o estado final completo (x, y, vx, vy de cada corpo) com 17 dígitos significativos.

Uma versão paralela é válida quando `make check` der `IDENTICO` para todos os N.
Diferenças com erro relativo da ordem de 1e-15 devem ser investigadas (ordem de
operações ou contração FMA). Erros maiores indicam falha na paralelização.

## Observações

- O sequencial define o resultado correto. As versões paralelas não podem alterar a
  lógica de cálculo.
- A cópia `06_nbody_valid.cpp` foi enviada ao professor para aprovação. [registrar a resposta aqui]
- Os binários ficam em `bin/` e não entram no Git.
