//
//  main.cpp
//  Lab10
//
//  Created by Jonathan Ramirez on 12/8/25.
//
#include <iostream>
#include <vector>
#include <string>
#include <limits>

using namespace std;


string buildOptimal(int i, int j, const vector<vector<int>>& s) {
    if (i == j) {
        return "A" + to_string(i);
    }
    return "(" + buildOptimal(i, s[i][j], s) +
           buildOptimal(s[i][j] + 1, j, s) + ")";
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    while (cin >> n) {
        vector<int> p(n + 1);
        for (int i = 0; i <= n; ++i) {
            cin >> p[i];
        }

        
        vector<vector<long long>> m(n, vector<long long>(n, 0));
        vector<vector<int>> s(n, vector<int>(n, 0));

        
        for (int l = 2; l <= n; ++l) {
            for (int i = 0; i <= n - l; ++i) {
                int j = i + l - 1;
                m[i][j] = numeric_limits<long long>::max();

                for (int k = i; k < j; ++k) {
                    long long cost = m[i][k] + m[k+1][j] +
                                     (long long)p[i] * p[k+1] * p[j+1];

                    if (cost < m[i][j]) {
                        m[i][j] = cost;
                        s[i][j] = k;
                    }
                }
            }
        }

        
        cout << m[0][n-1] << "\n";
        cout << buildOptimal(0, n-1, s) << "\n";
    }

    return 0;
}
