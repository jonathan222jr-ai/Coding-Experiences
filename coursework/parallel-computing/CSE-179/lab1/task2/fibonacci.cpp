#include <iostream>
#include <sys/time.h>
#include <unistd.h>


using namespace std;


int main() {
   struct timeval start, end;


   int n, firstTerm = 1, secondTerm = 1, nextTerm;
   cout << "Enter number of terms: ";
   cin >> n;


   cout << "Fibonacci Series: " << firstTerm << " + " << secondTerm << " + ";


   gettimeofday(&start, NULL);


   for (int i = 1; i <= n - 2; ++i) {
       nextTerm = firstTerm + secondTerm;
       cout << nextTerm << " + ";
       firstTerm = secondTerm;
       secondTerm = nextTerm;
   }


   gettimeofday(&end, NULL);


   long seconds = end.tv_sec - start.tv_sec;
   long microseconds = end.tv_usec - start.tv_usec;
   double elapsed_time = seconds + microseconds;


   cout << "\nExecution time: " << elapsed_time << " seconds\n";


   return 0;
}

