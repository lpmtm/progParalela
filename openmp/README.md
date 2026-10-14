# Frente 2 — OpenMP: simulacao de N corpos

Responsavel: Joao Miguel Luiz da Costa.

## Implementacao

Arquivo `06_nbody_openmp.cpp`, derivado de `sequencial/06_nbody.cpp` do repositorio.
A simulacao calcula interacoes gravitacionais de todos os pares de corpos (O(N²) por passo).
O `parallel for` externo distribui corpos `i` entre threads. Cada thread acumula forcas
locais para seu corpo e grava apenas `fx[i]`/`fy[i]`, evitando condicoes de corrida.
O segundo `parallel for` atualiza velocidades e posicoes. A barreira implicita ao final
de cada loop impede atualizacoes enquanto ainda ha calculos de forcas pendentes.
O `schedule(static)` oferece distribuicao previsivel de trabalho.

## Compilacao

Na raiz do repositorio:

```bash
mkdir -p bin
g++ -O2 -fopenmp -o bin/06_nbody_openmp openmp/06_nbody_openmp.cpp
g++ -O2 -o bin/06_nbody sequencial/06_nbody.cpp
```

## Execucao

```bash
./bin/06_nbody 2000 10
OMP_NUM_THREADS=1 ./bin/06_nbody_openmp 2000 10
OMP_NUM_THREADS=2 ./bin/06_nbody_openmp 2000 10
OMP_NUM_THREADS=4 ./bin/06_nbody_openmp 2000 10
OMP_NUM_THREADS=8 ./bin/06_nbody_openmp 2000 10
```

## Experimentos

Use N=1000, 2000, 4000 e 8000, sempre 10 passos. Para cada configuracao,
execute 6 vezes, descarte a primeira como aquecimento e registre a mediana das
5 restantes. Compare com a versao sequencial usando as mesmas entradas.

- Speedup: S(p) = T_seq / T_p
- Eficiencia: E(p) = S(p) / p

O checksum exibido com 6 casas decimais e uma verificacao rapida, nao uma
validacao numerica completa do estado. Para validar rigorosamente, adapte a
saida de estado final (x,y,vx,vy) conforme o procedimento em `validacao/`
do projeto, comparando com as referencias oficiais.

## Observacoes

A medicao cobre os passos de simulacao, assim como o baseline sequencial.
O overhead de criacao/sincronizacao das regioes paralelas pode tornar casos
pequenos mais lentos; por isso, avalie diversos tamanhos e numeros de threads.
