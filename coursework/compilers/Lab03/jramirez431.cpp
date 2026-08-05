//
//  jramirez431.cpp
//  Lab03
//
//  Created by Jonathan Ramirez on 9/30/25.
//


#include <iostream>
#include <vector>
#include <climits>

using namespace std;


int maxThree(int x, int y, int z){
    return max(max(x, y), z);
}


int maxCross(vector<int>& arr, int left, int mid, int right){
    int sum = 0;
    int ls = INT_MIN;
    for (int i = mid; i >= left; i--){
        sum += arr[i];
        if (sum > ls)
            ls = sum;
    }
    
    sum = 0;
    int rs = INT_MIN;
    for (int i = mid + 1; i <= right; i++){
        sum += arr[i];
        if (sum > rs)
            rs = sum;
    }
    
    return ls + rs;
}


int maxSub(vector<int>& arr, int left, int right){
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
    cin >> n;

    vector<int> arr(n);
    for (int i = 0; i < n; i++){
        cin >> arr[i];
    }

    
    int maxSum = maxSub(arr, 0, n - 1);

    
    cout << maxSum;

    return 0;
}
