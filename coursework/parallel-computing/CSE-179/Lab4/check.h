#ifndef CHECK_H
#define CHECK_H

#include <stdio.h>
#include <stdlib.h>

static void compResults(char *string, int rc) {
    if (rc) {
        printf("Error on: %s rc=%d\n", string, rc);
        exit(EXIT_FAILURE);
    }
}

#endif