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

import errno

import roslib
roslib.load_manifest('baxter_interface')
import rospy

import baxter_msgs.msg
import std_msgs.msg

import settings

class Head(object):
    def __init__(self):
        """
        Interface class for the head on the Baxter Robot.

        Used to control the head pan angle and to enable/disable the head nod
        action.
        """
        self._state = {}

        self._pub_pan = rospy.Publisher(
            '/sdk/robot/head/command_head_pan',
            baxter_msgs.msg.HeadPanCommand)

        self._pub_nod = rospy.Publisher(
            '/robot/head/command_head_nod',
            std_msgs.msg.Bool)

        self._sub_state = rospy.Subscriber(
            '/sdk/robot/head/head_state',
            baxter_msgs.msg.HeadState,
            self._on_head_state)

        rate = rospy.Rate(100)
        while not rospy.is_shutdown():
            if len(self._state.keys()):
                break
            rate.sleep()

    def _on_head_state(self, msg):
        self._state['pan'] = msg.pan
        self._state['panning'] = msg.isPanning
        self._state['nodding'] = msg.isNodding

    def pan(self):
        """
        Get the current pan angle of the head.

        @returns (float)    - current angle in radians
        """
        return self._state['pan']

    def nodding(self):
        """
        Check if the head is currently nodding.

        @returns (bool) - True if the head is currently nodding, False otherwise.
        """
        return self._state['nodding']

    def panning(self):
        """
        Check if the head is currently panning.

        @returns (bool) - True if the head is currently panning, False otherwise.
        """
        return self._state['panning']


    def set_pan(self, angle, speed = 100, timeout = 0):
        """
        Pan at the given speed to the desired angle.

        @param angle (float)    - Desired pan angle in radians.
        @param speed (int)      - Desired speed to pan at, range is 0-100 [100]
        @param timeout (float)  - Seconds to wait for the head to pan to the specified
                                  angle.  If 0, just command once and return.  [0]
        """
        msg = baxter_msgs.msg.HeadPanCommand(angle, speed)

        self._pub_pan.publish(msg)
        if timeout == 0:
            return

        hz = 100
        rate = rospy.Rate(100)

        for _ in range(int(hz * timeout)):
            if rospy.is_shutdown():
                break

            self._pub_pan.publish(msg)

            if abs(self.pan() - angle) < settings.JOINT_ANGLE_TOLERANCE:
                return

            rate.sleep()

        raise OSError(errno.ETIMEDOUT, "Timeout waiting for head pan")

    def command_nod(self):
        """
        Command the head to nod once.
        """
        msg = std_msgs.msg.Bool(True)

        hz = 100
        rate = rospy.Rate(hz)

        for _ in range(hz):
            if rospy.is_shutdown():
                break

            self._pub_nod.publish(msg)
            if self.nodding():
                return

            rate.sleep()

        raise OSError(errno.ETIMEDOUT, "Timeout commanding head to nod")
