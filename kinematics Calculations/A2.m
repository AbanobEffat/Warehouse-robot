function [ A2] = A2( a2 ,alpha2, d2 , theta2 )
%Trans matrix form 2 to 1 
syms theta2  
 a2=0
 alpha2=-90
 d2=0


A2= [  cos(theta2)     ,  -sin(theta2)*cosd(alpha2)   ,       sin(theta2)*sind(alpha2)          ,     a2*cos(theta2)        ;
          sin(theta2) ,      cos(theta2)*cosd(alpha2)     ,    -cos(theta2)*sind(alpha2)   ,       a2 *sin(theta2)       ;
          0       ,        sind(alpha2)     ,                 cosd(alpha2)   ,      d2                ;
                   0           ,      0      ,     0               ,    1                             ;
]
end

