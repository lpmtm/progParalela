"""Gráficos da versão MPI a partir de resultados/mpi.csv.

Gera resultados/mpi_resumo.csv (medianas, desvio, speedup, eficiência, overhead)
e os PNGs em resultados/graficos/.

Uso: python3 scripts/graficos_mpi.py   (precisa de matplotlib)
"""
import csv
import os
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ENTRADA = "resultados/mpi.csv"
RESUMO = "resultados/mpi_resumo.csv"
PASTA = "resultados/graficos"

# Cores fixas por N (a mesma cor representa o mesmo N em todos os gráficos)
CORES = {2000: "#2a78d6", 4000: "#eb6834", 8000: "#1baf7a"}
CINZA = "#8a8984"
TEXTO = "#52514e"

# Fração paralelizável estimada no Marco 1 (95% a 99%)
AMDAHL = [0.95, 0.99]


def carrega():
    tempos, comms = defaultdict(list), defaultdict(list)
    with open(ENTRADA) as f:
        for l in csv.DictReader(f):
            k = (l["escala"], l["versao"], int(l["N"]), int(l["np"]))
            tempos[k].append(float(l["tempo_s"]))
            comms[k].append(float(l["comm_s"]))
    return tempos, comms


def estilo(ax, titulo, ylabel):
    ax.set_title(titulo, loc="left", fontsize=12, color="#0b0b0b")
    ax.set_xlabel("Número de processos (np)", color=TEXTO)
    ax.set_ylabel(ylabel, color=TEXTO)
    ax.set_xticks([1, 2, 3, 4])
    ax.grid(True, color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#c3c2b7")
    ax.tick_params(colors=TEXTO)


def salva(fig, nome):
    fig.tight_layout()
    fig.savefig(os.path.join(PASTA, nome), dpi=150)
    plt.close(fig)
    print("gerado:", os.path.join(PASTA, nome))


def main():
    os.makedirs(PASTA, exist_ok=True)
    tempos, comms = carrega()
    if not any(k[0] == "fraca" and k[3] == 4 for k in tempos):
        raise SystemExit(f"{ENTRADA} está incompleto (medição interrompida?). "
                         "Rode a medição até o fim: make medicao-mpi")
    media = {k: statistics.median(v) for k, v in tempos.items()}
    desvio = {k: statistics.stdev(v) if len(v) > 1 else 0 for k, v in tempos.items()}
    comm = {k: statistics.median(v) for k, v in comms.items()}

    Ns = sorted({k[2] for k in media if k[0] == "forte" and k[1] == "mpi"})
    Ps = sorted({k[3] for k in media if k[0] == "forte" and k[1] == "mpi"})

    # Resumo: speedup em relação ao sequencial medido na mesma máquina
    linhas = []
    for N in Ns:
        tseq = media[("forte", "seq", N, 0)]
        linhas.append(["forte", "seq", N, 0, tseq, desvio[("forte", "seq", N, 0)], 0, "", "", ""])
        for P in Ps:
            k = ("forte", "mpi", N, P)
            s = tseq / media[k]
            linhas.append(["forte", "mpi", N, P, media[k], desvio[k], comm[k],
                           s, s / P, comm[k] / media[k]])
    fracas = sorted((k for k in media if k[0] == "fraca"), key=lambda k: k[3])
    t1 = media[fracas[0]]
    for k in fracas:
        linhas.append(["fraca", "mpi", k[2], k[3], media[k], desvio[k], comm[k],
                       "", t1 / media[k], comm[k] / media[k]])
    with open(RESUMO, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["escala", "versao", "N", "np", "tempo_mediana_s", "desvio_s",
                    "comm_mediana_s", "speedup", "eficiencia", "fracao_comm"])
        for l in linhas:
            w.writerow([f"{v:.6f}" if isinstance(v, float) else v for v in l])
    print("gerado:", RESUMO)

    # Resumo legível no terminal
    print("\nESCALABILIDADE FORTE (N fixo, mais processos)")
    print(f"{'N':>6} {'np':>4} {'tempo (s)':>10} {'speedup':>8} {'eficiência':>11} {'% comm':>7}")
    for l in linhas:
        if l[0] != "forte":
            continue
        if l[1] == "seq":
            print(f"{l[2]:>6} {'seq':>4} {l[4]:>10.4f} {'—':>8} {'—':>11} {'—':>7}")
        else:
            print(f"{l[2]:>6} {l[3]:>4} {l[4]:>10.4f} {l[7]:>7.2f}x {100*l[8]:>10.0f}% {100*l[9]:>6.1f}%")
    print("\nESCALABILIDADE FRACA (trabalho por processo constante; ideal = tempo igual)")
    print(f"{'N':>6} {'np':>4} {'tempo (s)':>10} {'eficiência':>11}")
    for l in linhas:
        if l[0] == "fraca":
            print(f"{l[2]:>6} {l[3]:>4} {l[4]:>10.4f} {100*l[8]:>10.0f}%")
    print()

    def speedup(N, P):
        return media[("forte", "seq", N, 0)] / media[("forte", "mpi", N, P)]

    # 1. Tempo (escala log: os N diferem em ~16x de custo)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for N in Ns:
        ys = [media[("forte", "mpi", N, P)] for P in Ps]
        es = [desvio[("forte", "mpi", N, P)] for P in Ps]
        ax.errorbar(Ps, ys, yerr=es, color=CORES[N], marker="o", markersize=6,
                    linewidth=2, capsize=3, label=f"N={N}")
        ax.annotate(f"N={N}", (Ps[-1], ys[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", color=TEXTO)
    ax.set_yscale("log")
    ax.set_yticks([0.1, 0.2, 0.5, 1, 2, 5])
    ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%g"))
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    estilo(ax, "Tempo de execução (10 passos)", "Tempo (s, escala log)")
    ax.set_xlim(0.8, 4.6)
    ax.legend(frameon=False)
    salva(fig, "mpi_tempo.png")

    # 2. Speedup com ideal e Amdahl
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(Ps, Ps, color=CINZA, linestyle="--", linewidth=1.5, label="Ideal (linear)")
    for f, ls in zip(AMDAHL, [":", "-."]):
        ax.plot(Ps, [1 / ((1 - f) + f / P) for P in Ps], color=CINZA, linestyle=ls,
                linewidth=1.5, label=f"Amdahl f={f:.2f}")
    for N in Ns:
        ax.plot(Ps, [speedup(N, P) for P in Ps], color=CORES[N], marker="o",
                markersize=6, linewidth=2, label=f"N={N}")
    estilo(ax, "Speedup em relação ao sequencial", "Speedup")
    ax.legend(frameon=False)
    salva(fig, "mpi_speedup.png")

    # 3. Eficiência
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.axhline(1.0, color=CINZA, linestyle="--", linewidth=1.5, label="Ideal")
    for N in Ns:
        ax.plot(Ps, [speedup(N, P) / P for P in Ps], color=CORES[N], marker="o",
                markersize=6, linewidth=2, label=f"N={N}")
    estilo(ax, "Eficiência (speedup / np)", "Eficiência")
    ax.set_ylim(0, 1.3)
    ax.legend(frameon=False)
    salva(fig, "mpi_eficiencia.png")

    # 4. Overhead de comunicação: fração do tempo dentro do Allgatherv
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for N in Ns:
        ax.plot(Ps, [100 * comm[("forte", "mpi", N, P)] / media[("forte", "mpi", N, P)]
                     for P in Ps], color=CORES[N], marker="o", markersize=6,
                linewidth=2, label=f"N={N}")
    estilo(ax, "Tempo em comunicação (Allgatherv + espera)", "% do tempo total")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    salva(fig, "mpi_overhead.png")

    # 5. Escalabilidade fraca: N = 2000*sqrt(np), trabalho por processo constante
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.axhline(1.0, color=CINZA, linestyle="--", linewidth=1.5, label="Ideal")
    xs = [k[3] for k in fracas]
    ys = [t1 / media[k] for k in fracas]
    ax.plot(xs, ys, color=CORES[2000], marker="o", markersize=6, linewidth=2,
            label="Eficiência fraca")
    for k, y in zip(fracas, ys):
        ax.annotate(f"N={k[2]}", (k[3], y), xytext=(0, -16),
                    textcoords="offset points", ha="center", color=TEXTO, fontsize=9)
    estilo(ax, "Escalabilidade fraca (N = 2000·√np)", "Eficiência (T₁ / Tₚ)")
    ax.set_ylim(0, 1.3)
    ax.legend(frameon=False)
    salva(fig, "mpi_fraca.png")


if __name__ == "__main__":
    main()
