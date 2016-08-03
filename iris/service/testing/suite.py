import os
import doctest
from functools import partial

from pyramid import paster
from webtest import TestApp

from lovely.essequence import sequence

from iris.service.petition import Petition
from iris.service.user import User
from iris.service.city import City

from . import util
from . import layer
from . import samples


here = os.path.abspath(os.path.dirname(__file__))
conf = os.path.join(here, 'testing.ini')

default_app = None
app = None


def get_app():
    global default_app, app
    if default_app is None:
        default_app = paster.get_app(conf, 'main')
    app = default_app
    return app


def create_object(cls, *args, **kwargs):
    obj = cls(*args, **kwargs)
    obj.store(refresh=True)
    return obj


class Creators(object):
    """Provides access to document classes

    This is to simplify tests. In a test it is possible to create instances
    without the need to import the document classes::

        Create a petition:
            creators.petition(state='test', ...)

        The new document is stored and the index is refreshed.
    """

    petition = partial(create_object, Petition)
    user = partial(create_object, User)
    city = partial(create_object, City)


def setUp(test):
    app = get_app()
    testapp = TestApp(app, extra_environ={'REMOTE_ADDR': '127.0.0.1'})
    test.globs['browser'] = testapp
    util.setupGlobs(test.globs, testapp, app)
    test.globs['creators'] = Creators
    test.globs['samples'] = samples


def tearDown(test):
    pass


def setUpCrate(test):
    setUp(test)
    print
    layer.delete_crate_indexes()
    layer.create_crate_indexes()


def tearDownCrate(test):
    layer.delete_crate_indexes()
    sequence.testing_reset_sequences()
    tearDown(test)


def create_suite(testfile,
                 package='iris.service',
                 layer=None,
                 level=None,
                 setUp=setUp,
                 tearDown=tearDown,
                 cls=doctest.DocFileSuite,
                 encoding='utf-8'):
    suite = cls(
        testfile,
        package=package,
        setUp=setUp,
        tearDown=tearDown,
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
        encoding=encoding)
    if layer:
        suite.layer = layer
    if level:
        suite.level = level
    return suite


def create_crate_suite(testfile, level=None):
    return create_suite(testfile,
                        layer=layer.crateDBLayer,
                        setUp=setUpCrate,
                        tearDown=tearDownCrate,
                        level=level,
                       )


def create_crate_doc_suite(testfile):
    testfile = os.path.join('../../../docs', testfile)
    return create_suite(testfile,
                        package=None,
                        layer=layer.crateDBLayer,
                        setUp=setUpCrate,
                        tearDown=tearDownCrate,
                       )
