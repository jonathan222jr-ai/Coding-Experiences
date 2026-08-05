#include "my_rwlock.h"

int my_rwlock_init(my_rwlock_t *rw)
{
    pthread_mutex_init(&rw->mutex, NULL);
    pthread_cond_init(&rw->readers, NULL);
    pthread_cond_init(&rw->writers, NULL);

    rw->active_readers = 0;
    rw->active_writers = 0;
    rw->waiting_writers = 0;

    return 0;
}

int my_rwlock_rdlock(my_rwlock_t *rw)
{
    pthread_mutex_lock(&rw->mutex);

    while (rw->active_writers > 0 || rw->waiting_writers > 0) {
        pthread_cond_wait(&rw->readers, &rw->mutex);
    }

    rw->active_readers++;

    pthread_mutex_unlock(&rw->mutex);
    return 0;
}

int my_rwlock_wrlock(my_rwlock_t *rw)
{
    pthread_mutex_lock(&rw->mutex);

    rw->waiting_writers++;

    while (rw->active_readers > 0 || rw->active_writers > 0) {
        pthread_cond_wait(&rw->writers, &rw->mutex);
    }

    rw->waiting_writers--;
    rw->active_writers++;

    pthread_mutex_unlock(&rw->mutex);
    return 0;
}

int my_rwlock_unlock(my_rwlock_t *rw)
{
    pthread_mutex_lock(&rw->mutex);

    if (rw->active_writers > 0) {
        rw->active_writers--;
    } else {
        rw->active_readers--;
    }

    if (rw->waiting_writers > 0) {
        if (rw->active_readers == 0 && rw->active_writers == 0) {
            pthread_cond_signal(&rw->writers);
        }
    } else {
        pthread_cond_broadcast(&rw->readers);
    }

    pthread_mutex_unlock(&rw->mutex);
    return 0;
}

int my_rwlock_destroy(my_rwlock_t *rw)
{
    pthread_mutex_destroy(&rw->mutex);
    pthread_cond_destroy(&rw->readers);
    pthread_cond_destroy(&rw->writers);
    return 0;
}