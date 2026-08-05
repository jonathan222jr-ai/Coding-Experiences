#include <stdlib.h>
#include <stdio.h>
#include "omp.h"

#ifndef N
#define N 5
#endif
#ifndef FS
#define FS 38
#endif

struct node {
   int data;
   int fibdata;
   struct node* next;
};

int fib(int n) {
   int x, y;
   if (n < 2) {
      return (n);
   } else {
      x = fib(n - 1);
      y = fib(n - 2);
	  return (x + y);
   }
}

void processwork(struct node* p) 
{
   int n;
   n = p->data;
   p->fibdata = fib(n);
}

struct node* init_list(struct node* p) {
    int i;
    struct node* head = NULL;
    struct node* temp = NULL;
    
    head = malloc(sizeof(struct node));
    p = head;
    p->data = FS;
    p->fibdata = 0;
    for (i=0; i< N; i++) {
       temp  = malloc(sizeof(struct node));
       p->next = temp;
       p = temp;
       p->data = FS + i + 1;
       p->fibdata = i+1;
    }
    p->next = NULL;
    return head;
}

/* helper: count nodes and build array of pointers */
int list_to_array(struct node* head, struct node*** out_array) {
   int count = 0;
   struct node* p = head;
   while (p) { ++count; p = p->next; }
   struct node** arr = malloc(count * sizeof(struct node*));
   p = head; int i = 0;
   while (p) { arr[i++] = p; p = p->next; }
   *out_array = arr;
   return count;
}

void free_list(struct node* head) {
   struct node* p = head;
   struct node* tmp;
   while (p) {
      tmp = p->next;
      free(p);
      p = tmp;
   }
}

/* clone linked list structure (data values copied, fibdata zeroed) */
struct node* clone_from(struct node* src) {
   if (!src) return NULL;
   struct node* h = malloc(sizeof(struct node));
   struct node* cur = h;
   struct node* s = src;
   cur->data = s->data;
   cur->fibdata = 0;
   s = s->next;
   while (s) {
      struct node* n = malloc(sizeof(struct node));
      cur->next = n;
      cur = n;
      cur->data = s->data;
      cur->fibdata = 0;
      s = s->next;
   }
   cur->next = NULL;
   return h;
}

double run_serial(struct node* head) {
   double t0 = omp_get_wtime();
   struct node* p = head;
   while (p) {
      processwork(p);
      p = p->next;
   }
   return omp_get_wtime() - t0;
}

double run_tasks(struct node* head, int num_threads) {
   double t0 = omp_get_wtime();
#pragma omp parallel num_threads(num_threads)
   {
#pragma omp single nowait
      {
         struct node* p = head;
         for (; p != NULL; p = p->next) {
#pragma omp task firstprivate(p)
            processwork(p);
         }
#pragma omp taskwait
      }
   }
   return omp_get_wtime() - t0;
}

double run_for(struct node* head, int num_threads) {
   struct node** arr;
   int count = list_to_array(head, &arr);
   double t0 = omp_get_wtime();
#pragma omp parallel for num_threads(num_threads) schedule(dynamic)
   for (int i = 0; i < count; ++i) {
      processwork(arr[i]);
   }
   double t = omp_get_wtime() - t0;
   free(arr);
   return t;
}

int main(int argc, char *argv[]) {
   int num_threads = 4;
   int n_nodes = N;
   int fs_val = FS;

   /* Simple CLI: linked [threads] [N] [FS]
      If no args, defaults used. */
   if (argc > 1) num_threads = atoi(argv[1]);
   if (argc > 2) n_nodes = atoi(argv[2]);
   if (argc > 3) fs_val = atoi(argv[3]);

   printf("Process linked list (N=%d nodes, FS=%d)\n", n_nodes, fs_val);
   printf("Using up to %d threads\n", num_threads);

   /* rebuild macros for this run: create list of size n_nodes */
   /* init_list uses the macro N and FS; to avoid changing macros, write a small init here */
   struct node* head = NULL;
   struct node* p = NULL;
   struct node* temp = NULL;

   head = malloc(sizeof(struct node));
   p = head;
   p->data = fs_val;
   p->fibdata = 0;
   for (int i = 0; i < n_nodes; ++i) {
      temp = malloc(sizeof(struct node));
      p->next = temp;
      p = temp;
      p->data = fs_val + i + 1;
      p->fibdata = 0;
   }
   p->next = NULL;

   /* We'll run three variants; recreate list before each run since nodes are modified */
   struct node* head_serial = NULL;
   struct node* head_tasks = NULL;
   struct node* head_for = NULL;

   /* clone helper is defined above */

   head_serial = clone_from(head);
   head_tasks = clone_from(head);
   head_for = clone_from(head);

   double t_serial = run_serial(head_serial);
   double t_tasks = run_tasks(head_tasks, num_threads);
   double t_for = run_for(head_for, num_threads);

   printf("Serial time: %f seconds\n", t_serial);
   printf("Tasks time (threads=%d): %f seconds\n", num_threads, t_tasks);
   printf("For time (threads=%d): %f seconds\n", num_threads, t_for);

   /* Optionally print results for verification from one of the lists */
   // printf("Results (data : fibdata) from serial run:\n");
   // while (q) { printf("%d : %d\n", q->data, q->fibdata); q = q->next; }

   free_list(head_serial);
   free_list(head_tasks);
   free_list(head_for);
   free_list(head);

   return 0;
}

