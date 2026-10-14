#!/bin/bash
# Medição da versão MPI — mesmo protocolo do baseline:
# 1 aquecimento descartado + 5 repetições por configuração.
#
# Escalabilidade forte: N fixo, np = 1..4 (+ sequencial na mesma máquina,
#   que é a referência do speedup).
# Escalabilidade fraca: trabalho por processo constante. Como o custo é O(N^2),
#   N cresce com raiz(P): N = 2000 * sqrt(P).
#
# Uso: bash scripts/medicao_mpi.sh   (dentro do contêiner, após make seq mpi)

SEQ=./bin/06_nbody
MPI=./bin/06_nbody_mpi
OUT=resultados/mpi.csv
PASSOS=10
REPS=5
NPS="1 2 3 4"

for b in "$SEQ" "$MPI"; do
  if [ ! -x "$b" ]; then echo "Compile antes: make seq mpi"; exit 1; fi
done

mkdir -p resultados
echo "escala,versao,N,np,rep,tempo_s,comm_s,checksum" > "$OUT"

# roda "$@" REPS+1 vezes e grava as REPS últimas no CSV
mede() {
  local escala=$1 versao=$2 N=$3 np=$4; shift 4
  for r in $(seq 0 $REPS); do
    line=$("$@")
    [ "$r" -eq 0 ] && continue
    t=$(echo "$line" | sed -n 's/.*tempo=\([0-9.]*\) s.*/\1/p')
    c=$(echo "$line" | sed -n 's/.*comm=\([0-9.]*\) s.*/\1/p')
    k=$(echo "$line" | sed -n 's/.*checksum=\([-0-9.]*\).*/\1/p')
    echo "$escala,$versao,$N,$np,$r,$t,${c:-0},$k" >> "$OUT"
  done
  echo "$escala $versao N=$N np=$np ok"
}

for N in 2000 4000 8000; do
  mede forte seq $N 0 $SEQ $N $PASSOS
  for P in $NPS; do
    mede forte mpi $N $P mpirun --bind-to core -np $P $MPI $N $PASSOS
  done
done

for P in $NPS; do
  N=$(awk -v p=$P 'BEGIN { printf "%d", 2000 * sqrt(p) + 0.5 }')
  mede fraca mpi $N $P mpirun --bind-to core -np $P $MPI $N $PASSOS
done

echo "Pronto: $OUT"
