function [ A1] = A1( a1 ,alpha1, d1 ,theta1  )
%Trans matrix form 1 to 0 
syms theta1 
 a1=-.05
 alpha1=0
 d1=.98
A1= [  cos(theta1) , -sin(theta1)*cos(alpha1) , sin(theta1)*sin(alpha1)  , a1*cos(theta1)                 ;
         sin(theta1) ,  cos(theta1)*cos(alpha1)  , -cos(theta1)*sin(alpha1)   ,  a1 *sin(theta1)       ;
          0     ,     sin(alpha1)     ,    cos(alpha1)   ,      d1                ;
            0    ,   0             ,     0               ,    1                             ;
]
