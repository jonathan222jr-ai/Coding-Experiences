#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <mpi.h>
 

double *alloc_matrix(int n) {
    double *m = (double *)malloc((size_t)n * n * sizeof(double));
    if (!m) { fprintf(stderr, "malloc failed\n"); MPI_Abort(MPI_COMM_WORLD, 1); }
    return m;
}
 

void rand_matrix(double *m, int n) {
    for (int i = 0; i < n * n; i++)
        m[i] = (double)rand() / RAND_MAX;
}
 

void serial_matmul(double *A, double *B, double *C, int n) {
    memset(C, 0, (size_t)n * n * sizeof(double));
    for (int i = 0; i < n; i++)
        for (int k = 0; k < n; k++) {
            double aik = A[i * n + k];
            for (int j = 0; j < n; j++)
                C[i * n + j] += aik * B[k * n + j];
        }
}
 

double max_diff(double *X, double *Y, int n) {
    double d = 0.0;
    for (int i = 0; i < n * n; i++) {
        double diff = fabs(X[i] - Y[i]);
        if (diff > d) d = diff;
    }
    return d;
}
 
int main(int argc, char *argv[]) {
    int rank, nprocs;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &nprocs);
 
    if (argc < 3) {
        if (rank == 0)
            fprintf(stderr, "Usage: %s <n> <q>\n  n = matrix size, q = block size (num procs = q)\n", argv[0]);
        MPI_Finalize();
        return 1;
    }
 
    int n = atoi(argv[1]);
    int q = atoi(argv[2]);  
 
    if (nprocs != q) {
        if (rank == 0)
            fprintf(stderr, "Error: must launch with exactly q=%d MPI processes (got %d)\n", q, nprocs);
        MPI_Finalize();
        return 1;
    }
 
    if (n % q != 0) {
        if (rank == 0)
            fprintf(stderr, "Error: n=%d must be divisible by q=%d\n", n, q);
        MPI_Finalize();
        return 1;
    }
 
    int rows_per_proc = n / q;   /* rows each processor owns */
 
    
    double *A = NULL, *B = NULL, *C_parallel = NULL, *C_serial = NULL;
    if (rank == 0) {
        srand(42);
        A = alloc_matrix(n);
        B = alloc_matrix(n);
        C_parallel = alloc_matrix(n);
        C_serial   = alloc_matrix(n);
        rand_matrix(A, n);
        rand_matrix(B, n);
    }
 
   
    double *B_local = alloc_matrix(n);   /* every proc keeps full B */
    if (rank == 0) memcpy(B_local, B, (size_t)n * n * sizeof(double));
    MPI_Bcast(B_local, n * n, MPI_DOUBLE, 0, MPI_COMM_WORLD);
 
    
    double *A_local = (double *)malloc((size_t)rows_per_proc * n * sizeof(double));
    MPI_Scatter(A, rows_per_proc * n, MPI_DOUBLE,
                A_local, rows_per_proc * n, MPI_DOUBLE,
                0, MPI_COMM_WORLD);
 
    
    double *C_local = (double *)malloc((size_t)rows_per_proc * n * sizeof(double));
    memset(C_local, 0, (size_t)rows_per_proc * n * sizeof(double));
 
    MPI_Barrier(MPI_COMM_WORLD);
    double t_start = MPI_Wtime();
 
    for (int i = 0; i < rows_per_proc; i++)
        for (int k = 0; k < n; k++) {
            double aik = A_local[i * n + k];
            for (int j = 0; j < n; j++)
                C_local[i * n + j] += aik * B_local[k * n + j];
        }
 
    MPI_Barrier(MPI_COMM_WORLD);
    double t_end = MPI_Wtime();
    double elapsed = t_end - t_start;
 
    
    MPI_Gather(C_local, rows_per_proc * n, MPI_DOUBLE,
               C_parallel, rows_per_proc * n, MPI_DOUBLE,
               0, MPI_COMM_WORLD);
 
    
    if (rank == 0) {
        /* Serial reference */
        serial_matmul(A, B, C_serial, n);
 
        double err = max_diff(C_parallel, C_serial, n);
 
        printf("=== Parallel Matrix Multiplication ===\n");
        printf("Matrix size : %d x %d\n", n, n);
        printf("Block size q: %d  (processes: %d, rows/proc: %d)\n", q, nprocs, rows_per_proc);
        printf("Max error vs serial: %.2e  %s\n", err, (err < 1e-9 ? "[PASS]" : "[FAIL]"));
        printf("Parallel time: %.6f seconds\n", elapsed);
        printf("GFLOPS: %.4f\n", 2.0 * n * n * n / elapsed / 1e9);
    }
 
    
    free(A_local); free(B_local); free(C_local);
    if (rank == 0) { free(A); free(B); free(C_parallel); free(C_serial); }
 
    MPI_Finalize();
    return 0;
}