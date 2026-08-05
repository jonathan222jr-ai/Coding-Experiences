#define _MULTI_THREADED
#include <pthread.h>
#include <stdio.h>
#include <unistd.h>
#include "check.h"
#include "my_rwlock.h"

my_rwlock_t rwlock;

void *rdlockThread(void *arg)
{
  int rc;

  printf("Entered thread, getting read lock\n");
  rc = my_rwlock_rdlock(&rwlock);
  compResults("my_rwlock_rdlock()\n", rc);
  printf("got the rwlock read lock\n");

  sleep(5);

  printf("unlock the read lock\n");
  rc = my_rwlock_unlock(&rwlock);
  compResults("my_rwlock_unlock()\n", rc);
  printf("Secondary thread unlocked\n");
  return NULL;
}

void *wrlockThread(void *arg)
{
  int rc;

  printf("Entered thread, getting write lock\n");
  rc = my_rwlock_wrlock(&rwlock);
  compResults("my_rwlock_wrlock()\n", rc);

  printf("Got the rwlock write lock, now unlock\n");
  rc = my_rwlock_unlock(&rwlock);
  compResults("my_rwlock_unlock()\n", rc);
  printf("Secondary thread unlocked\n");
  return NULL;
}

int main(int argc, char **argv)
{
  int rc = 0;
  int n_readers = 1, n_writers = 1;
  pthread_t *readers = NULL;
  pthread_t *writers = NULL;
  int i;

  /* parse optional command-line arguments */
  if (argc > 1)
    n_readers = atoi(argv[1]);
  if (argc > 2)
    n_writers = atoi(argv[2]);

  if (n_readers < 0) n_readers = 0;
  if (n_writers < 0) n_writers = 0;

  printf("Enter test case - %s (readers=%d writers=%d)\n", argv[0],
         n_readers, n_writers);

  printf("Main, initialize the read write lock\n");
  rc = my_rwlock_init(&rwlock);
  compResults("my_rwlock_init()\n", rc);

  /* allocate thread arrays */
  if (n_readers > 0)
    readers = malloc(n_readers * sizeof(pthread_t));
  if (n_writers > 0)
    writers = malloc(n_writers * sizeof(pthread_t));

  /* create reader threads */
  for (i = 0; i < n_readers; ++i) {
    printf("Main, create reader thread %d\n", i + 1);
    rc = pthread_create(&readers[i], NULL, rdlockThread, NULL);
    compResults("pthread_create (reader)\n", rc);
  }

  /* create writer threads */
  for (i = 0; i < n_writers; ++i) {
    printf("Main, create writer thread %d\n", i + 1);
    rc = pthread_create(&writers[i], NULL, wrlockThread, NULL);
    compResults("pthread_create (writer)\n", rc);
  }

  /* wait for threads to finish */
  for (i = 0; i < n_readers; ++i)
    pthread_join(readers[i], NULL);
  for (i = 0; i < n_writers; ++i)
    pthread_join(writers[i], NULL);

  rc = my_rwlock_destroy(&rwlock);
  compResults("my_rwlock_destroy()\n", rc);

  printf("Main completed\n");

  free(readers);
  free(writers);
  return 0;
}