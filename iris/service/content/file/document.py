from lovely.esdb.document import Document
from lovely.esdb.properties import Property

from iris.service.db.dc import dc_defaults, DC_CREATED, DC_MODIFIED
from .tempstorage import get_temp_upload_path


class StorageType(object):
    S3 = "s3"
    TMP = "tmp"


class File(Document):
    """A file in the database.

    This is a meta data container for the file. The file remains in an external
    storage.
    """

    INDEX = 'files'

    id = Property(primary_key=True)

    dc = Property(
        default=dc_defaults(DC_CREATED, DC_MODIFIED),
        doc="Dublin Core data."
    )

    state = Property(
        doc="The state of the file (visible/hidden)"
    )

    original_name = Property(
        doc="The original file name before upload"
    )

    owner_id = Property(
        doc="The ID of the user/session user who uploaded the file"
    )

    storage_type = Property(
        doc="""The kind of storage that has been used for the file.

        `s3` for files stored on S3, `tmp` for files stored in a temporary
        folder (used for local/testing environments).
        """
    )

    content_type = Property(
        doc="The file's guessed MIME type (e.g. `text/plain`, `image/jpeg`)"
    )

    @property
    def url(self):
        """The download URL to retrieve the file.
        """
        if self.storage_type == StorageType.S3:
            return "test"
        elif self.storage_type == StorageType.TMP:
            # for local environment or testing
            return "file://%s/%s" % (get_temp_upload_path(), self.id)
        return None

    def get_source(self):
        res = super(File, self).get_source()
        res['url'] = self.url
        return res
