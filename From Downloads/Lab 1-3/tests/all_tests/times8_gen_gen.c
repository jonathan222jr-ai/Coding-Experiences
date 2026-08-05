#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)

int cse141cse141add(int cse141cse141a, int cse141cse141b) {
  return cse141cse141a+cse141cse141b;
}

int cse141cse141times_eight(int cse141cse141a) {
  return cse141cse141add(cse141cse141add(cse141cse141add(cse141cse141a,cse141cse141a),cse141cse141add(cse141cse141a,cse141cse141a)), cse141cse141add(cse141cse141add(cse141cse141a,cse141cse141a),cse141cse141add(cse141cse141a,cse141cse141a)));
}

int main() {
    int cse141cse141a, cse141cse141b;
    read(cse141cse141a);
    write(cse141cse141times_eight(cse141cse141a));
}
