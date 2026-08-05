#include <iostream>
#include <vector>
#include <limits>

using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    
    long long V, E;
    cin >> V >> E;

    
    struct Edge {
        int u, v;
        long long w;
    };

    
    vector<Edge> edges;
    edges.reserve(E);

    
    for (long long i = 0; i < E; ++i) {
        int u, v;
        long long w;
        cin >> u >> v >> w;
        edges.push_back({u, v, w});
    }

    
    const long long INF = numeric_limits<long long>::max() / 4;

  
    vector<long long> dist(V, INF);

    
    int s = 0;
    dist[s] = 0;

   
    
    for (long long iter = 0; iter < V - 1; ++iter) {
        bool improved = false;

        for (const auto &e : edges) {
          
            if (dist[e.u] != INF && dist[e.u] + e.w < dist[e.v]) {
                dist[e.v] = dist[e.u] + e.w;
                improved = true;
            }
        }

        
        if (!improved) break;
    }

    
    bool neg_cycle = false;
    for (const auto &e : edges) {
        if (dist[e.u] != INF && dist[e.u] + e.w < dist[e.v]) {
            neg_cycle = true;
            break;
        }
    }

    
    if (neg_cycle) {
        
        cout << "FALSE\n";
        return 0;
    }

    
    cout << "TRUE\n";
    for (int i = 0; i < V; ++i) {
        if (dist[i] == INF)
            cout << "INFINITY\n";
        else
            cout << dist[i] << "\n";
    }

    return 0;
}
