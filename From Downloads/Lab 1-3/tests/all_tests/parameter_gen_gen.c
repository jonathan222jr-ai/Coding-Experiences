#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

void cse141cse141foo(int cse141cse141m,int cse141cse141n) {
    cse141cse141m = cse141cse141m + cse141cse141n;
    cse141cse141n = cse141cse141n + cse141cse141m;
}

int main() {
    int cse141cse141a;
    read(cse141cse141a);
    cse141cse141foo(cse141cse141a,cse141cse141a);
    write(cse141cse141a);
}


