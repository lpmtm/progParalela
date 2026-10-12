/* Versão MPI 06 — Simulação de N corpos (memória distribuída)
 * Frente 3 — a partir de sequencial/06_nbody.cpp (cálculo inalterado)
 *
 * Decomposição de domínio: cada processo é dono de um bloco contíguo de
 * índices i e calcula fx, fy, vx, vy, x, y só desse bloco. O laço interno
 * continua varrendo j = 0..N-1 na mesma ordem do sequencial, então cada
 * fx[i] é somado na mesma ordem e o resultado é idêntico bit a bit.
 *
 * Comunicação por passo: MPI_Allgatherv de x e y (todo processo precisa das
 * posições de todos os corpos para o próximo cálculo de forças).
 *
 * Compilar: mpicxx -O2 -o 06_nbody_mpi 06_nbody_mpi.cpp
 * Executar: mpirun -np 4 ./06_nbody_mpi 2000 10 [estado.txt]
 *           (o 3º argumento, opcional, grava o estado final para validação)
 */
#include <mpi.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <cmath>
using namespace std;

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, P;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &P);

    int N = (argc > 1) ? atoi(argv[1]) : 2000;
    int STEPS = (argc > 2) ? atoi(argv[2]) : 10;
    const char* saida = (argc > 3) ? argv[3] : NULL;
    const double G = 6.674e-11, DT = 0.01, EPS = 1e-9;

    // Blocos: os N % P primeiros processos ficam com um corpo a mais.
    // counts/displs são exigidos pelo Allgatherv (N não precisa ser divisível por P).
    vector<int> counts(P), displs(P);
    for (int r = 0, off = 0; r < P; r++) {
        counts[r] = N / P + (r < N % P ? 1 : 0);
        displs[r] = off;
        off += counts[r];
    }
    int ini = displs[rank], nloc = counts[rank], fim = ini + nloc;

    // Inicialização por fórmula: cada processo gera tudo sozinho, sem Bcast.
    // x, y, m são replicados (todos leem); vx, vy só são usados no próprio bloco.
    vector<double> x(N), y(N), vx(N, 0), vy(N, 0), m(N);
    for (int i = 0; i < N; i++) {
        x[i] = (i % 100) * 1.0; y[i] = (i / 100) * 1.0; m[i] = 1.0 + (i % 10);
    }

    MPI_Barrier(MPI_COMM_WORLD);  // todos começam a cronometrar juntos
    double t0 = MPI_Wtime(), tcomm = 0;
    for (int s = 0; s < STEPS; s++) {
        vector<double> fx(nloc, 0), fy(nloc, 0);
        for (int i = ini; i < fim; i++)
            for (int j = 0; j < N; j++) if (i != j) {
                double dx = x[j]-x[i], dy = y[j]-y[i];
                double d2 = dx*dx + dy*dy + EPS;
                double f = G * m[i] * m[j] / d2;
                double inv = 1.0 / sqrt(d2);
                fx[i-ini] += f * dx * inv; fy[i-ini] += f * dy * inv;
            }
        for (int i = ini; i < fim; i++) {
            vx[i] += DT * fx[i-ini] / m[i]; vy[i] += DT * fy[i-ini] / m[i];
            x[i] += DT * vx[i]; y[i] += DT * vy[i];
        }

        // Cada processo contribui com o seu bloco (já está na posição certa
        // do vetor, por isso MPI_IN_PLACE) e recebe os blocos dos outros.
        double tc = MPI_Wtime();
        MPI_Allgatherv(MPI_IN_PLACE, 0, MPI_DATATYPE_NULL,
                       x.data(), counts.data(), displs.data(), MPI_DOUBLE, MPI_COMM_WORLD);
        MPI_Allgatherv(MPI_IN_PLACE, 0, MPI_DATATYPE_NULL,
                       y.data(), counts.data(), displs.data(), MPI_DOUBLE, MPI_COMM_WORLD);
        tcomm += MPI_Wtime() - tc;
    }
    double tloc = MPI_Wtime() - t0;

    // Tempo do programa = o do processo mais lento.
    double tempo, comm;
    MPI_Reduce(&tloc, &tempo, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&tcomm, &comm, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    // Depois do último Allgatherv, x e y estão completos em todos os processos:
    // o rank 0 soma na mesma ordem do sequencial (mesmo checksum, bit a bit).
    if (rank == 0) {
        double soma = 0;
        for (int i = 0; i < N; i++) soma += x[i] + y[i];
        printf("N=%d passos=%d  checksum=%.6f  tempo=%.6f s  comm=%.6f s  np=%d\n",
               N, STEPS, soma, tempo, comm, P);
    }

    // Validação: junta vx, vy no rank 0 e grava no mesmo formato de 06_nbody_valid.
    if (saida) {
        MPI_Gatherv(rank == 0 ? MPI_IN_PLACE : vx.data() + ini, nloc, MPI_DOUBLE,
                    vx.data(), counts.data(), displs.data(), MPI_DOUBLE, 0, MPI_COMM_WORLD);
        MPI_Gatherv(rank == 0 ? MPI_IN_PLACE : vy.data() + ini, nloc, MPI_DOUBLE,
                    vy.data(), counts.data(), displs.data(), MPI_DOUBLE, 0, MPI_COMM_WORLD);
        if (rank == 0) {
            FILE* f = fopen(saida, "w");
            if (!f) { perror("fopen"); MPI_Abort(MPI_COMM_WORLD, 1); }
            for (int i = 0; i < N; i++)
                fprintf(f, "%.17g %.17g %.17g %.17g\n", x[i], y[i], vx[i], vy[i]);
            fclose(f);
        }
    }

    MPI_Finalize();
    return 0;
}
