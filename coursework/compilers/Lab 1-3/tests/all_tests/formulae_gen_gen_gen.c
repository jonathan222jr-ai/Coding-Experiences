#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141cse141cse141getinput(void)
{
    int cse141cse141cse141a;
    cse141cse141cse141a = 0;
    while (0 >= cse141cse141cse141a)
    {
	read(cse141cse141cse141a);
	if (0 > cse141cse141cse141a)
	{
	    print("I need a positive number: ");
	}
    }

    return cse141cse141cse141a;
}

int main() 
{
    int cse141cse141cse141coneradius, cse141cse141cse141coneheight;
    int cse141cse141cse141circleradius;
    int cse141cse141cse141trianglebase, cse141cse141cse141triangleheight;
    int cse141cse141cse141sphereradius;

    int cse141cse141cse141cone, cse141cse141cse141circle, cse141cse141cse141triangle, cse141cse141cse141sphere;
    int cse141cse141cse141pi;
    cse141cse141cse141pi = 3141;

    print("Give me a radius for the base of a cone: ");
    cse141cse141cse141coneradius = cse141cse141cse141getinput();
    print("Give me a height for a cone: ");
    cse141cse141cse141coneheight = cse141cse141cse141getinput();
    print("Give me a radius for a circle: ");
    cse141cse141cse141circleradius = cse141cse141cse141getinput();
    print("Give me a length for the base of a triangle: ");
    cse141cse141cse141trianglebase = cse141cse141cse141getinput();
    print("Give me a height for a triangle: ");
    cse141cse141cse141triangleheight = cse141cse141cse141getinput();
    print("Give me a radius for a sphere: ");
    cse141cse141cse141sphereradius = cse141cse141cse141getinput();

    cse141cse141cse141cone = (cse141cse141cse141pi*cse141cse141cse141coneradius*cse141cse141cse141coneradius*cse141cse141cse141coneheight + 500) / 3000;
    cse141cse141cse141circle = (cse141cse141cse141pi*cse141cse141cse141circleradius*cse141cse141cse141circleradius + 500) / 1000;
    cse141cse141cse141triangle = (cse141cse141cse141trianglebase*cse141cse141cse141triangleheight) / 2;
    cse141cse141cse141sphere = (4*cse141cse141cse141pi*cse141cse141cse141sphereradius*cse141cse141cse141sphereradius*cse141cse141cse141sphereradius+500) / 3000;

    print("The volume of the cone is: ");
    write(cse141cse141cse141cone);
    print("The area of the circle is: ");
    write(cse141cse141cse141circle);
    print("The area of the triangle is: ");
    write(cse141cse141cse141triangle);
    print("The volume of the sphere is: ");
    write(cse141cse141cse141sphere);
}
