#include <iostream>
#include <vector>
#include <stack>
#include <algorithm>
using namespace std;

void dfs1(int v, vector<vector<int>>& adj, vector<bool>& visited, stack<int>& st) {
    visited[v] = true;
    for (int u : adj[v]) {
        if (!visited[u])
            dfs1(u, adj, visited, st);
    }
    st.push(v);
}


void dfs2(int v, vector<vector<int>>& adjT, vector<bool>& visited, vector<int>& component, int root) {
    visited[v] = true;
    component[v] = root;
    for (int u : adjT[v]) {
        if (!visited[u])
            dfs2(u, adjT, visited, component, root);
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int V, E;
    cin >> V >> E;

    vector<vector<int>> adj(V), adjT(V);

    for (int i = 0; i < E; i++) {
        int u, v;
        cin >> u >> v;
        adj[u].push_back(v);
        adjT[v].push_back(u);
    }

    vector<bool> visited(V, false);
    stack<int> st;

    
    for (int i = 0; i < V; i++) {
        if (!visited[i])
            dfs1(i, adj, visited, st);
    }

    
    fill(visited.begin(), visited.end(), false);
    vector<int> component(V, -1);

    while (!st.empty()) {
        int v = st.top();
        st.pop();
        if (!visited[v]) {
            
            vector<int> nodes;
            dfs2(v, adjT, visited, component, v);
        }
    }

    
    vector<int> sccMin(V, -1);
    for (int i = 0; i < V; i++) {
        if (sccMin[component[i]] == -1 || i < sccMin[component[i]])
            sccMin[component[i]] = i;
    }

    
    for (int i = 0; i < V; i++) {
        cout << sccMin[component[i]] << "\n";
    }

    return 0;
}

