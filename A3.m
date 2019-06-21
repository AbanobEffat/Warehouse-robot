function [ A3] = A3( a3 ,alpha3, d3 , theta3 )
%Trans matrix form 2 to 3 
syms theta3  
 a3=0
 alpha3=0
 d3=.45

A3 = [  cos(theta3)                 ,  -sin(theta3)*cos(alpha3)                       ,       sin(theta3)*sin(alpha3)               ,     a3*cos(theta3)                        ;
          sin(theta3) ,                            cos(theta3)*cos(alpha3)     ,                 -cos(theta3)*sin(alpha3)   ,                            a3 *sin(theta3)       ;
          0                ,                                 sin(alpha3)     ,                 cos(alpha3)   ,                                          d3                ;
                   0                        ,      0                                  ,     0               ,    1                             ;
]


end
