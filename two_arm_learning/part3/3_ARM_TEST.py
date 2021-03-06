import numpy as np
import pyglet


class ArmEnv(object):
    viewer = None
    dt = 0.1    # refresh rate
    action_bound = [-1, 1]  # 每一步最大转动
    goal = {'x': 100., 'y': 100., 'l': 40}  # 被抓物体位置
    state_dim = 3  # 两个观测角度
    action_dim = 3  # 关节数

    def __init__(self):
        # 生成一个3X3的表 保存转动角参数
        self.arm_info = np.zeros(
            3, dtype=[('l', np.float32), ('r', np.float32)])
        self.arm_info['l'] = 100 # 机械臂长度
        self.arm_info['r'] = np.pi/6

    def step(self, action):
        done = False
        r = 0.
        action = np.clip(action, *self.action_bound)
        self.arm_info['r'] += action * self.dt
        self.arm_info['r'] %= np.pi * 2    # normalize

        # state
        s = self.arm_info['r']

        (a1l, a2l,a3l) = self.arm_info['l']  # radius, arm length
        (a1r, a2r,a3r) = self.arm_info['r']  # radian, angle
        a1xy = np.array([00., 200.])    # a1 start (x0, y0)
        a1xy_ = np.array([np.cos(a1r), np.sin(a1r)]) * a1l + a1xy  # a1 end and a2 start (x1, y1)
        a2xy_ = np.array([np.cos(a1r + a2r), np.sin(a1r + a2r)]) * a2l + a1xy_ # a2 end (x2, y2)
        finger = a2xy_ +np.array([np.cos(a1r + a2r+a3r), np.sin(a1r + a2r+a3r)]) * a3l

        # done and reward
        if (self.goal['x'] - self.goal['l']/2 < finger[0] < self.goal['x'] + self.goal['l']/2
        ) and (self.goal['y'] - self.goal['l']/2 < finger[1] < self.goal['y'] + self.goal['l']/2):
                done = True
                r = 1.
        return s, r, done

    def reset(self):
        self.arm_info['r'] = 2 * np.pi * np.random.rand(3)
        return self.arm_info['r']

    def render(self):
        if self.viewer is None:
            self.viewer = Viewer(self.arm_info, self.goal)
        self.viewer.render()

    def sample_action(self):
        return np.random.rand(3)-0.5    # two radians


class Viewer(pyglet.window.Window):
    bar_thc = 5  # 机械臂宽度

    def __init__(self, arm_info, goal):
        # vsync=False to not use the monitor FPS, we can speed up training
        super(Viewer, self).__init__(width=500, height=500, resizable=False, caption='Arm', vsync=False)
        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.arm_info = arm_info
        self.center_coord = np.array([300, 300])  # 机械臂chushi坐标

        self.batch = pyglet.graphics.Batch()    # display whole batch at once
        self.goal = self.batch.add(
            4, pyglet.gl.GL_QUADS, None,    # 4 corners
            ('v2f', [goal['x'] - goal['l'] / 2, goal['y'] - goal['l'] / 2,                # location
                     goal['x'] - goal['l'] / 2, goal['y'] + goal['l'] / 2,
                     goal['x'] + goal['l'] / 2, goal['y'] + goal['l'] / 2,
                     goal['x'] + goal['l'] / 2, goal['y'] - goal['l'] / 2]),
            ('c3B', (86, 109, 249) * 4))    # color
        self.arm1 = self.batch.add(
            4, pyglet.gl.GL_QUADS, None,
            ('v2f', [250, 250,                # location
                     250, 300,
                     260, 300,
                     260, 250]),
            ('c3B', (249, 86, 86) * 4,))    # color
        self.arm2 = self.batch.add(
            4, pyglet.gl.GL_QUADS, None,
            ('v2f', [100, 150,              # location
                     100, 160,
                     200, 160,
                     200, 150]), ('c3B', (249, 86, 86) * 4,))
        self.arm3 = self.batch.add(
            4, pyglet.gl.GL_QUADS, None,
            ('v2f', [90, 140,  # location
                     90, 150,
                     190, 150,
                     190, 140]), ('c3B', (249, 86, 86) * 4,))

    def render(self):
        self._update_arm()
        self.switch_to()
        self.dispatch_events()
        self.dispatch_event('on_draw')
        self.flip()

    def on_draw(self):
        self.clear()
        self.batch.draw()

    def _update_arm(self):
        (a1l, a2l, a3l) = self.arm_info['l']     # radius, arm length
        (a1r, a2r, a3r) = self.arm_info['r']     # radian, angle
        a1xy = self.center_coord            # a1 start (x0, y0)
        a1xy_ = np.array([np.cos(a1r), np.sin(a1r)]) * a1l + a1xy   # a1 end and a2 start (x1, y1)
        a2xy_ = np.array([np.cos(a1r+a2r), np.sin(a1r+a2r)]) * a2l + a1xy_  # a2 end (x2, y2)
        a3xy_ = a2xy_ + np.array([np.cos(a1r+a2r+a3r), np.sin(a1r+a2r+a3r)]) * a3l

        a1tr = np.pi / 2 - self.arm_info['r'][0]
        a2tr = np.pi / 2 - self.arm_info['r'][0]-self.arm_info['r'][1]
        a3tr = a2tr-self.arm_info['r'][2]


        xy01 = a1xy + np.array([-np.cos(a1tr), np.sin(a1tr)]) * self.bar_thc
        xy02 = a1xy + np.array([np.cos(a1tr), -np.sin(a1tr)]) * self.bar_thc
        xy11 = a1xy_ + np.array([np.cos(a1tr), -np.sin(a1tr)]) * self.bar_thc
        xy12 = a1xy_ + np.array([-np.cos(a1tr), np.sin(a1tr)]) * self.bar_thc

        xy11_ = a1xy_ + np.array([np.cos(a2tr), -np.sin(a2tr)]) * self.bar_thc
        xy12_ = a1xy_ + np.array([-np.cos(a2tr), np.sin(a2tr)]) * self.bar_thc
        xy21 = a2xy_ + np.array([-np.cos(a2tr), np.sin(a2tr)]) * self.bar_thc
        xy22 = a2xy_ + np.array([np.cos(a2tr), -np.sin(a2tr)]) * self.bar_thc

        xy21_ = a2xy_ + np.array([-np.cos(a3tr), np.sin(a3tr)]) * self.bar_thc
        xy22_ = a2xy_ + np.array([np.cos(a3tr), -np.sin(a3tr)]) * self.bar_thc
        xy31 = a3xy_ + np.array([np.cos(a3tr), -np.sin(a3tr)]) * self.bar_thc
        xy32 = a3xy_ + np.array([-np.cos(a3tr), np.sin(a3tr)]) * self.bar_thc

        self.arm1.vertices = np.concatenate((xy01, xy02, xy11, xy12))
        self.arm2.vertices = np.concatenate((xy11_, xy12_, xy21, xy22))
        self.arm3.vertices = np.concatenate((xy21_, xy22_, xy31, xy32))


if __name__ == '__main__':
    env = ArmEnv()
    while True:
        env.render()
        env.step(env.sample_action())