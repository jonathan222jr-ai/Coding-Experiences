#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

#define SAMPLE_POINTS_PER_THREAD 10000

long long total_hits = 0;
pthread_mutex_t mutex;

typedef struct {
    int thread_id;
} thread_data_t;

void* compute_pi(void* arg) {
    thread_data_t* data = (thread_data_t*) arg;
    unsigned int seed = time(NULL) ^ data->thread_id;

    long long local_hits = 0;

    for (int i = 0; i < SAMPLE_POINTS_PER_THREAD; i++) {
        double x = (double) rand_r(&seed) / RAND_MAX;
        double y = (double) rand_r(&seed) / RAND_MAX;

        if (x*x + y*y <= 1.0) {
            local_hits++;
        }
    }

    // Critical section
    pthread_mutex_lock(&mutex);
    total_hits += local_hits;
    pthread_mutex_unlock(&mutex);

    pthread_exit(NULL);
}

int main(int argc, char* argv[]) {

    if (argc != 2) {
        printf("Usage: %s <number_of_threads>\n", argv[0]);
        return 1;
    }

    int num_threads = atoi(argv[1]);

    pthread_t threads[num_threads];
    thread_data_t thread_data[num_threads];

    pthread_mutex_init(&mutex, NULL);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < num_threads; i++) {
        thread_data[i].thread_id = i;
        pthread_create(&threads[i], NULL, compute_pi, &thread_data[i]);
    }

    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double time_spent = (end.tv_sec - start.tv_sec) +
                        (end.tv_nsec - start.tv_nsec) / 1e9;

    double pi = 4.0 * total_hits /
                (num_threads * SAMPLE_POINTS_PER_THREAD);

    printf("Threads: %d\n", num_threads);
    printf("Estimated PI = %.10f\n", pi);
    printf("Execution Time = %f seconds\n", time_spent);

    pthread_mutex_destroy(&mutex);

    return 0;
}