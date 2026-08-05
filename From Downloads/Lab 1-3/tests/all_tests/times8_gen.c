#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

int cse141add(int cse141a, int cse141b) {
  return cse141a+cse141b;
}

int cse141times_eight(int cse141a) {
  return cse141add(cse141add(cse141add(cse141a,cse141a),cse141add(cse141a,cse141a)), cse141add(cse141add(cse141a,cse141a),cse141add(cse141a,cse141a)));
}

int main() {
    int cse141a, cse141b;
    read(cse141a);
    write(cse141times_eight(cse141a));
}
