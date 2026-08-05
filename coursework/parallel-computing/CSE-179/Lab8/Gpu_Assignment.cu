#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <cuda_runtime.h>

/* ---------- error-checking macro ---------- */
#define CUDA_CHECK(call)                                                        \
    do {                                                                        \
        cudaError_t _e = (call);                                                \
        if (_e != cudaSuccess) {                                                \
            fprintf(stderr, "CUDA error %s:%d  %s\n",                          \
                    __FILE__, __LINE__, cudaGetErrorString(_e));                 \
            exit(EXIT_FAILURE);                                                 \
        }                                                                       \
    } while (0)

/* ---------- tile dimensions for shared memory ---------- */
#define TILE_W 16
#define TILE_H 16

/* ================================================================
 * CUDA Kernel
 * Each thread handles one cell (i, j).
 * We use shared memory with a halo of 1 cell on every side so that
 * neighbor lookups stay in fast SMEM rather than global memory.
 * ================================================================ */
__global__ void stepKernel(const int *__restrict__ in,
                            int       *__restrict__ out,
                            int M, int N)
{
    /* Shared tile includes a 1-cell halo on all four sides */
    __shared__ int tile[TILE_H + 2][TILE_W + 2];

    int tx = threadIdx.x;          /* 0 .. TILE_W-1 */
    int ty = threadIdx.y;          /* 0 .. TILE_H-1 */

    int col = blockIdx.x * TILE_W + tx;   /* global column */
    int row = blockIdx.y * TILE_H + ty;   /* global row    */

    /* ---- Load interior of tile ---- */
    int val = 0;
    if (row < M && col < N)
        val = in[row * N + col];
    tile[ty + 1][tx + 1] = val;

    /* ---- Load halo: left column ---- */
    if (tx == 0) {
        int c = col - 1;
        tile[ty + 1][0] = (c >= 0 && row < M) ? in[row * N + c] : 0;
    }
    /* ---- Load halo: right column ---- */
    if (tx == TILE_W - 1) {
        int c = col + 1;
        tile[ty + 1][TILE_W + 1] = (c < N && row < M) ? in[row * N + c] : 0;
    }
    /* ---- Load halo: top row ---- */
    if (ty == 0) {
        int r = row - 1;
        tile[0][tx + 1] = (r >= 0 && col < N) ? in[r * N + col] : 0;
    }
    /* ---- Load halo: bottom row ---- */
    if (ty == TILE_H - 1) {
        int r = row + 1;
        tile[TILE_H + 1][tx + 1] = (r < M && col < N) ? in[r * N + col] : 0;
    }
    /* ---- Load four corners ---- */
    if (tx == 0 && ty == 0) {
        int r = row - 1, c = col - 1;
        tile[0][0] = (r >= 0 && c >= 0) ? in[r * N + c] : 0;
    }
    if (tx == TILE_W - 1 && ty == 0) {
        int r = row - 1, c = col + 1;
        tile[0][TILE_W + 1] = (r >= 0 && c < N) ? in[r * N + c] : 0;
    }
    if (tx == 0 && ty == TILE_H - 1) {
        int r = row + 1, c = col - 1;
        tile[TILE_H + 1][0] = (r < M && c >= 0) ? in[r * N + c] : 0;
    }
    if (tx == TILE_W - 1 && ty == TILE_H - 1) {
        int r = row + 1, c = col + 1;
        tile[TILE_H + 1][TILE_W + 1] = (r < M && c < N) ? in[r * N + c] : 0;
    }

    __syncthreads();

    /* ---- Apply rules ---- */
    if (row >= M || col >= N) return;

    int alive = tile[ty + 1][tx + 1];

    int neighbors =
        tile[ty    ][tx    ] +
        tile[ty    ][tx + 1] +
        tile[ty    ][tx + 2] +
        tile[ty + 1][tx    ] +
        tile[ty + 1][tx + 2] +
        tile[ty + 2][tx    ] +
        tile[ty + 2][tx + 1] +
        tile[ty + 2][tx + 2];

    int next;
    if (alive) {
        /* Rule 1: loneliness */
        if (neighbors <= 1)       next = 0;
        /* Rule 2: overpopulation */
        else if (neighbors >= 4)  next = 0;
        /* Rule 4: unchanged */
        else                      next = 1;
    } else {
        /* Rule 3: birth */
        if (neighbors == 2 || neighbors == 3) next = 1;
        /* Rule 4: unchanged */
        else                                  next = 0;
    }

    out[row * N + col] = next;
}

