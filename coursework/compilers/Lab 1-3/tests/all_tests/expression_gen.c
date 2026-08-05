#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

int main() {
    int cse141a, cse141sum;
    read(cse141a);
    cse141sum = (cse141a+1) *cse141a / 2;
    write(cse141sum);
}
