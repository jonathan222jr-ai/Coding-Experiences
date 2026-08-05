/*
**  PROGRAM: A simple serial producer/consumer program
**
**  One function generates (i.e. produces) an array of random values.  
**  A second functions consumes that array and sums it.
**
**  HISTORY: Written by Tim Mattson, April 2007.
*/
#include "omp.h"
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>

#define N        10000

/* Some random number constants from numerical recipies */
#define SEED       2531
#define RAND_MULT  1366
#define RAND_ADD   150889
#define RAND_MOD   714025
int randy = SEED;

/* function to fill an array with random numbers */
void fill_rand(int length, double *a)
{
   int i; 
   for (i=0;i<length;i++) {
     randy = (RAND_MULT * randy + RAND_ADD) % RAND_MOD;
     *(a+i) = ((double) randy)/((double) RAND_MOD);
   }   
}

/* function to sum the elements of an array */
double Sum_array(int length, double *a)
{
   int i;  double sum = 0.0;
   for (i=0;i<length;i++)  sum += *(a+i);  
   return sum; 
}
  
int main()
{
  double *A, sum = 0.0, runtime;
  int produced = 0, consumed = 0; /* counters for pairwise sync */

  A = (double *)malloc(N * sizeof(double));
  if (!A) {
    fprintf(stderr, "Failed to allocate memory\n");
    return 1;
  }

  runtime = omp_get_wtime();

  /*
   * Use two OpenMP sections: one producer and one consumer.
   * The producer generates one value at a time and waits until the
   * consumer has consumed it before producing the next one (pairwise
   * synchronization). Synchronization is implemented with simple
   * counters and explicit omp flush operations to ensure visibility.
   */
  #pragma omp parallel sections num_threads(2) shared(A, produced, consumed, sum)
  {
    #pragma omp section
    {
      int i;
      for (i = 0; i < N; ++i) {
        /* generate a single random value (same RNG as fill_rand) */
        randy = (RAND_MULT * randy + RAND_ADD) % RAND_MOD;
        A[i] = ((double) randy) / ((double) RAND_MOD);

        /* publish produced count */
        #pragma omp flush(A)
        produced = i + 1;
        #pragma omp flush(produced)

        /* wait until consumer has consumed this element */
        while (1) {
          #pragma omp flush(consumed)
          if (consumed >= i + 1) break;
        }
      }
    }

    #pragma omp section
    {
      int i;
      double local_sum = 0.0;
      for (i = 0; i < N; ++i) {
        /* wait until producer has produced element i */
        while (1) {
          #pragma omp flush(produced)
          if (produced >= i + 1) break;
        }

        local_sum += A[i];

        /* mark consumed and publish */
        consumed = i + 1;
        #pragma omp flush(consumed)
      }
      /* write back local sum to shared variable once finished */
      #pragma omp atomic
      sum += local_sum;
    }
  } /* end parallel sections */

  runtime = omp_get_wtime() - runtime;

  printf(" In %lf seconds, The sum is %lf \n", runtime, sum);

  free(A);
  return 0;
}
 
