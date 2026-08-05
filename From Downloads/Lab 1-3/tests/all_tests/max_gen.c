#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

int cse141max(int cse141a, int cse141b) {
    if (cse141a>cse141b) {
        return cse141a;
    }
    return cse141b;
}

int main() {
    int cse141a,cse141b;
    read(cse141a);
    read(cse141b);

    write(cse141max(cse141a,cse141b));
}

