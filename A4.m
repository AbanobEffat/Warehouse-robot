function [A4] = A4( a3,alpha4,d4,theta4)
%Trans matrix form 3 to 4 
syms theta4  
 a4=0
 alpha4=0
 d4=.32

A4= [  cos(theta4)                 ,  -sin(theta4)                       ,      0              ,     a4                         ;
          sin(theta4)*cos(alpha4) ,  cos(theta4)*cos(alpha4)     , -sin(alpha4)   ,    -d4 *sin(alpha4)       ;
          sin(theta4)*sin(alpha4)  ,   cos(theta4)*sin(alpha4)     , cos(alpha4)   ,     d4 *cos(alpha4)       ;
                   0                        ,      0                                  ,     0               ,    1                             ;
]
end
