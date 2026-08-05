#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

int cse141cse141cse141max(int cse141cse141cse141a, int cse141cse141cse141b) {
    if (cse141cse141cse141a>cse141cse141cse141b) {
        return cse141cse141cse141a;
    }
    return cse141cse141cse141b;
}

int main() {
    int cse141cse141cse141a,cse141cse141cse141b;
    read(cse141cse141cse141a);
    read(cse141cse141cse141b);

    write(cse141cse141cse141max(cse141cse141cse141a,cse141cse141cse141b));
}