/* ================================================================
 * Host helpers
 * ================================================================ */
static void printGrid(const int *grid, int M, int N)
{
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            printf("%d", grid[i * N + j]);
            if (j < N - 1) printf(" ");
        }
        printf("\n");
    }
}

static void initRandom(int *grid, int M, int N)
{
    for (int i = 0; i < M * N; i++)
        grid[i] = rand() % 2;
}

int main(int argc, char *argv[])
{
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <M> <N> <K> [-d]\n", argv[0]);
        return EXIT_FAILURE;
    }

    int M     = atoi(argv[1]);
    int N     = atoi(argv[2]);
    int K     = atoi(argv[3]);
    int debug = (argc >= 5 && strcmp(argv[4], "-d") == 0);

    if (M <= 0 || N <= 0 || K <= 0) {
        fprintf(stderr, "M, N, K must all be positive integers.\n");
        return EXIT_FAILURE;
    }

    size_t bytes = (size_t)M * N * sizeof(int);

    /* ---- Allocate host grid ---- */
    int *h_grid = (int *)malloc(bytes);
    int *h_out  = (int *)malloc(bytes);
    if (!h_grid || !h_out) { perror("malloc"); return EXIT_FAILURE; }

    srand((unsigned)time(NULL));
    initRandom(h_grid, M, N);

    /* ---- Print initial state ---- */
    printf("Start:\n------\n");
    printGrid(h_grid, M, N);

    /* ---- Allocate device buffers (double-buffer) ---- */
    int *d_a, *d_b;
    CUDA_CHECK(cudaMalloc(&d_a, bytes));
    CUDA_CHECK(cudaMalloc(&d_b, bytes));

    /* Master sends initial values to device (slaves) */
    CUDA_CHECK(cudaMemcpy(d_a, h_grid, bytes, cudaMemcpyHostToDevice));

    /* ---- Configure grid/block dimensions ---- */
    dim3 blockDim(TILE_W, TILE_H);
    dim3 gridDim((N + TILE_W - 1) / TILE_W,
                 (M + TILE_H - 1) / TILE_H);

    /* ---- Timing ---- */
    cudaEvent_t evStart, evStop;
    CUDA_CHECK(cudaEventCreate(&evStart));
    CUDA_CHECK(cudaEventCreate(&evStop));
    CUDA_CHECK(cudaEventRecord(evStart));

    /* ---- Run K iterations ---- */
    int *d_in  = d_a;
    int *d_out = d_b;

    for (int k = 0; k < K; k++) {
        stepKernel<<<gridDim, blockDim>>>(d_in, d_out, M, N);
        CUDA_CHECK(cudaGetLastError());

        if (debug) {
            /* In debug mode slaves send master their values each round */
            CUDA_CHECK(cudaMemcpy(h_out, d_out, bytes, cudaMemcpyDeviceToHost));
            printf("\nRound %d:\n", k);
            printf("-------\n");
            printGrid(h_out, M, N);
        }

        /* Swap buffers */
        int *tmp = d_in; d_in = d_out; d_out = tmp;
    }

    CUDA_CHECK(cudaEventRecord(evStop));
    CUDA_CHECK(cudaEventSynchronize(evStop));

    float ms = 0.f;
    CUDA_CHECK(cudaEventElapsedTime(&ms, evStart, evStop));

    /* Master receives final result from slaves */
    CUDA_CHECK(cudaMemcpy(h_out, d_in, bytes, cudaMemcpyDeviceToHost));

    if (!debug) {
        printf("\nFinal state after %d rounds:\n", K);
        printf("-----------------------------\n");
        printGrid(h_out, M, N);
    }

    printf("\nPerformance: M=%d N=%d K=%d  GPU time=%.3f ms\n", M, N, K, ms);

    /* ---- Cleanup ---- */
    CUDA_CHECK(cudaEventDestroy(evStart));
    CUDA_CHECK(cudaEventDestroy(evStop));
    CUDA_CHECK(cudaFree(d_a));
    CUDA_CHECK(cudaFree(d_b));
    free(h_grid);
    free(h_out);

    return 0;
}
