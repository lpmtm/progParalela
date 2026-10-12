#!/bin/bash
# uso: ./compara.sh referencia.txt novo.txt
if cmp -s "$1" "$2"; then
  echo "IDENTICO (bit a bit): $2"
  exit 0
fi
paste -d' ' "$1" "$2" | awk '
{ for (k = 1; k <= 4; k++) {
    a = $k; b = $(k+4); d = a - b; if (d < 0) d = -d;
    m = (a < 0 ? -a : a);
    if (d > 0) n++;
    if (m > 0 && d/m > max) max = d/m;
  }
}
END { printf "DIFERENTES: %d valores, erro relativo maximo = %g\n", n+0, max+0 }'
exit 1
