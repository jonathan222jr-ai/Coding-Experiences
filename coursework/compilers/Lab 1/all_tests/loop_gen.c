#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

int main() {
    int cse141a, cse141sum;
    read(cse141a);
    cse141sum = 0;
    while (cse141a>0) {
        cse141sum = cse141sum + cse141a;
        cse141a = cse141a - 1;
    }
    write(cse141sum);
}

