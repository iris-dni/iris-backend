from fabric.api import env

env.forward_agent = True
env.user = 'admin'

import es  # noqa
import migrate  # noqa

import v_0_1_0  # noqa
