#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    const int N = 25;  // Try different sizes

    int *array = NULL;
    int *local = NULL;

    MPI_Barrier(MPI_COMM_WORLD);
    double start = MPI_Wtime();

    // Root initializes array
    if (rank == 0) {
        array = (int *)malloc(N * sizeof(int));
        for (int i = 0; i < N; i++) {
            array[i] = i;
        }
    }

    // =========================
    // CASE 1: Use Scatter/Gather
    // =========================
    if (N % size == 0) {
        int chunk = N / size;
        local = (int *)malloc(chunk * sizeof(int));

        MPI_Scatter(array, chunk, MPI_INT,
                    local, chunk, MPI_INT,
                    0, MPI_COMM_WORLD);

        for (int i = 0; i < chunk; i++) {
            local[i] += rank;
        }

        MPI_Gather(local, chunk, MPI_INT,
                   array, chunk, MPI_INT,
                   0, MPI_COMM_WORLD);

        if (rank == 0) {
            printf("\nUsed MPI_Scatter / MPI_Gather\n");
        }
    }

    // =========================
    // CASE 2: Use Scatterv/Gatherv
    // =========================
    else {
        int *sendcounts = (int *)malloc(size * sizeof(int));
        int *displs = (int *)malloc(size * sizeof(int));

        int base = N / size;
        int rem = N % size;

        for (int i = 0; i < size; i++) {
            sendcounts[i] = base + (i < rem ? 1 : 0);
        }

        displs[0] = 0;
        for (int i = 1; i < size; i++) {
            displs[i] = displs[i - 1] + sendcounts[i - 1];
        }

        int local_n = sendcounts[rank];
        local = (int *)malloc(local_n * sizeof(int));

        MPI_Scatterv(array, sendcounts, displs, MPI_INT,
                     local, local_n, MPI_INT,
                     0, MPI_COMM_WORLD);

        for (int i = 0; i < local_n; i++) {
            local[i] += rank;
        }

        MPI_Gatherv(local, local_n, MPI_INT,
                    array, sendcounts, displs, MPI_INT,
                    0, MPI_COMM_WORLD);

        if (rank == 0) {
            printf("\nUsed MPI_Scatterv / MPI_Gatherv\n");
        }

        free(sendcounts);
        free(displs);
    }

    MPI_Barrier(MPI_COMM_WORLD);
    double end = MPI_Wtime();

    // Print result at root
    if (rank == 0) {
        printf("Final array:\n");
        for (int i = 0; i < N; i++) {
            printf("%d ", array[i]);
        }
        printf("\n");

        printf("Execution time with %d processes: %f seconds\n",
               size, end - start);

        free(array);
    }

    free(local);
    MPI_Finalize();
    return 0;
}