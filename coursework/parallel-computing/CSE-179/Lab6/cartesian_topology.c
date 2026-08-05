#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    MPI_Init(&argc, &argv);

    int world_rank, world_size;
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    // 4x4 topology requires exactly 16 processes
    if (world_size != 16) {
        if (world_rank == 0) {
            printf("This program requires exactly 16 MPI processes for a 4x4 Cartesian topology.\n");
        }
        MPI_Finalize();
        return 1;
    }

    MPI_Comm cart_comm;
    int dims[2] = {4, 4};
    int periods[2] = {1, 1};   // periodic in both dimensions
    int reorder = 1;           // allow MPI to reorder ranks

    // You could also do:
    // int dims[2] = {0, 0};
    // MPI_Dims_create(world_size, 2, dims);
    // For 16 processes this should give 4x4.
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, reorder, &cart_comm);

    int cart_rank;
    MPI_Comm_rank(cart_comm, &cart_rank);

    int coords[2];
    MPI_Cart_coords(cart_comm, cart_rank, 2, coords);

    // Find neighbors
    int north, south, west, east;

    // direction 0 = rows
    MPI_Cart_shift(cart_comm, 0, 1, &north, &south);

    // direction 1 = columns
    MPI_Cart_shift(cart_comm, 1, 1, &west, &east);

    // Exchange local Cartesian ranks with neighbors
    int my_value = cart_rank;
    int north_val, south_val, west_val, east_val;

    MPI_Sendrecv(&my_value, 1, MPI_INT, north, 0,
                 &south_val, 1, MPI_INT, south, 0,
                 cart_comm, MPI_STATUS_IGNORE);

    MPI_Sendrecv(&my_value, 1, MPI_INT, south, 1,
                 &north_val, 1, MPI_INT, north, 1,
                 cart_comm, MPI_STATUS_IGNORE);

    MPI_Sendrecv(&my_value, 1, MPI_INT, west, 2,
                 &east_val, 1, MPI_INT, east, 2,
                 cart_comm, MPI_STATUS_IGNORE);

    MPI_Sendrecv(&my_value, 1, MPI_INT, east, 3,
                 &west_val, 1, MPI_INT, west, 3,
                 cart_comm, MPI_STATUS_IGNORE);

    double average = (my_value + north_val + east_val + south_val + west_val) / 5.0;

    MPI_Barrier(cart_comm);
    printf("WORLD rank=%2d  CART rank=%2d  coords=(%d,%d)  "
           "N=%2d E=%2d S=%2d W=%2d  avg=%.2f\n",
           world_rank, cart_rank, coords[0], coords[1],
           north_val, east_val, south_val, west_val, average);

    MPI_Comm_free(&cart_comm);
    MPI_Finalize();
    return 0;
}