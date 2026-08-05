#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141getinput(void)
{
    int cse141a;
    cse141a = 0;
    while (0 >= cse141a)
    {
	read(cse141a);
	if (0 > cse141a)
	{
	    print("I need a positive number: ");
	}
    }

    return cse141a;
}

int main() 
{
    int cse141coneradius, cse141coneheight;
    int cse141circleradius;
    int cse141trianglebase, cse141triangleheight;
    int cse141sphereradius;

    int cse141cone, cse141circle, cse141triangle, cse141sphere;
    int cse141pi;
    cse141pi = 3141;

    print("Give me a radius for the base of a cone: ");
    cse141coneradius = cse141getinput();
    print("Give me a height for a cone: ");
    cse141coneheight = cse141getinput();
    print("Give me a radius for a circle: ");
    cse141circleradius = cse141getinput();
    print("Give me a length for the base of a triangle: ");
    cse141trianglebase = cse141getinput();
    print("Give me a height for a triangle: ");
    cse141triangleheight = cse141getinput();
    print("Give me a radius for a sphere: ");
    cse141sphereradius = cse141getinput();

    cse141cone = (cse141pi*cse141coneradius*cse141coneradius*cse141coneheight + 500) / 3000;
    cse141circle = (cse141pi*cse141circleradius*cse141circleradius + 500) / 1000;
    cse141triangle = (cse141trianglebase*cse141triangleheight) / 2;
    cse141sphere = (4*cse141pi*cse141sphereradius*cse141sphereradius*cse141sphereradius+500) / 3000;

    print("The volume of the cone is: ");
    write(cse141cone);
    print("The area of the circle is: ");
    write(cse141circle);
    print("The area of the triangle is: ");
    write(cse141triangle);
    print("The volume of the sphere is: ");
    write(cse141sphere);
}
