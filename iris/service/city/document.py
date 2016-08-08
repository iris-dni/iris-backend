from lovely.esdb.document import Document
from lovely.esdb.properties import Property

from ..db.dc import dc_defaults, DC_CREATED, DC_MODIFIED


class City(Document):

    INDEX = 'cities'

    def __init__(self, **kwargs):
        if kwargs:
            # Some kind of a hack but currently the only way to detect if the
            # instance is created from the database or instantiated by our
            # code.
            if 'id' not in kwargs:
                raise ValueError('City.__init__ is missing id')
            if 'provider' not in kwargs:
                raise ValueError('City.__init__ is missing provider')
            kwargs['id'] = self.buildPrimaryKey(kwargs['id'],
                                                kwargs['provider'])
        super(City, self).__init__(**kwargs)

    id = Property(
        primary_key=True,
        doc="""
        There is no autogenerated id because the cities are always imported
        from external sources which must provide an id.
        Anyway the importer prefixes the city ids with the provider name.
        """
    )

    dc = Property(
        default=dc_defaults(DC_CREATED, DC_MODIFIED),
        doc="Dublin Core data."
    )

    state = Property(
        default='active',
        doc="""
          The current state of the user.
        """
    )

    name = Property(
        default=''
    )

    tags = Property(
        default=lambda: [],
        doc="""
          A list of tags which are searchable.
        """,
    )

    zips = Property(
        default=lambda: [],
        doc="""
          A list of zips.
        """,
    )

    treshold = Property(
        default=0,
        doc="""
          The treshold for the petitions on this city.
        """,
    )

    contact = Property(
        default=lambda: {},
        doc="""
          An object which contains contact information.
        """
    )

    provider = Property(
        doc="""
        The provider which created the city.
        """
    )

    @classmethod
    def buildPrimaryKey(cls, id, provider):
        """Create the primary key

        The primary key of a city is created from an external id and the
        provider name.
        """
        return provider + ':' + str(id)

    def __repr__(self):
        return "<%s [id=%r, %r]>" % (self.__class__.__name__,
                                     self.id,
                                     self.name)
