"""smp systems

A system in the smp framework is any thing that can be packed into a
box with inputs and outputs and some kind of internal activity that
transforms inputs into outputs.

I distinguish open-loop systems (OLS) and closed-loop systems (CLS).

*OLS*'s are autonomous data sources that ignore any actual input, just
do their thing and produce some output. Examples are a file reader, a
signal generator, ...

*CLS*'s are data sources that depend fundamentally on some input and
will probably not produce any interesting output without any
input. Examples are all actual simulated and real robots, things with
motors, things that can move or somehow do stuff in any kind of world.

"""

# existing systems in legacy code for pulling in
#  - pointmass: mass, dimension, order(0: kinematic/pos,
#    1: dynamic/velocity, 2: dynamic/force),
#   - model v1
#    - smp/smp/ode_inert_system.py: InertParticle, InertParticle2D, InertParticleND,
#    - smp/smpblocks/smpblocks/systems.py
#
#   - model v2
#    - explauto/explauto/environment/pointmass/pointmass.py
#    - smq/smq/robots.py

# smp/smp/arm: kinematic, dynamic
# smp_sphero/sphero: wheels, angle/vel, x/y
# smq/smq/arm
# smq/smq/stdr
# smp/morse_work/atrv
# smp/morse_work/turtlebot
# smp/morse_work/quadrotor
# bha model
# ntrtsim
# malmo

# TODO
#  - A system should be given a reference to a 'world' that implies
#    constraints on state values and provides autonmous activity from outside the agent

import numpy as np

class SMPSys(object):
    def __init__(self, conf = {}):
        self.conf = conf
        # set_attr_from_dict(self, conf) # check that this is OK

        # set_attr_from_dict_ifs(self, ifs_conf)
        
        # self.id = self.__class__.__name__
        for k, v in conf.items():
            setattr(self, k, v)
            # print "%s.init self.%s = %s" % (self.__class__.__name__, k, v)

        # ROS
        if hasattr(self, 'ros') and self.ros:
            # rospy.init_node(self.name)
            self.subs = {}
            self.pubs = {}
            
    def step(self, x):
        return None

class PointmassSys(SMPSys):
    """point mass system (pm)

    a pm is an abstract model of a rigid body robot represented by the coordinates 

    taken from smq/robots.py, seems to be the same code as in explauto/environments/pointmass.py
    """
    defaults = {
        'sysdim': 1,
        'x0': np.random.uniform(-0.3, 0.3, (3, 1)),
        'statedim': 3,
        'dt': 1e-1,
        'mass': 1.0,
        "force_max":  1.0,
        "force_min": -1.0,
        "friction": 0.001,
        "sysnoise": 1e-2,
        }
    
    def __init__(self, conf = {}):
        """Pointmass.__init__

        Arguments:
        - conf: configuration dictionary
        -- mass: point _mass_
        -- sysdim: dimension of system, usually 1,2, or 3D
        -- statedim: 1d pointmass has 3 variables (pos, vel, acc) in this model, so sysdim * 3
        -- dt: integration time step
        -- x0: initial state
        -- order: NOT IMPLEMENT (control mode of the system, order = 0 kinematic, 1 velocity, 2 force)
        """
        SMPSys.__init__(self, conf)
        
        # state is (pos, vel, acc).T
        # self.state_dim
        if not hasattr(self, 'x0'):
            self.x0 = np.zeros((self.statedim, 1))
        self.x  = self.x0.copy()
        self.cnt = 0

    def reset(self):
        self.x = self.x0.copy()
        
    def step(self, x = None, world = None):
        """update the robot, pointmass"""
        # print "%s.step[%d] x = %s" % (self.__class__.__name__, self.cnt, x)
        # x = self.inputs['u'][0]
        self.apply_force(x)
        # return dict of state values
        return {'s_proprio': self.compute_sensors_proprio(),
                's_extero':  self.compute_sensors_extero(),
                's_all':     self.compute_sensors(),
        }
        
    def bound_motor(self, m):
        return np.clip(m, self.force_min, self.force_max)

    def apply_force(self, u):
        """control pointmass with force command (2nd order)"""
        # print "u", u, self.mass, u/self.mass
        # FIXME: insert motor transfer function
        a = (u/self.mass).reshape((self.sysdim, 1))
        # a += np.random.normal(0.05, 0.01, a.shape)

        # # world modification
        # if np.any(self.x[:self.sysdim] > 0):
        #     a += np.random.normal(0.05, 0.01, a.shape)
        # else:
        #     a += np.random.normal(-0.1, 0.01, a.shape)
            
        # print("a.shape", a.shape)
        # print "a", a, self.x[self.conf.s_ndims/2:]
        v = self.x[self.sysdim:self.sysdim*2] * (1 - self.friction) + a * self.dt
        
        # self.a_ = a.copy()
        
        
        # # world modification
        # v += np.sin(self.cnt * 0.01) * 0.05
        
        # print "v", v
        p = self.x[:self.sysdim] + v * self.dt

        # collect temporary state description (p,v,a) into joint state vector x
        self.x[:self.sysdim] = p.copy()
        self.x[self.sysdim:self.sysdim*2] = v.copy()
        self.x[self.sysdim*2:] = a.copy()

        # apply noise
        self.x += self.sysnoise * np.random.randn(self.x.shape[0], self.x.shape[1])

        # print "self.x[2,0]", self.x[2,0]

        # self.scale()
        # self.pub()                
        self.cnt += 1
        
        # return x
        # self.x = x # pointmasslib.simulate(self.x, [u], self.dt)

    def compute_sensors_proprio(self):
        return self.x[self.sysdim*2:]
    
    def compute_sensors_extero(self):
        return self.x[self.sysdim:self.sysdim*2]
    
    def compute_sensors(self):
        """compute the proprio and extero sensor values from state"""
        return self.x



