#include <stdio.h>
#include <limits.h>
#include <stdbool.h>
#include <time.h>

#define MAX_VERTICES 100

int n;
int graph[MAX_VERTICES][MAX_VERTICES];

// Find vertex with minimum key value not yet in MST
int minKey(int key[], bool inMST[]) {
    int min = INT_MAX, min_index = -1;
    for (int v = 0; v < n; v++) {
        if (!inMST[v] && key[v] < min) {
            min = key[v];
            min_index = v;
        }
    }
    return min_index;
}

void primMST() {
    int parent[MAX_VERTICES];
    int key[MAX_VERTICES];
    bool inMST[MAX_VERTICES];

    for (int i = 0; i < n; i++) {
        key[i] = INT_MAX;
        inMST[i] = false;
    }

    // Start from vertex 0
    key[0] = 0;
    parent[0] = -1;

    for (int count = 0; count < n - 1; count++) {
        // Pick the minimum key vertex not yet in MST
        int u = minKey(key, inMST);
        inMST[u] = true;

        // Update key values of adjacent vertices
        for (int v = 0; v < n; v++) {
            if (graph[u][v] && !inMST[v] && graph[u][v] < key[v]) {
                parent[v] = u;
                key[v] = graph[u][v];
            }
        }
    }

    // Print MST edges and total weight
    int totalWeight = 0;
    printf("MST Edges (Serial Prim's):\n");
    printf("Edge\t\tWeight\n");
    for (int i = 1; i < n; i++) {
        printf("%3d - %3d\t%d\n", parent[i], i, graph[i][parent[i]]);
        totalWeight += graph[i][parent[i]];
    }
    printf("Total MST Weight: %d\n", totalWeight);
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

    clock_t start = clock();
    primMST();
    clock_t end = clock();

    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;
    printf("\nSerial execution time: %.6f seconds\n", elapsed);

    return 0;
}
