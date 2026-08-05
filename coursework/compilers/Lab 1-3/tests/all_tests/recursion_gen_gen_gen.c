#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

int cse141cse141cse141recursionsum(int cse141cse141cse141n) {
    if (cse141cse141cse141n==0) {
        return 0;
    }
    return cse141cse141cse141n + cse141cse141cse141recursionsum(cse141cse141cse141n-1);
}

int main() {
    int cse141cse141cse141a;
    read(cse141cse141cse141a);
    write(cse141cse141cse141recursionsum(cse141cse141cse141a));
}