def forward(angles, lengths):
    """ Link object as defined by the standard DH representation.

    :param list angles: angles of each joint

    :param list lengths: length of each segment

    :returns: a tuple (x, y) of the end-effector position

    .. warning:: angles and lengths should be the same size.
    """
    x, y = joint_positions(angles, lengths)
    return x[-1], y[-1]

def joint_positions(angles, lengths, unit='rad'):
    """ Link object as defined by the standard DH representation.

    :param list angles: angles of each joint

    :param list lengths: length of each segment

    :returns: x positions of each joint, y positions of each joints, except the first one wich is fixed at (0, 0)

    .. warning:: angles and lengths should be the same size.
    """
    # print "angles", angles, "lengths", lengths
    
    if len(angles) != len(lengths):
        raise ValueError('angles and lengths must be the same size!')

    if unit == 'rad':
        a = np.array(angles)
    elif unit == 'std':
        a = np.pi * np.array(angles)
    else:
        raise NotImplementedError
     
    a = np.cumsum(a)
    return np.cumsum(np.cos(a)*lengths), np.cumsum(np.sin(a)*lengths)

class SimplearmSys(SMPSys):
    """SimplearmSys

    explauto's simplearm environment

    an n-joint / n-1 segment generative robot
    """

    defaults = {
        'sysdim': 1,
        'x0': np.random.uniform(-0.3, 0.3, (3, 1)),
        'statedim': 3,
        'dt': 1e-1,
        'mass': 1.0,
        "force_max":  1.0,
        "force_min": -1.0,
        "friction": 0.001,
        "sysnoise": 1e-2,
        'dim_s_motor': 3,
        'length_ratio': [1],
        'm_mins': -1,
        'm_maxs': 1,
        'dim_s_extero': 2,
        }
    
    def __init__(self, conf = {}):
        """SimplearmSys.__init__

        Arguments:
        - conf: configuration dictionary
        -- mass: point _mass_
        -- sysdim: dimension of system, usually 1,2, or 3D
        -- statedim: 1d pointmass has 3 variables (pos, vel, acc) in this model, so sysdim * 3
        -- dt: integration time step
        -- x0: initial state
        -- order: NOT IMPLEMENT (control mode of the system, order = 0 kinematic, 1 velocity, 2 force)
        """
        SMPSys.__init__(self, conf)
        
        # state is (pos, vel, acc).T
        # self.state_dim
        if not hasattr(self, 'x0'):
            self.x0 = np.zeros((self.statedim, 1))
        self.x  = self.x0.copy()
        self.cnt = 0



        self.factor = 1.0

        self.lengths = self.compute_lengths(self.dim_s_motor, self.length_ratio)

        self.m = np.zeros((self.dim_s_motor, 1))
        
    def reset(self):
        self.x = self.x0.copy()
        
    # def step(self, x = None, world = None):
    #     """update the robot, pointmass"""
    #     # print "%s.step[%d] x = %s" % (self.__class__.__name__, self.cnt, x)
    #     # x = self.inputs['u'][0]
    #     self.apply_force(x)
    #     # return dict of state values
    #     return {'s_proprio': self.compute_sensors_proprio(),
    #             's_extero':  self.compute_sensors_extero(),
    #             's_all':     self.compute_sensors(),
    #     }
        

    def compute_lengths(self, n_dofs, ratio):
        l = np.ones(n_dofs)
        for i in range(1, n_dofs):
            l[i] = l[i-1] / ratio
        return l / sum(l)

    def compute_motor_command(self, m):
        m *= self.factor
        return np.clip(m, self.m_mins, self.m_maxs)

    def compute_sensors_proprio(self):
        # hand_pos += 
        return self.m + self.sysnoise * np.random.randn(*self.m.shape)

    def step(self, x):
        """update the robot, pointmass"""
        # print "%s.step x = %s" % (self.__class__.__name__, x)
        # print "x", x.shape
        # self.m = self.compute_motor_command(self.m + x)# .reshape((self.dim_s_motor, 1))
        self.m = self.compute_motor_command(x)# .reshape((self.dim_s_motor, 1))
        
        # print "m", m
        # self.apply_force(x)
        return {"s_proprio": self.m, # self.compute_sensors_proprio(),
                "s_extero":  self.compute_sensors_extero(),
                's_all':     self.compute_sensors(),
                }

    def compute_sensors_extero(self):
        hand_pos = np.array(forward(self.m, self.lengths)).reshape((self.dim_s_extero, 1))
        hand_pos += self.sysnoise * np.random.randn(*hand_pos.shape)
        # print "hand_pos", hand_pos.shape
        return hand_pos

    def compute_sensors(self):
        """compute the proprio and extero sensor values from state"""
        # return np.vstack((self.m, self.compute_sensors_extero()))
        return np.vstack((self.compute_sensors_proprio(), self.compute_sensors_extero()))
        # return self.x
    
