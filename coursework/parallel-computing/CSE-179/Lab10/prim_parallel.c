#include <stdio.h>
#include <limits.h>
#include <stdbool.h>
#include <omp.h>

#define MAX_VERTICES 100

int n;
int graph[MAX_VERTICES][MAX_VERTICES];

void primMST_parallel(int num_threads, int *out_parent, int *out_total_weight) {
    int parent[MAX_VERTICES];
    int key[MAX_VERTICES];
    bool inMST[MAX_VERTICES];

    for (int i = 0; i < n; i++) {
        key[i] = INT_MAX;
        inMST[i] = false;
    }

    key[0] = 0;
    parent[0] = -1;

    omp_set_num_threads(num_threads);

    for (int count = 0; count < n - 1; count++) {

        // --- Parallel min-key search ---
        int u = -1;
        int global_min = INT_MAX;

        #pragma omp parallel
        {
            int local_min = INT_MAX;
            int local_u = -1;

            #pragma omp for nowait
            for (int v = 0; v < n; v++) {
                if (!inMST[v] && key[v] < local_min) {
                    local_min = key[v];
                    local_u = v;
                }
            }

            #pragma omp critical
            {
                if (local_min < global_min) {
                    global_min = local_min;
                    u = local_u;
                }
            }
        }

        if (u == -1) break;
        inMST[u] = true;

        // --- Parallel key update ---
        #pragma omp parallel for
        for (int v = 0; v < n; v++) {
            if (graph[u][v] && !inMST[v] && graph[u][v] < key[v]) {
                key[v] = graph[u][v];
                parent[v] = u;
            }
        }
    }

    // Compute total weight
    int totalWeight = 0;
    for (int i = 1; i < n; i++)
        totalWeight += graph[i][parent[i]];

    if (out_parent)
        for (int i = 0; i < n; i++) out_parent[i] = parent[i];
    if (out_total_weight)
        *out_total_weight = totalWeight;
}

int main() {
    FILE *f = fopen("adjacency_matrix.txt", "r");
    if (!f) {
        printf("Error: adjacency_matrix.txt not found. Run generate_graph.py first.\n");
        return 1;
    }

    fscanf(f, "%d", &n);
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            fscanf(f, "%d", &graph[i][j]);
    fclose(f);

    printf("Graph loaded: %d vertices\n\n", n);

    int thread_counts[] = {1, 2, 4, 8};
    int num_tests = 4;

    int ref_parent[MAX_VERTICES];
    int ref_weight = 0;

    printf("%-10s %-15s %-12s %-10s\n", "Threads", "Time (s)", "MST Weight", "Speedup");
    printf("-------------------------------------------------------\n");

    double base_time = 0.0;

    for (int t = 0; t < num_tests; t++) {
        int threads = thread_counts[t];
        int parent[MAX_VERTICES];
        int total_weight = 0;

        double start = omp_get_wtime();
        primMST_parallel(threads, parent, &total_weight);
        double end = omp_get_wtime();
        double elapsed = end - start;

        if (t == 0) {
            base_time = elapsed;
            for (int i = 0; i < n; i++) ref_parent[i] = parent[i];
            ref_weight = total_weight;
        }

        // Verify correctness against 1-thread result
        bool correct = (total_weight == ref_weight);
        double speedup = base_time / elapsed;

        printf("%-10d %-15.6f %-12d %-10.2fx %s\n",
               threads, elapsed, total_weight, speedup,
               correct ? "" : "[MISMATCH!]");
    }

    printf("\nReference MST Weight (1 thread): %d\n", ref_weight);
    printf("\nMST Edges (1-thread run):\n");
    printf("Edge\t\tWeight\n");
    for (int i = 1; i < n; i++) {
        printf("%3d - %3d\t%d\n", ref_parent[i], i, graph[i][ref_parent[i]]);
    }

    return 0;
}
