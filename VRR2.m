startup_rvc  % Run Robotics ToolBox 
 % link(theta,d,alpha,segma(0>> Revolute,1>> prismatic))
L(1)=  Link([0 .98 -.05 0]);
 L(2)=Link([0 0 0 -pi/2]);
 L(3)=Link([0 .45 0  0]);
L(4)=Link([0 .32  0 0]);
 VPR2=SerialLink(L,'name','VPR2')
  q=[0 0 0 0 ];
 VPR2.plot(q)
  VPR2.fkine(q)