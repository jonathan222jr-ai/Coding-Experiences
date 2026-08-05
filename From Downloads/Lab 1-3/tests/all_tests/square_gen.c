#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141square(int cse141x)
{
    int cse141x;
    cse141x = 10;

    return cse141x * cse141x;
}

int main(void)
{
    int cse141val;
    print("Give me a number: ");
    read(cse141val);

    print("Your number squared is: ");
    write(cse141square(cse141val));
}
