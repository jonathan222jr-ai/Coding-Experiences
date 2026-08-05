#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#define N 4096

// Function to verify correctness by comparing with serial prefix sum
int verify_prefix_sum(int *A, int n) {
    int *expected = malloc(n * sizeof(int));
    expected[0] = A[0];
    for (int i = 1; i < n; i++)
        expected[i] = expected[i-1] + A[i];
    
    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (A[i] != expected[i]) {
            correct = 0;
            break;
        }
    }
    free(expected);
    return correct;
}

int main(int argc, char* argv[]) {
    int n = N;
    int num_threads = 4;
    
    // Allow command line arguments to test different sizes and thread counts
    if (argc > 1) n = atoi(argv[1]);
    if (argc > 2) num_threads = atoi(argv[2]);
    
    int *A = malloc(n * sizeof(int));
    int *block_sum = malloc(num_threads * sizeof(int));
    int block_size = n / num_threads;

    // Initialize random data
    for (int i = 0; i < n; i++)
        A[i] = rand() % 100;
    
    printf("\n=== Parallel Prefix Sum ===\n");
    printf("Array size: %d, Threads: %d, Block size: %d\n", n, num_threads, block_size);

    double total_start = omp_get_wtime();

    // ============ Step 1: Parallel prefix within each block ============
    double step1_start = omp_get_wtime();

#pragma omp parallel num_threads(num_threads)
    {
        int tid = omp_get_thread_num();
        int start = tid * block_size;
        int end = start + block_size;

        for (int i = start + 1; i < end; i++)
            A[i] += A[i - 1];

        block_sum[tid] = A[end - 1];
    }

    double step1_end = omp_get_wtime();

    // ============ Step 2: Sequential prefix of block sums ============
    double step2_start = omp_get_wtime();

    for (int i = 1; i < num_threads; i++)
        block_sum[i] += block_sum[i - 1];

    double step2_end = omp_get_wtime();

    // ============ Step 3: Parallel propagate block offsets ============
    double step3_start = omp_get_wtime();

#pragma omp parallel num_threads(num_threads)
    {
        int tid = omp_get_thread_num();
        /* thread 0 has no work in this step; other threads apply offset */
        if (tid != 0) {
            int start = tid * block_size;
            int end = start + block_size;
            int offset = block_sum[tid - 1];

            for (int i = start; i < end; i++)
                A[i] += offset;
        }
    }

    double step3_end = omp_get_wtime();
    double total_end = omp_get_wtime();

    // ============ Verification & Results ============
    printf("\nTimings:\n");
    printf("  Step 1 (Parallel prefix in blocks): %.6f seconds\n", step1_end - step1_start);
    printf("  Step 2 (Sequential block prefix):   %.6f seconds\n", step2_end - step2_start);
    printf("  Step 3 (Parallel offset propagate): %.6f seconds\n", step3_end - step3_start);
    printf("  Total execution time:               %.6f seconds\n\n", total_end - total_start);

    // Verify correctness
    if (verify_prefix_sum(A, n)) {
        printf("✓ Correctness verification: PASSED\n");
    } else {
        printf("✗ Correctness verification: FAILED\n");
    }
    
    // Print first and last elements for manual verification
    printf("\nSample results:\n");
    printf("  A[0] = %d\n", A[0]);
    printf("  A[n/2] = %d\n", A[n/2]);
    printf("  A[n-1] = %d\n", A[n-1]);

    free(A);
    free(block_sum);
    return 0;
}
