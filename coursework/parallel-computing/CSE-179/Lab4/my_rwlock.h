#ifndef MY_RWLOCK_H
#define MY_RWLOCK_H

#include <pthread.h>

typedef struct {
    pthread_mutex_t mutex;
    pthread_cond_t  readers;
    pthread_cond_t  writers;
    int active_readers;
    int active_writers;
    int waiting_writers;
} my_rwlock_t;

int my_rwlock_init(my_rwlock_t *rw);
int my_rwlock_destroy(my_rwlock_t *rw);

int my_rwlock_rdlock(my_rwlock_t *rw);
int my_rwlock_wrlock(my_rwlock_t *rw);
int my_rwlock_unlock(my_rwlock_t *rw);

#endif