# class SimpleArmRobot(Robot2):
#     def __init__(self, conf, ifs_conf):
#         Robot2.__init__(self, conf, ifs_conf)
        
#         # self.length_ratio = length_ratio
#         # self.noise = noise

#         self.factor = 1.0

#         self.lengths = self.compute_lengths(self.dim_s_motor, self.length_ratio)

#         self.m = np.zeros((self.dim_s_motor, 1))

#     def compute_lengths(self, n_dofs, ratio):
#         l = np.ones(n_dofs)
#         for i in range(1, n_dofs):
#             l[i] = l[i-1] / ratio
#         return l / sum(l)

#     def compute_motor_command(self, m):
#         m *= self.factor
#         return np.clip(m, self.m_mins, self.m_maxs)

#     def step(self, world, x):
#         """update the robot, pointmass"""
#         print "%s.step world = %s, x = %s" % (self.__class__.__name__, world, x)
#         # print "x", x.shape
#         self.m = self.compute_motor_command(self.m + x)# .reshape((self.dim_s_motor, 1))
        
#         # print "m", m
#         # self.apply_force(x)
#         return {"s_proprio": self.m, # self.compute_sensors_proprio(),
#                 "s_extero": self.compute_sensors_extero()}

#     def compute_sensors_extero(self):
#         hand_pos = np.array(forward(self.m, self.lengths)).reshape((self.dim_s_extero, 1))
#         hand_pos += self.sysnoise * np.random.randn(*hand_pos.shape)
#         # print "hand_pos", hand_pos.shape
#         return hand_pos
                

    
sysclasses = [SimplearmSys, PointmassSys]
# sysclasses = [SimplearmSys]


if __name__ == "__main__":
    """smp_sys.systems.main

    simple test for this file's systems:
    - iterate all known classes
    - run system for 1000 steps on it's own proprioceptive (motor) sensors
    - plot timeseries
    """
    for c in sysclasses:
        print "class", c
        c_ = c(conf = c.defaults)
        c_data = []
        for i in range(1000):
            # do proprio feedback
            x = c_.compute_sensors_proprio() * 0.1
            # print "x", x
            # step system with feedback input
            d = c_.step(x = np.roll(x, shift = 1) * -1.0)['s_all'].copy()
            # print "d", d.shape
            c_data.append(d)

        # print c_data
        # print np.array(c_data).shape

        import matplotlib.pylab as plt
        # remove additional last axis
        plt.plot(np.array(c_data)[...,0])
        plt.show()
