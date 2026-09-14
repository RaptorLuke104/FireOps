#include "../Bridge/UnifiedParams.h"
#include <cstdio>
int main(){for(uint32_t p=1;p<=3;++p)for(uint32_t c=0;c<=6;++c)for(uint32_t s=1;s<100000;s+=997){uint32_t id=(p<<30)|(c<<27)|s;auto v=unifiedValues(id);std::printf("%u %.8f %.8f %.8f %.8f %.0f %.0f\n",id,v.fireScale,v.smokeWidth,v.smokeRise,v.smokeDensity,v.fireOn,v.smokeOn);}return 0;}
