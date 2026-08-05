#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

#define LOCAL_N 10
#define BLOCK   2

static void check_equal_or_abort(int cond, const char *msg, MPI_Comm comm) {
    if (!cond) {
        int rank;
        MPI_Comm_rank(comm, &rank);
        if (rank == 0) {
            fprintf(stderr, "%s\n", msg);
        }
        MPI_Abort(comm, 1);
    }
}

int main(int argc, char *argv[]) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    check_equal_or_abort(LOCAL_N % BLOCK == 0,
                         "LOCAL_N must be divisible by BLOCK.",
                         MPI_COMM_WORLD);

    const int nchunks = LOCAL_N / BLOCK;

    int write_buf[LOCAL_N];
    int read_buf[LOCAL_N];

    for (int i = 0; i < LOCAL_N; i++) {
        write_buf[i] = rank * LOCAL_N + i;
        read_buf[i] = -1;
    }

    MPI_File fh;
    MPI_Status status;
    MPI_Offset offset_bytes;
    MPI_Offset filesize;

    /* ---------------------------------------------------------
       STEP I:
       Each process writes 10 ints using its individual file pointer.
       rank r writes at integer position r*10.
       --------------------------------------------------------- */
    MPI_File_open(MPI_COMM_WORLD,
                  "step12.bin",
                  MPI_MODE_CREATE | MPI_MODE_RDWR,
                  MPI_INFO_NULL,
                  &fh);

    offset_bytes = (MPI_Offset)rank * LOCAL_N * sizeof(int);
    MPI_File_seek(fh, offset_bytes, MPI_SEEK_SET);
    MPI_File_write(fh, write_buf, LOCAL_N, MPI_INT, &status);

    /* Make data visible before closing/reopening */
    MPI_File_sync(fh);
    MPI_File_close(&fh);

    /* ---------------------------------------------------------
       STEP II:
       Re-open and read back using explicit offsets.
       Each process reads the same 10 ints it wrote.
       --------------------------------------------------------- */
    MPI_File_open(MPI_COMM_WORLD,
                  "step12.bin",
                  MPI_MODE_RDONLY,
                  MPI_INFO_NULL,
                  &fh);

    offset_bytes = (MPI_Offset)rank * LOCAL_N * sizeof(int);
    MPI_File_read_at(fh, offset_bytes, read_buf, LOCAL_N, MPI_INT, &status);

    /* Optional: check file size */
    MPI_File_get_size(fh, &filesize);
    if (rank == 0) {
        printf("step12.bin size = %lld bytes\n", (long long)filesize);
    }

    /* Verify read correctness */
    int ok = 1;
    for (int i = 0; i < LOCAL_N; i++) {
        if (read_buf[i] != rank * LOCAL_N + i) {
            ok = 0;
            break;
        }
    }

    if (!ok) {
        printf("Rank %d: read verification FAILED\n", rank);
    } else {
        printf("Rank %d: read verification PASSED\n", rank);
    }

    MPI_File_close(&fh);

    /* ---------------------------------------------------------
       STEP III:
       Reorganize data into chunk-interleaved layout using file views
       and collective write.

       For each rank, local buffer is still contiguous:
         [x0 x1 x2 x3 x4 x5 x6 x7 x8 x9]

       But in the file, write as 5 blocks of 2 ints each with stride
       of 2*size ints between block starts.
       --------------------------------------------------------- */
    MPI_File_open(MPI_COMM_WORLD,
                  "step3.bin",
                  MPI_MODE_CREATE | MPI_MODE_RDWR,
                  MPI_INFO_NULL,
                  &fh);

    /* Build filetype: 5 blocks, each of length 2 ints,
       spaced every 2*size ints in the file. */
    MPI_Datatype filetype;
    MPI_Type_vector(nchunks,           /* count      */
                    BLOCK,             /* blocklength*/
                    BLOCK * size,      /* stride in etypes (MPI_INTs) */
                    MPI_INT,
                    &filetype);
    MPI_Type_commit(&filetype);

    /* rank r starts at the r-th slot of each round */
    MPI_Offset disp = (MPI_Offset)rank * BLOCK * sizeof(int);

    MPI_File_set_view(fh,
                      disp,
                      MPI_INT,
                      filetype,
                      "native",
                      MPI_INFO_NULL);

    /* Collective write from contiguous local memory to strided file view */
    MPI_File_write_all(fh, read_buf, LOCAL_N, MPI_INT, &status);

    MPI_File_sync(fh);
    MPI_File_close(&fh);

    MPI_Type_free(&filetype);

    /* Optional pretty print */
    MPI_Barrier(MPI_COMM_WORLD);
    for (int r = 0; r < size; r++) {
        if (rank == r) {
            printf("Rank %d local data: ", rank);
            for (int i = 0; i < LOCAL_N; i++) {
                printf("%d ", read_buf[i]);
            }
            printf("\n");
            fflush(stdout);
        }
        MPI_Barrier(MPI_COMM_WORLD);
    }

    if (rank == 0) {
        printf("\nUse these to inspect the files:\n");
        printf("  od -i step12.bin\n");
        printf("  od -i step3.bin\n");
    }

    MPI_Finalize();
    return 0;
}