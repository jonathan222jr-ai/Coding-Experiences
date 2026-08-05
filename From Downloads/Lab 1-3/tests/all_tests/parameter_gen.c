#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

void cse141foo(int cse141m,int cse141n) {
    cse141m = cse141m + cse141n;
    cse141n = cse141n + cse141m;
}

int main() {
    int cse141a;
    read(cse141a);
    cse141foo(cse141a,cse141a);
    write(cse141a);
}


