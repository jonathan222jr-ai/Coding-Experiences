//
//  jramirez431.cpp
//  Lab04-2
//
//  Created by Jonathan Ramirez on 10/5/25.
//
#include <iostream>
#include <vector>
#include <cstdlib>   // for rand() and srand()
#include <ctime>     // for time()
using namespace std;

// Partition function (Lomuto partition scheme)
int partition(vector<int>& arr, int low, int high) {
    int pivot = arr[high]; // pivot element
    int i = low - 1;       // smaller element index

    for (int j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(arr[i], arr[j]);
        }
    }
    swap(arr[i + 1], arr[high]);
    return i + 1;
}

// Randomized partition — chooses a random pivot and swaps it with the last element
int randomizedPartition(vector<int>& arr, int low, int high) {
    int randomIndex = low + rand() % (high - low + 1); // random pivot between low and high
    swap(arr[randomIndex], arr[high]); // move random pivot to the end
    return partition(arr, low, high);
}

// Randomized QuickSort
void randomizedQuickSort(vector<int>& arr, int low, int high) {
    if (low < high) {
        int pi = randomizedPartition(arr, low, high); // partition index

        // Recursively sort elements before and after partition
        randomizedQuickSort(arr, low, pi - 1);
        randomizedQuickSort(arr, pi + 1, high);
    }
}

int main() {
    srand(time(NULL)); // seed random number generator

    int n;
    cin >> n;
    vector<int> arr(n);
    for (int i = 0; i < n; i++) {
        cin >> arr[i];
    }

    randomizedQuickSort(arr, 0, n - 1);

    // Output in required format (no spaces, one line)
    for (int i = 0; i < n; i++) {
        cout << arr[i] << ";";
    }

    return 0;
}

