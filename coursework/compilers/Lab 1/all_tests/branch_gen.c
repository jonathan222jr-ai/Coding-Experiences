#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

int main() {
    int cse141a, cse141b;
    read(cse141a);
    read(cse141b);
    if (cse141a>=cse141b) {
        write(cse141a);
    }
    if (cse141b>cse141a) {
        write(cse141b);
    }
}

