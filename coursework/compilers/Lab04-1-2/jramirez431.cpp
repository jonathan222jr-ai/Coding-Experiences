#include <iostream>
#include <vector>
using namespace std;

// Stable counting sort used by Radix Sort
void countingSort(vector<vector<int>>& array, int column) {
    int n = array.size();
    vector<vector<int>> output(n, vector<int>(10));
    int count[4] = {0};

    // Count occurrences of each digit from (0–3) at position col
    for (int i = 0; i < n; i++)
        count[array[i][column]]++;

    // Compute prefix sums for stable sorting
    for (int i = 1; i < 4; i++)
        count[i] += count[i - 1];

    // Build output array (stable, so go backward)
    for (int i = n - 1; i >= 0; i--) {
        int digit = array[i][column];
        output[count[digit] - 1] = array[i];
        count[digit]--;
    }

    // Copy back to original array
    for (int i = 0; i < n; i++)
        array[i] = output[i];
}

// Perform radix sort from least significant digit to most
void radixSort(vector<vector<int>>& array) {
    for (int column = 9; column >= 0; column--) {
        countingSort(array, column);
    }
}

int main() {
    int n;
    cin >> n;

    vector<vector<int>> array(n, vector<int>(10));
    for (int i = 0; i < n; i++)
        for (int j = 0; j < 10; j++)
            cin >> array[i][j];

    radixSort(array);

    // Output in the required format
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < 10; j++) {
            cout << array[i][j] << ";";
        }
        cout << endl;
    }

    return 0;
}
