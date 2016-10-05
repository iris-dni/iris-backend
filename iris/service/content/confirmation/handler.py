from iris.service import rest

from .document import Confirmation


class Handler(rest.DocumentRESTMapperMixin):

    ALLOW_API_CONFIRM = True

    def create(self, data):
        confirmation = Confirmation(handler=self.HANDLER_NAME,
                                    **data['data'])
        self._create(confirmation)
        confirmation.store(refresh=True)
        return self.to_api(confirmation)

    def confirm(self, confirmation):
        if confirmation.state == 'used':
            raise ValueError("Already used")
        if confirmation.expired:
            raise ValueError("Expired")
        self._confirm(confirmation)
        confirmation.state = 'used'
        confirmation.store(refresh=True)
        return self.to_api(confirmation)

    def _create(self, confirmation):
        pass

    def _confirm(self, confirmation):
        pass

    @classmethod
    def create_for_handler(cls, handler_name, data, request=None):
        handler = rest.RESTMapper.getMapperImplementation(
            'confirmations.' + handler_name,
            request,
        )
        return handler.create({"data": data})

    @classmethod
    def confirm_handler(cls, handler_name, token, request=None):
        handler = rest.RESTMapper.getMapperImplementation(
            'confirmations.' + handler_name,
            request,
        )
        confirmation = Confirmation.get(token)
        if confirmation is None:
            return None
        return handler.confirm(confirmation)
