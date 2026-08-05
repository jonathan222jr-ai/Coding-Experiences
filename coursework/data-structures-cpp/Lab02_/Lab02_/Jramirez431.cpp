//
//  main.cpp
//  Lab02_
//
//  Created by Jonathan Ramirez on 9/21/25.
//
#include <vector>      // Include the vector container (dynamic array)
#include <iostream>    // Include input/output library (cin, cout)
using namespace std;   // Avoid writing std:: prefix everywhere

// Function to merge two sorted halves of the array
void merge(vector<int>& Array, int left, int middle, int right){
    int n1 = middle - left + 1;   // Size of the left subarray
    int n2 = right - middle;      // Size of the right subarray

    vector<int> L(n1), R(n2);    // Temporary arrays for left and right halves
    
    // Copy data into left subarray
    for (int i = 0; i < n1; ++i)
        L[i] = Array[left + i];
    
    // Copy data into right subarray
    for (int j = 0; j < n2; ++j)
        R[j] = Array[middle + 1 + j];

    int i = 0, j = 0, k = left;   // i = index for L, j = index for R, k = index for Array

    // Merge elements from L and R back into Array
    while (i < n1 && j < n2){
        if (L[i] <= R[j])
            Array[k++] = L[i++];  // Take element from L if smaller
        else
            Array[k++] = R[j++];  // Take element from R if smaller
    }

    // Copy any remaining elements of L
    while (i < n1)
        Array[k++] = L[i++];

    // Copy any remaining elements of R
    while (j < n2)
        Array[k++] = R[j++];
}

void mergeSort(vector<int>& Array, int Left, int Right){
    if (Left < Right){   // Code runs if more than 1 element is in the array
        int Middle = Left + (Right - Left) / 2;   // Find the middle index

        mergeSort(Array, Left, Middle);       // Recursively sort left half
        mergeSort(Array, Middle + 1, Right);  // Recursively sort right half

        merge(Array, Left, Middle, Right);    // Merge the two halves
    }
}

int main() {
    int User_input;
    if (!(cin >> User_input))   // Read number of elements, exit if invalid input
        return 0;
    
    vector<int> Array(User_input);   // Create vector of given size
    
    // Read elements into Array
    for (int i = 0; i < User_input; ++i)
        cin >> Array[i];

    // Perform merge sort on the entire array
    mergeSort(Array, 0, User_input - 1);

    // Print sorted array with semicolons
    for (int i = 0; i < User_input; ++i) {
        cout << Array[i] << ";";
    }

    return 0;   // End program
}
