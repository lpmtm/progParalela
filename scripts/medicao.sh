BIN=./bin/06_nbody
OUT=resultados/baseline.csv

if [ ! -x "$BIN" ]; then
  echo "Compile antes: g++ -O2 -o 06_nbody 06_nbody.cpp"
  exit 1
fi

mkdir -p resultados
echo "N,passos,rep,tempo_s,checksum" > "$OUT"

for N in 1000 2000 4000 8000; do
  for r in 0 1 2 3 4 5; do
    line=$($BIN $N 10)
    if [ "$r" -eq 0 ]; then
      echo "aquecimento N=$N (descartado)"
      continue
    fi
    t=$(echo "$line" | sed -n 's/.*tempo=\([0-9.]*\) s/\1/p')
    c=$(echo "$line" | sed -n 's/.*checksum=\([-0-9.]*\).*/\1/p')
    echo "$N,10,$r,$t,$c" >> "$OUT"
  done
done
echo "Pronto: $OUT"