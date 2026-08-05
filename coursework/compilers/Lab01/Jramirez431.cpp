//
//  Jramirez431.cpp
//  Lab01
//
//  Created by Jonathan Ramirez on 9/16/25.
//

#include <iostream>
#include <vector> //Allow us to shrink and grow the array as needed
using namespace std; //Removes the need of 'std::' when writing code

int main()
    {
    int Array_size; // creates the variable size and labeling it as an integer variable.
    cin >> Array_size; //This allows us to input numbers and it will register as the varaible size.

    vector<int> arr(Array_size); //Here we use the vector function to create an array the size of the input. It's more efficient.

    for (int i = 0; i < Array_size; i++) { //Loop to input all elements into the vector
        cin >> arr[i];
    }

    //Insertion Array
    for (int k = 1; k < Array_size; k++) { //We start at k=1 so the code can begin comparing with the other inputs in the array
        int key = arr[k]; //Using the varible 'key' we create an array that we will input sorted inputs
        int j = k - 1; //This is the index of the input(element) before the key

        while (j >= 0 && arr[j] > key) { //While the element (input) is greater than the key
            arr[j + 1] = arr[j];         //Move the element one position to the right
            j--;                         //Move to the previous element
        }
        arr[j + 1] = key;                //Place the key in its sorted position

        for (int i = 0; i <= k; i++) { //Print all elements up to current index of the array
            cout << arr[i] << ";";     // Print each element followed by a semicolon as required by the lab assignment
        }
        cout << endl;  // Move to the next line
    }
    return 0; // End of program
}
