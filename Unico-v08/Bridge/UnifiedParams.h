#pragma once
#include <stdint.h>
#include <cmath>
struct UnifiedValues {float fireScale,smokeWidth,smokeRise,smokeDensity,fireOn,smokeOn;};
static uint32_t hash08(uint32_t x){x^=x>>16;x*=0x7feb352du;x^=x>>15;x*=0x846ca68bu;x^=x>>16;return x;}
static float unit08(uint32_t x){return float(hash08(x)&0xffffu)/65535.f;}
static UnifiedValues unifiedValues(uint32_t id){
 const unsigned profile=id>>30,style=(id>>27)&7u;const uint32_t seed=id&0x7ffffffu;
 unsigned cls=style;
 if(cls==0){float u=unit08(seed);cls=u<.15f?1:u<.4f?2:u<.75f?3:u<.95f?4:5;}
 if(cls>6)cls=3;
 const float lo[7]={1,.25f,.55f,.85f,1.2f,1.6f,1},hi[7]={1,.45f,.75f,1.1f,1.5f,1.8f,1};
 float scale=lo[cls]+(hi[cls]-lo[cls])*unit08(seed^0x13579u);
 UnifiedValues v{};v.fireScale=scale;
 v.smokeWidth=std::fmin(1.3f,std::fmax(.55f,std::sqrt(scale)*(.92f+.12f*unit08(seed^0xabcdu))));
 v.smokeRise=.9f+.2f*unit08(seed^0x319u);v.smokeDensity=.85f+.2f*unit08(seed^0x456u);
 if(cls==6){v.fireScale=v.smokeWidth=v.smokeRise=v.smokeDensity=1;}
 v.fireOn=(profile==1||profile==3)?1.f:0.f;v.smokeOn=(profile==2||profile==3)?1.f:0.f;
 return v;
}
