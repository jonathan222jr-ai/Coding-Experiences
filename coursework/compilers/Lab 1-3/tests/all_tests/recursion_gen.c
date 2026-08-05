#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

int cse141recursionsum(int cse141n) {
    if (cse141n==0) {
        return 0;
    }
    return cse141n + cse141recursionsum(cse141n-1);
}

int main() {
    int cse141a;
    read(cse141a);
    write(cse141recursionsum(cse141a));
}


