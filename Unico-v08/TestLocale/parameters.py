"""Generation ID contract v2: profile[31:30], size[29:27], seed[26:0]."""
import math,secrets
STYLES={'auto':0,'tiny':1,'small':2,'medium':3,'large':4,'huge':5,'base':6}
PROFILES={'fire':1,'smoke':2,'both':3}
def hash32(x):
 x&=0xffffffff;x^=x>>16;x=(x*0x7feb352d)&0xffffffff;x^=x>>15;x=(x*0x846ca68b)&0xffffffff;x^=x>>16;return x
def unit(x):return (hash32(x)&65535)/65535
def new_id(profile,style,previous=0):
 while True:
  n=(PROFILES[profile]<<30)|(STYLES[style]<<27)|secrets.randbelow(1<<27)
  if n!=previous:return n
def values(n):
 profile=n>>30;cls=(n>>27)&7;seed=n&0x7ffffff
 if cls==0:
  u=unit(seed);cls=1 if u<.15 else 2 if u<.4 else 3 if u<.75 else 4 if u<.95 else 5
 if cls>6:cls=3
 lo=[1,.25,.55,.85,1.2,1.6,1];hi=[1,.45,.75,1.1,1.5,1.8,1]
 scale=lo[cls]+(hi[cls]-lo[cls])*unit(seed^0x13579)
 v={'FireScale':scale,'SmokeWidth':min(1.3,max(.55,math.sqrt(scale)*(.92+.12*unit(seed^0xabcd)))),'SmokeRise':.9+.2*unit(seed^0x319),'SmokeDensity':.85+.2*unit(seed^0x456)}
 if cls==6:v={k:1 for k in v}
 v.update(FireOn=int(profile in (1,3)),SmokeOn=int(profile in (2,3)))
 return v
