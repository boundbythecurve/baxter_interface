#!/usr/bin/env python

# Copyright (c) 2013, Rethink Robotics
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the Rethink Robotics nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
Baxter RSDK Joint Position Example: joystick
"""
import argparse

import roslib
roslib.load_manifest('joint_position')
import rospy

import baxter_interface
import iodevices

def rotate(l):
    """
    rotates a list left
    @param l - the list
    """
    if len(l):
        v = l[0]
        l[:-1] = l[1:]
        l[-1] = v

def set_j(cmd, limb, joints, index, delta):
    """
    set the selected joint to current pos + delta
    joint/index is to make this work in the bindings
    @param cmd - the joint command dictionary
    @param limb - the limb to get the pos from
    @param joints - a list of joint names
    @param index - the index in the list of names
    @param delta - delta to update the joint by
    """
    joint = joints[index]
    cmd[joint] = delta + limb.joint_angle(joint)

def map_joystick(joystick):
    """
    maps joystick input to joint position commands
    @param joystick - an instance of a Joystick
    """
    left = baxter_interface.Limb('left')
    right = baxter_interface.Limb('right')
    grip_left = baxter_interface.Gripper('left')
    grip_right = baxter_interface.Gripper('right')
    lcmd = {}
    rcmd = {}

    #available joints
    lj = ['s0', 's1', 'e0', 'e1', 'w0', 'w1', 'w2']
    rj = ['s0', 's1', 'e0', 'e1', 'w0', 'w1', 'w2']

    #abbreviations
    jhi = lambda s: joystick.stick_value(s) > 0
    jlo = lambda s: joystick.stick_value(s) < 0
    bdn = joystick.button_down
    bup = joystick.button_up

    bindings = (
        ((bdn, ['rightTrigger']), (grip_left.close,  []), "left: gripper close"),
        ((bup, ['rightTrigger']), (grip_left.open,   []), "left: gripper open"),
        ((bdn, ['leftTrigger']),  (grip_right.close, []), "right: gripper close"),
        ((bup, ['leftTrigger']),  (grip_right.open,  []), "right: gripper open"),
        ((jhi, ['leftStickHorz']),  (set_j, [rcmd, right, rj, 0,  0.1]), lambda i=0:"right inc "+rj[i]),
        ((jlo, ['leftStickHorz']),  (set_j, [rcmd, right, rj, 0, -0.1]), lambda i=0:"right dec "+rj[i]),
        ((jhi, ['rightStickHorz']), (set_j, [lcmd, left,  lj, 0,  0.1]), lambda i=0:"left inc "+lj[i]),
        ((jlo, ['rightStickHorz']), (set_j, [lcmd, left,  lj, 0, -0.1]), lambda i=0:"left dec "+lj[i]),
        ((jhi, ['leftStickVert']),  (set_j, [rcmd, right, rj, 1,  0.1]), lambda i=1:"right inc "+rj[i]),
        ((jlo, ['leftStickVert']),  (set_j, [rcmd, right, rj, 1, -0.1]), lambda i=1:"right dec "+rj[i]),
        ((jhi, ['rightStickVert']), (set_j, [lcmd, left,  lj, 1,  0.1]), lambda i=1:"left inc "+lj[i]),
        ((jlo, ['rightStickVert']), (set_j, [lcmd, left,  lj, 1, -0.1]), lambda i=1:"left dec "+lj[i]),
        ((bdn, ['rightBumper']), (rotate, [lj]), "left: cycle joint"),
        ((bdn, ['leftBumper']),  (rotate, [rj]), "right: cycle joint"),
    )

    rate = rospy.Rate(100)
    print("press any key to stop...")
    while not rospy.is_shutdown():
        if iodevices.getch():
            return True
        for (test, cmd, doc) in bindings:
            if test[0](*test[1]):
                cmd[0](*cmd[1])
                if callable(doc):
                    print(doc())
                else:
                    print(doc)
        if len(lcmd):
            left.set_positions(lcmd)
            lcmd.clear()
        if len(rcmd):
            right.set_positions(rcmd)
            rcmd.clear()
        rate.sleep()
    return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("joystick", help="specify the type of joystick to use; xbox or logitech")
    args, unknown = parser.parse_known_args()

    print("Initializing node... ")
    rospy.init_node("rethink_rsdk_joint_position_joystick")
    print("Getting robot state... ")
    rs = baxter_interface.RobotEnable()
    print("Enabling robot... ")
    rs.enable()

    joystick = None
    if args.joystick == 'xbox':
        joystick = iodevices.joystick.XboxController()
    elif args.joystick == 'logitech':
        joystick = iodevices.joystick.LogitechController()
    else:
        parser.error("Unsupported joystick type '%s'" % (args.joystick))

    if map_joystick(joystick):
        print("Disabling robot... ")
        rs.disable()
        print("done")
    else:
        print("terminated")