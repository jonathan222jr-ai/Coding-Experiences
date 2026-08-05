/*
 * openmp_matvec.c
 * Simple matrix-vector multiply b = A*x with OpenMP.
 * Usage: ./openmp_matvec <N> <threads> <chunk> <repeats>
 * Defaults: N=1000, threads=4, chunk=16, repeats=3
 */

#include <stdio.h>
#include <stdlib.h>
#include "omp.h"

int main(int argc, char **argv) {
    int N = 1000; /* default matrix size */
    if (argc > 1) N = atoi(argv[1]);

    int threads = 4;
    int chunk = 16;
    int repeats = 3;
    if (argc > 2) threads = atoi(argv[2]);
    if (argc > 3) chunk = atoi(argv[3]);
    if (argc > 4) repeats = atoi(argv[4]);

    size_t NN = (size_t)N * (size_t)N;
    double *A = malloc(NN * sizeof(double));
    double *x = malloc((size_t)N * sizeof(double));
    double *b = malloc((size_t)N * sizeof(double));
    if (!A || !x || !b) {
        fprintf(stderr, "Allocation failed for N=%d\n", N);
        return 1;
    }

    /* Initialize A and x with simple values */
    for (int i = 0; i < N; ++i) {
        x[i] = 1.0;
        for (int j = 0; j < N; ++j) {
            A[(size_t)i * N + j] = (double)(i + j + 1);
        }
    }

    printf("Matrix-vector multiply: N=%d, threads=%d, chunk=%d, repeats=%d\n",
           N, threads, chunk, repeats);

    omp_set_num_threads(threads);

    const char *schedules[] = {"static", "dynamic", "guided"};
    for (int si = 0; si < 3; ++si) {
        const char *sched = schedules[si];
        double total_time = 0.0;
        double last_checksum = 0.0;

        for (int r = 0; r < repeats; ++r) {
            double start = omp_get_wtime();

            if (si == 0) {
#pragma omp parallel for schedule(static)
                for (int i = 0; i < N; ++i) {
                    double sum = 0.0;
                    for (int j = 0; j < N; ++j) sum += A[(size_t)i * N + j] * x[j];
                    b[i] = sum;
                }
            } else if (si == 1) {
#pragma omp parallel for schedule(dynamic, chunk)
                for (int i = 0; i < N; ++i) {
                    double sum = 0.0;
                    for (int j = 0; j < N; ++j) sum += A[(size_t)i * N + j] * x[j];
                    b[i] = sum;
                }
            } else {
#pragma omp parallel for schedule(guided, chunk)
                for (int i = 0; i < N; ++i) {
                    double sum = 0.0;
                    for (int j = 0; j < N; ++j) sum += A[(size_t)i * N + j] * x[j];
                    b[i] = sum;
                }
            }

            double elapsed = omp_get_wtime() - start;
            total_time += elapsed;

            double checksum = 0.0;
            for (int i = 0; i < N; ++i) checksum += b[i];
            last_checksum = checksum;
        }

        double avg = total_time / repeats;
        printf("sched=%7s threads=%2d avg_time=%10.6f checksum=%f\n",
               sched, threads, avg, last_checksum);
    }

    free(A); free(x); free(b);
    return 0;
}
