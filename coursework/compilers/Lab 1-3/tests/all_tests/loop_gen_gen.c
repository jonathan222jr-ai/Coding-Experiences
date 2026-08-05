#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

int main() {
    int cse141cse141a, cse141cse141sum;
    read(cse141cse141a);
    cse141cse141sum = 0;
    while (cse141cse141a>0) {
        cse141cse141sum = cse141cse141sum + cse141cse141a;
        cse141cse141a = cse141cse141a - 1;
    }
    write(cse141cse141sum);
}

