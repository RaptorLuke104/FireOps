"""Offline EGM96 15-minute GTX bilinear interpolation.
N = ellipsoid height minus geoid height, metres. h = H + N.
Not a terrain elevation database. This only converts a supplied geoid height.
"""
import hashlib
import math
import pathlib
import struct

class Geoid:
    SHA256='c02a6eb70a7a78efebe5adf3ade626eb75390e170bb8b3f36136a2c28f5326a0'
    def __init__(self,path=None):
        path=pathlib.Path(path) if path else pathlib.Path(__file__).resolve().parent/'data'/'egm96_15.gtx'
        self.data=path.read_bytes()
        if hashlib.sha256(self.data).hexdigest()!=self.SHA256:
            raise ValueError('Griglia EGM96 diversa da quella verificata o danneggiata: estrarre nuovamente tutto lo ZIP.')
        self.lat0,self.lon0,self.dlat,self.dlon,self.rows,self.cols=struct.unpack_from('>ddddii',self.data)
        if (self.lat0,self.lon0,self.dlat,self.dlon,self.rows,self.cols)!=(-90.,-180.,.25,.25,721,1440):
            raise ValueError('Header della griglia inatteso')
        if len(self.data)!=40+self.rows*self.cols*4: raise ValueError('Dimensioni griglia errate')
    def cell(self,row,col):
        return struct.unpack_from('>f',self.data,40+4*(row*self.cols+col))[0]
    def undulation(self,lat,lon):
        if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90:
            raise ValueError('Coordinate geografiche non valide')
        lon=(lon+180)%360-180
        x=(lon-self.lon0)/self.dlon;y=(lat-self.lat0)/self.dlat
        row=min(int(math.floor(y)),self.rows-2); col=int(math.floor(x))%self.cols
        fx=x-math.floor(x);fy=y-row;right=(col+1)%self.cols
        a=self.cell(row,col)*(1-fx)+self.cell(row,right)*fx
        b=self.cell(row+1,col)*(1-fx)+self.cell(row+1,right)*fx
        return a*(1-fy)+b*fy
