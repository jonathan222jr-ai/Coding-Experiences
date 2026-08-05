//
//  jramirez431.cpp
//  Lab03
//
//  Created by Jonathan Ramirez on 9/30/25.
//

//(Divide and Conquer)
#include <iostream>
#include <vector>
#include <climits>

using namespace std;

//Function to find maximum of three ints
int maxThree(int x, int y, int z){
    return max(max(x, y), z);
}

//Function to find maximum subarray that crosses the midpoint
int maxCross(vector<int>& arr, int left, int mid, int right){
    //include elements on the left of mid
    int sum = 0;
    int ls = INT_MIN;
    for (int i = mid; i >= left; i--){
        sum += arr[i];
        if (sum > ls)
            ls = sum;
    }
    //include elements on right of mid
    sum = 0;
    int rs = INT_MIN;
    for (int i = mid + 1; i <= right; i++){
        sum += arr[i];
        if (sum > rs)
            rs = sum;
    }
    //maximum sum is left + right combined
    return ls + rs;
}

//recurssieve function to find maximum subarray sum using divde and conq
int maxSub(vector<int>& arr, int left, int right){
    //if one element only
    if (left == right)
        return arr[left];

    int mid = (left + right) / 2;

    return maxThree(
        maxSub(arr, left, mid),
        maxSub(arr, mid + 1, right),
        maxCross(arr, left, mid, right)
    );
}

int main(){
    int n;
    cin >> n; //read the size of the array

    vector<int> arr(n);
    for (int i = 0; i < n; i++){
        cin >> arr[i]; //read each array element
    }

    //call the recursive function on the whole array
    int maxSum = maxSub(arr, 0, n - 1);

    //output the max ubarray sum
    cout << maxSum;

    return 0;
}
