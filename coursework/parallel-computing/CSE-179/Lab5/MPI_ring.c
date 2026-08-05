#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>

int main(int argc, char *argv[]) {
    int rank, numprocs;
    int message;
    MPI_Status status;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &numprocs);

    /* Need at least 2 processes for a ring */
    if (numprocs < 2) {
        if (rank == 0) {
            printf("Please run with at least 2 processes.\n");
        }
        MPI_Finalize();
        return 0;
    }

    if (rank == 0) {
        /* Start the ring */
        message = rank;
        MPI_Send(&message, 1, MPI_INT, 1, 0, MPI_COMM_WORLD);

        /* Receive final message from last process */
        MPI_Recv(&message, 1, MPI_INT, numprocs - 1, 0, MPI_COMM_WORLD, &status);

        printf("Process 0 received final message %d from process %d\n",
               message, numprocs - 1);
    } else {
        /* Receive from previous process */
        MPI_Recv(&message, 1, MPI_INT, rank - 1, 0, MPI_COMM_WORLD, &status);

        /* Verify message */
        if (message != rank - 1) {
            printf("Process %d ERROR: expected %d but got %d\n",
                   rank, rank - 1, message);
        }

        /* Replace with own rank */
        message = rank;

        /* Send to next process, or back to 0 if last */
        if (rank == numprocs - 1) {
            MPI_Send(&message, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);
        } else {
            MPI_Send(&message, 1, MPI_INT, rank + 1, 0, MPI_COMM_WORLD);
        }
    }

    MPI_Finalize();
    return 0;
}