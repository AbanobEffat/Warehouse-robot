clc ; clear all ;
%Find forward kinematics for the Robot by symbolic toolbox 
A= A1*A2*A3*A4;
 Fk=A

 matlabFunction(Fk,'file','kin')
theta1=0;
theta2=0;
theta3=0;
theta4=0;

forward_kinematics=kin(theta1,theta2,theta3,theta4)


