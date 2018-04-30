"""Agent to solve (my own implementation) of Snake."""

from absl import app
import gym
import gym_snake
import numpy as np


class QFunctionApproxAgent(object):
    def __init__(self, actions, dims):
        self._actions = actions

        self._gamma = 0.9
        self._alpha = 0.00001
        self._eps = 0.3

        # bias + action + distance to apple + sorrounding
        self._weights = np.zeros(1 + 1 + 1 + 4)
        self._prev_state_action = None

        self._step = 0
        self._episode = 0

    def _phi(self, state, action):
        """Creates features from (state, action)."""
        head = np.where(state == 2)
        right = state[(head[0], (head[1] + 1) % 10)]
        up = state[((head[0] - 1) % 10, head[1])]
        left = state[(head[0], (head[1] - 1) % 10)]
        down = state[((head[0] + 1) % 10, head[1])]

        # Distance to apple
        head = np.array([head[1][0], head[0][0]])
        apple = np.where(state == 3)
        apple = np.array([apple[1][0], apple[0][0]])
        dist = np.linalg.norm(head-apple)

        return np.array([1, action, dist, right, up, left, down])

    def _find_max_action(self, state):
        """Finds the action with the maximum expected reward in the `state`."""
        max_action = 0
        max_q_val = np.dot(self._weights, self._phi(state, max_action))
        for action in range(1, self._actions.n):
            q_val = np.dot(self._weights, self._phi(state, action))
            if q_val > max_q_val:
                max_q_val = q_val
                max_action = action
        return max_action

    def _update_q(self, next_state, reward, done):
        """Performs "gradient descent" on the Q-Function weights.

        Note: no automatic differentiation is necessary since the partial
        derivatives were done by hand.
        """
        if done:
            q_prime = reward
        else:
            phi_prime = self._phi(
                next_state, self._find_max_action(next_state))
            q_prime = reward + self._gamma * np.dot(self._weights, phi_prime)
        phi = self._phi(*self._prev_state_action)
        self._weights -= (self._alpha *
                          (q_prime - np.dot(phi, self._weights))) * phi
        print(self._episode, self._step, q_prime)

    def act(self, state, reward=None, done=False):
        """Updates the internal Q Function weights and choses an action.

        Args:
            state: the current state of the environment.
            reward: the reward in the current state, `None` if this is the
                first state.
            done: whether the episode has ended.
        Returns:
            The next action to take.
        """
        self._step += 1
        # TODO(ehotaj): decay alpha and eps
        if not self._prev_state_action:
            assert not reward
            assert not done
            self._episode += 1
            action = self._find_max_action(state)
            self._prev_state_action = (state, action)
            return action

        self._update_q(state, reward, done)

        if done:
            self._prev_state_action = None
            return None

        if np.random.uniform() < self._eps:
            action = self._actions.sample()
            self._prev_state_action = (state, action)
            return action
        action = self._find_max_action(self._prev_state_action[0])
        self._prev_state_action = (state, action)
        return action


def main(argv):
    del argv  # Unused.

    env = gym.make('Snake-v0')
    env.reset()
    agent = QFunctionApproxAgent(env.action_space, (10, 10))
    # TODO(ehotaj): probably the worst way to do this act/observe loop
    counter = -1
    while True:
        counter += 1
        if counter == 0:
            env.reset()
            state, reward, done, _ = env.step(env.action_space.sample())
            # TODO(ehotaj): there may be some bug in the gym-snake code
            # as in a substantial number of cases, the first action leads to
            # an game over. Theoretically, this should not be possible.
            if not done:
                action = agent.act(state)
        else:
            state, reward, done, _ = env.step(action)
            action = agent.act(state, reward, done)

        if done:
            counter = -1
        env.render()


if __name__ == '__main__':
    app.run(main)