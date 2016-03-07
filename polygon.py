#! /usr/bin/env python
'''
Generates Inkscape SVG file containing cabinet components needed to 
laser cut a drawer cabinet taking kerf and clearance into account

Copyright (C) 2016 Thore Mehr thore.mehr@gmail.com
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = "0.8" ### please report bugs, suggestions etc to bugs@twot.eu ###

import sys,inkex,simplestyle,gettext,math
_ = gettext.gettext

def textElement(text,positon,self):
  t = inkex.etree.Element(inkex.addNS('text','svg'))
  t.text=text
  t.set('x',str(self.unittouu(str(positon[0])+positon[2])))
  t.set('y',str(self.unittouu(str(positon[1])+positon[2])))
  parent.append(t)
  return t
  
def drawS(XYstring,color):         # Draw lines from a list
  name='part'
  style = { 'stroke': color, 'fill': 'none' }
  drw = {'style':simplestyle.formatStyle(style),inkex.addNS('label','inkscape'):name,'d':XYstring}
  inkex.etree.SubElement(parent, inkex.addNS('path','svg'), drw )
  return
  
def groupdraw(XYstrings,colors)  :
  if len(XYstrings)==1:
    drawS(XYstrings[0],colors[0])
    return
  grp_name = 'Group'
  grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
  grp = inkex.etree.SubElement(parent, 'g', grp_attribs)#the group to put everything in
  name='part'
  for i in range(len(XYstrings)):
    style = { 'stroke': colors[i], 'fill': 'none' }
    drw = {'style':simplestyle.formatStyle(style),inkex.addNS('label','inkscape'):name+str(i),'d':XYstrings[i]}
    inkex.etree.SubElement(grp, inkex.addNS('path','svg'), drw )
  return

def svg_from_points(points,offset):
  s='M'+str(points[0][0]+offset[0])+','+str(points[0][1]+offset[1])
  for i in range(1,len(points)):
    s+='L'+str(points[i][0]+offset[0])+','+str(points[i][1]+offset[1])
  s+='Z'
  return s
  
class Polygon(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options
      self.OptionParser.add_option('--unit',action='store',type='string',
        dest='unit',default='mm',help='Measure Units')
      self.OptionParser.add_option('--tab',action='store',type='string',
        dest='tab',default='page_1',help='tab')
      self.OptionParser.add_option('--o_type', action='store',type='int',
        dest='o_type', default=1,help='outer type')
      self.OptionParser.add_option('--o_radius',action='store',type='float',
        dest='o_radius',default=100,help='Outer Radius')
      self.OptionParser.add_option('--o_edges', action='store',type='int',
        dest='o_edges', default=1,help='outer edges')
      self.OptionParser.add_option('--o_r_type', action='store',type='int',
        dest='o_r_type', default=1,help='outer radius type')
      self.OptionParser.add_option('--o_offset',action='store',type='float',
        dest='o_offset',default=100,help='Outer Radius')
        
      self.OptionParser.add_option('--i_type', action='store',type='int',
        dest='i_type', default=1,help='inter type')
      self.OptionParser.add_option('--i_radius',action='store',type='float',
        dest='i_radius',default=100,help='inter Radius')
      self.OptionParser.add_option('--i_edges', action='store',type='int',
        dest='i_edges', default=1,help='inter edges')
      self.OptionParser.add_option('--i_r_type', action='store',type='int',
        dest='i_r_type', default=1,help='inter radius type')
      self.OptionParser.add_option('--i_offset',action='store',type='float',
        dest='i_offset',default=100,help='Outer Radius')
        
      self.OptionParser.add_option('--kerf',action='store',type='float',
        dest='kerf',default=0.5,help='Kerf (width) of cut')
      self.OptionParser.add_option('--spaceing',action='store',type='float',
        dest='spaceing',default=0.5,help='spaceing')
        
      self.OptionParser.add_option('--color1',action='store',type='string',
        dest='color1',default="#000000",help='color1')
      self.OptionParser.add_option('--color2',action='store',type='string',
        dest='color2',default="#FF0000",help='color1')
      self.OptionParser.add_option('--intensity', action='store',type='int',
        dest='intensity', default=1,help='intensity')
      self.OptionParser.add_option('--speed', action='store',type='int',
        dest='speed', default=1,help='speed')
      self.OptionParser.add_option('--pass_offset', action='store',type='int',
        dest='pass_offset', default=1,help='pass_offset')
      self.OptionParser.add_option('--lasertag',action='store',type='string',
        dest='lasertag',default="=pass%n:%s:%i:%c=",help='color1')
  def effect(self):
    global parent,nomTab,equalTabs,thickness,kerf,correction
    
    # Get access to main SVG document element and get its dimensions.
    svg = self.document.getroot()
    
    # Get the attibutes:
    widthDoc  = self.unittouu(svg.get('width'))
    heightDoc = self.unittouu(svg.get('height'))

    # Create a new layer.
    layer = inkex.etree.SubElement(svg, 'g')
    layer.set(inkex.addNS('label', 'inkscape'), 'newlayer')
    layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
    
    parent=self.current_layer
    
    # Get script's option values.
    unit=self.options.unit
    kerf = self.unittouu( str(self.options.kerf)  + unit )
    spaceing = self.unittouu( str(self.options.spaceing)  + unit )
    
    o_type=self.options.o_type
    o_edges=self.options.o_edges
    o_r_type=self.options.o_r_type
    o_radius=self.unittouu(str(self.options.o_radius+kerf)+unit)
    o_offset=math.radians(-self.options.o_offset)+math.pi
    
    i_type=self.options.i_type
    i_edges=self.options.i_edges
    i_r_type=self.options.i_r_type
    i_radius=self.unittouu(str(self.options.i_radius+kerf)+unit)
    i_offset=math.radians(-self.options.i_offset)+math.pi
    
    color1=self.options.color1
    color2=self.options.color2
    intensity=self.options.intensity
    speed=self.options.speed
    pass_offset=self.options.pass_offset
    lasertag=self.options.lasertag

    if (o_r_type==2 and o_type==2):
      beta=math.pi/2-(math.pi/o_edges)
      o_radius/=math.sin(beta)
    if (o_r_type==3 and o_type==2):
      alpha=(2*math.pi/o_edges)
      beta=(math.pi-alpha)/2
      o_radius*=math.sin(beta)/math.sin(alpha)
    if (i_r_type==2 and i_type==2):
      beta=math.pi/2-(math.pi/i_edges)
      i_radius/=math.sin(beta)
    if (i_r_type==3 and i_type==2):
      alpha=(2*math.pi/i_edges)
      beta=(math.pi-alpha)/2
      i_radius*=math.sin(beta)/math.sin(alpha)
    if(o_type==1):
      s=['M '+str(spaceing)+','+str(o_radius+spaceing)+'a'+str(o_radius)+','+str(o_radius)+' 0 1,0 '+str(2*(o_radius))+',0'+'a'+str(o_radius)+','+str(o_radius)+' 0 1,0 '+str(-2*(o_radius))+',0']
    if(o_type==2):
      stepsize=2*math.pi/o_edges
      points=[]
      for i in range(o_edges):
        points+=[(math.sin(o_offset+stepsize*i)*(o_radius),math.cos(o_offset+stepsize*i)*(o_radius))]
      s=[svg_from_points(points,(o_radius+spaceing,o_radius+spaceing))]
    if(i_type==1):
      s+=['M '+str(spaceing+o_radius-i_radius)+','+str(o_radius+spaceing)+'a'+str(i_radius)+','+str(i_radius)+' 0 1,0 '+str(2*i_radius)+',0'+'a'+str(i_radius)+','+str(i_radius)+' 0 1,0 '+str(-2*i_radius)+',0']
    if(i_type==2):
      stepsize=2*math.pi/i_edges
      points=[]
      for i in range(i_edges):
        points+=[(math.sin(i_offset+stepsize*i)*(i_radius),math.cos(i_offset+stepsize*i)*(i_radius))]
      s+=[svg_from_points(points,(o_radius+spaceing,o_radius+spaceing))]
    colors=[color1,color2]
    groupdraw(s,colors)
    for i in range(len(s)):
      textElement(lasertag.replace("%n",str(pass_offset+len(s)-i)).replace("%s",str(speed)).replace("%i",str(intensity)).replace("%c",colors[i]),(0,-i*10,"pt"),self)
# Create effect instance and apply it.
effect = Polygon()
effect.affect()