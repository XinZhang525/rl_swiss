<mujoco model="arm3d">
  <compiler inertiafromgeom="true" angle="radian" coordinate="local"/>
  <option timestep="0.01" gravity="0 0 0" iterations="20" integrator="Euler" />
  
  <default>
    <joint armature='0.04' damping="1" limited="true"/>
    <geom friction=".8 .1 .1" density="300" margin="0.002" condim="1" contype="0" conaffinity="0"/>
  </default>
  
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
    <geom name="table" type="plane" pos="0 0.5 -0.325" size="1 1 0.1" contype="1" conaffinity="1"/>

    <body name="r_shoulder_pan_link" pos="0 -0.6 0">
      <geom name="e1" type="sphere" rgba="0.6 0.6 0.6 1" pos="-0.06 0.05 0.2" size="0.05" />
      <geom name="e2" type="sphere" rgba="0.6 0.6 0.6 1" pos=" 0.06 0.05 0.2" size="0.05" />
      <geom name="e1p" type="sphere" rgba="0.1 0.1 0.1 1" pos="-0.06 0.09 0.2" size="0.03" />
      <geom name="e2p" type="sphere" rgba="0.1 0.1 0.1 1" pos=" 0.06 0.09 0.2" size="0.03" />
      <geom name="sp" type="capsule" fromto="0 0 -0.4 0 0 0.2" size="0.1" />
      <joint name="r_shoulder_pan_joint" type="hinge" pos="0 0 0" axis="0 0 1" range="-2.2854 1.714602" damping="1.0" />

      <body name="r_shoulder_lift_link" pos="0.1 0 0">
        <geom name="sl" type="capsule" fromto="0 -0.1 0 0 0.1 0" size="0.1" />
        <joint name="r_shoulder_lift_joint" type="hinge" pos="0 0 0" axis="0 1 0" range="-0.5236 1.3963" damping="1.0" />

        <body name="r_upper_arm_roll_link" pos="0 0 0">
          <geom name="uar" type="capsule" fromto="-0.1 0 0 0.1 0 0" size="0.02" />
          <joint name="r_upper_arm_roll_joint" type="hinge" pos="0 0 0" axis="1 0 0" range="-1.5 1.7" damping="0.1" />

          <body name="r_upper_arm_link" pos="0 0 0">
            <geom name="ua" type="capsule" fromto="0 0 0 0.4 0 0" size="0.06" />

            <body name="r_elbow_flex_link" pos="0.4 0 0">
              <geom name="ef" type="capsule" fromto="0 -0.02 0 0.0 0.02 0" size="0.06" />
              <joint name="r_elbow_flex_joint" type="hinge" pos="0 0 0" axis="0 1 0" range="-2.3213 0" damping="0.1" />

              <body name="r_forearm_roll_link" pos="0 0 0">
                <geom name="fr" type="capsule" fromto="-0.1 0 0 0.1 0 0" size="0.02" />
                <joint name="r_forearm_roll_joint" type="hinge" limited="true" pos="0 0 0" axis="1 0 0" damping=".1" range="-1.5 1.5"/>

                <body name="r_forearm_link" pos="0 0 0">
                  <geom name="fa" type="capsule" fromto="0 0 0 0.291 0 0" size="0.05" />

                  <body name="r_wrist_flex_link" pos="0.321 0 0">
                    <geom name="wf" type="capsule" fromto="0 -0.02 0 0 0.02 0" size="0.01" />
                    <joint name="r_wrist_flex_joint" type="hinge" pos="0 0 0" axis="0 1 0" range="-1.094 0" damping=".1" />

                    <body name="r_wrist_roll_link" pos="0 0 0">
                      <joint name="r_wrist_roll_joint" type="hinge" pos="0 0 0" limited="true" axis="1 0 0" damping="0.1" range="-1.5 1.5"/>
                      <body name="tips_arm" pos="0 0 0">
                        <geom name="tip_arml" type="sphere" pos="0.1 -0.1 0." size="0.01" />
                        <geom name="tip_armr" type="sphere" pos="0.1 0.1 0." size="0.01" />
                      </body>
                      <geom type="capsule" fromto="0 -0.1 0. 0.0 +0.1 0" size="0.02" contype="1" conaffinity="1" />
                      <geom type="capsule" fromto="0 -0.1 0. 0.1 -0.1 0" size="0.02" contype="1" conaffinity="1" />
                      <geom type="capsule" fromto="0 +0.1 0. 0.1 +0.1 0." size="0.02" contype="1" conaffinity="1" />
                    </body>
                  </body>
                </body>
              </body>
            </body>
          </body>
        </body>
      </body>
    </body>

    <!--<body name="object" pos="0.55 -0.3 -0.275" >-->
    <body name="object" pos="0.45 -0.05 -0.275" >
      <geom rgba="1 1 1 0" type="sphere" size="0.05 0.05 0.05" density="0.00001" conaffinity="0"/>
      <geom rgba="1 1 1 1" type="cylinder" size="0.05 0.05 0.05" density="0.00001" contype="1" conaffinity="0"/>
      <joint name="obj_slidey" type="slide" pos="0 0 0" axis="0 1 0" range="-10.3213 10.3" damping="0.5"/>
      <joint name="obj_slidex" type="slide" pos="0 0 0" axis="1 0 0" range="-10.3213 10.3" damping="0.5"/>
    </body>

    <body name="goal" pos="0.45 -0.05 -0.3230">
      <geom rgba="1 0 0 1" type="cylinder" size="0.08 0.001 0.1" density='0.00001' contype="0" conaffinity="0"/>
      <joint name="goal_slidey" type="slide" pos="0 0 0" axis="0 1 0" range="-10.3213 10.3" damping="0.5"/>
      <joint name="goal_slidex" type="slide" pos="0 0 0" axis="1 0 0" range="-10.3213 10.3" damping="0.5"/> 
    </body>
  </worldbody>

  <actuator>
    <motor joint="r_shoulder_pan_joint" ctrlrange="-2.0 2.0" ctrllimited="true" />
    <motor joint="r_shoulder_lift_joint" ctrlrange="-2.0 2.0" ctrllimited="true" />
    <motor joint="r_upper_arm_roll_joint" ctrlrange="-2.0 2.0" ctrllimited="true" />
    <motor joint="r_elbow_flex_joint" ctrlrange="-2.0 2.0" ctrllimited="true" />
    <motor joint="r_forearm_roll_joint" ctrlrange="-2.0 2.0" ctrllimited="true" />
    <motor joint="r_wrist_flex_joint" ctrlrange="-2.0 2.0" ctrllimited="true" />
    <motor joint="r_wrist_roll_joint" ctrlrange="-2.0 2.0" ctrllimited="true"/>
  </actuator>
</mujoco>