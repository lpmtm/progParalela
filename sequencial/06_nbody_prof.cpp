#include <cstdio>
#include <cstdlib>
#include <vector>
#include <cmath>
#include <ctime>
using namespace std;

static double agora() {
    timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(int argc, char** argv) {
    int N = (argc > 1) ? atoi(argv[1]) : 2000;
    int STEPS = (argc > 2) ? atoi(argv[2]) : 10;
    const double G = 6.674e-11, DT = 0.01, EPS = 1e-9;

    vector<double> x(N), y(N), vx(N, 0), vy(N, 0), m(N);
    for (int i = 0; i < N; i++) {
        x[i] = (i % 100) * 1.0; y[i] = (i / 100) * 1.0; m[i] = 1.0 + (i % 10);
    }

    double tf = 0, tu = 0;
    double t0 = agora();
    for (int s = 0; s < STEPS; s++) {
        vector<double> fx(N, 0), fy(N, 0);

        double a = agora();
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++) if (i != j) {
                double dx = x[j]-x[i], dy = y[j]-y[i];
                double d2 = dx*dx + dy*dy + EPS;
                double f = G * m[i] * m[j] / d2;
                double inv = 1.0 / sqrt(d2);
                fx[i] += f * dx * inv; fy[i] += f * dy * inv;
            }
        tf += agora() - a;

        a = agora();
        for (int i = 0; i < N; i++) {
            vx[i] += DT * fx[i] / m[i]; vy[i] += DT * fy[i] / m[i];
            x[i] += DT * vx[i]; y[i] += DT * vy[i];
        }
        tu += agora() - a;
    }
    double t1 = agora();

    double soma = 0;
    for (int i = 0; i < N; i++) soma += x[i] + y[i];
    printf("N=%d passos=%d  checksum=%.6f  tempo=%.6f s\n", N, STEPS, soma, t1 - t0);
    printf("forcas=%.6f s  atualizacao=%.6f s  f=%.6f\n", tf, tu, tf / (tf + tu));
    return 0;
}