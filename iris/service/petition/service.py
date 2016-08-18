import transitions

from transitions.extensions.nesting import NestedState

from pyramid import security

from lovely.pyrest.rest import RestService, rpcmethod_route, rpcmethod_view

from iris.service import rest
from iris.service.rest import queries
from iris.service.security import acl

from ..errors import Errors
from ..rest.swagger import swagger_reduce_response

from .sm import PetitionStateMachine, fromYAML
from .document import Petition


@RestService("petition_admin_api",
             permission=acl.Permissions.AdminFull)
class PetitionAdminRESTService(rest.RESTService):

    MAPPER_NAME = 'petitions'


def stateFilter(value):
    if isinstance(value, (list, tuple)):
        states = [v.strip() for v in value if v.strip()]
    else:
        states = [v.lower().strip() for v in value.split(',') if v.strip()]
    if not states:
        raise ValueError("No states provided")
    filters = []
    for state in states:
        parts = state.split(NestedState.separator, 1)
        if len(parts) > 1:
            parent, name = parts
            if not name or name == '*':
                filters.append(queries.termFilter('state.parent')(parent))
            else:
                filters.append({
                    "bool": {
                        "must": [
                            queries.termFilter('state.name')(name),
                            queries.termFilter('state.parent')(parent)
                        ]
                    }
                })
        else:
            filters.append(queries.termFilter('state.name')(parts[0]))
    if len(filters) == 1:
        return filters[0]
    return {
        "bool": {
            "should": filters
        }
    }


class PetitionsRESTMapper(rest.DocumentRESTMapperMixin,
                          rest.SearchableDocumentRESTMapperMixin,
                          rest.RESTMapper):
    """A mapper for the petitions admin REST API
    """

    NAME = 'petitions'

    DOC_CLASS = Petition

    QUERY_PARAMS = {
        'ft': queries.fulltextQuery(['tags_ft',
                                     'title_ft',
                                     'description_ft',
                                     'suggested_solution_ft',
                                    ]),
        'tags_ft': queries.fulltextQuery(['tags_ft']),
        'title_ft': queries.fulltextQuery(['title_ft']),
        'description_ft': queries.fulltextQuery(['description_ft']),
        'suggested_solution_ft': queries.fulltextQuery(
            ['suggested_solution_ft']
        ),
    }

    FILTER_PARAMS = {
        'state': stateFilter,
        'tags': queries.termsFilter('tags'),
        'city': queries.termsFilter('city'),
    }

    SORT_PARAMS = {
        'created': queries.fieldSorter('dc.created'),
        'modified': queries.fieldSorter('dc.modified'),
        'id': queries.fieldSorter('id'),
        'state': queries.fieldSorter('state.name'),
        'state.parent': queries.fieldSorter('state.parent'),
        'supporters.amount': queries.fieldSorter('supporters.amount'),
        'score': queries.scoreSorter,
        'default': queries.fieldSorter('dc.created', 'DESC'),
    }

    def support(self, contentId, data):
        """Sign a petition
        """
        petition = Petition.get(contentId)
        if petition is None:
            return None
        # TODO: support the petition
        return {}

    def delete_support(self, contentId, data):
        """Sign a petition
        """
        petition = Petition.get(contentId)
        if petition is None:
            return None
        # TODO: support the petition
        return {}

    def event(self, contentId, transitionName, data=None):
        petition = Petition.get(contentId)
        if petition is None:
            return None
        sm = PetitionStateMachine(petition)
        transition_fn = getattr(sm, transitionName)
        if transition_fn is None:
            # transition doesn't exist
            raise transitions.MachineError(
                'Unknown transition "%s"' % transitionName)
        done = getattr(sm, transitionName)()
        if done:
            petition.store(refresh=True)
        return self.doc_as_dict(petition)

    def statemachine(self):
        return fromYAML(raw=True)


@RestService("petition_public_api")
class PetitionPublicRESTService(rest.RESTService):
    """Public petition endpoint

    We reuse the RESTService for the simple endpoints.

    The REST methods which should not be available must not be configured in
    swagger.
    """

    MAPPER_NAME = 'petitions'

    @rpcmethod_route(request_method='OPTIONS',
                     route_suffix='/{contentId}/support')
    @rpcmethod_view(http_cache=0,
                    permission=security.NO_PERMISSION_REQUIRED)
    def options_contentId_support(self, **kwargs):
        return {}

    @rpcmethod_route(request_method='POST',
                     route_suffix='/{contentId}/support')
    @swagger_reduce_response
    def support(self, **kwargs):
        mapper = self._getMapper(self.MAPPER_NAME)
        result = mapper.support(**self.request.swagger_data)
        if result is None:
            raise self.not_found(
                Errors.document_not_found,
                {
                    'contentId': self.request.swagger_data.get('contentId',
                                                               'missing'),
                    'mapperName': self.MAPPER_NAME
                }
            )
        return result

    @rpcmethod_route(request_method='DELETE',
                     route_suffix='/{contentId}/support')
    @swagger_reduce_response
    def delete_support(self, **kwargs):
        mapper = self._getMapper(self.MAPPER_NAME)
        result = mapper.delete_support(**self.request.swagger_data)
        if result is None:
            raise self.not_found(
                Errors.document_not_found,
                {
                    'contentId': self.request.swagger_data.get('contentId',
                                                               'missing'),
                    'mapperName': self.MAPPER_NAME
                }
            )
        return result

    @rpcmethod_route(request_method='OPTIONS',
                     route_suffix='/{contentId}/event/reject')
    @rpcmethod_view(http_cache=0,
                    permission=security.NO_PERMISSION_REQUIRED)
    def options_contentId_event(self, **kwargs):
        return {}

    @rpcmethod_route(request_method='POST',
                     route_suffix='/{contentId}/event/reject')
    @swagger_reduce_response
    def event_reject(self, **kwargs):
        return self._event('reject')

    @rpcmethod_route(request_method='OPTIONS',
                     route_suffix='/{contentId}/event/publish')
    @rpcmethod_view(http_cache=0,
                    permission=security.NO_PERMISSION_REQUIRED)
    def options_contentId_event(self, **kwargs):
        return {}

    @rpcmethod_route(request_method='POST',
                     route_suffix='/{contentId}/event/publish')
    @swagger_reduce_response
    def event_publish(self, **kwargs):
        return self._event('publish')

    @rpcmethod_route(request_method='OPTIONS',
                     route_suffix='/{contentId}/event/delete')
    @rpcmethod_view(http_cache=0,
                    permission=security.NO_PERMISSION_REQUIRED)
    def options_contentId_event(self, **kwargs):
        return {}

    @rpcmethod_route(request_method='POST',
                     route_suffix='/{contentId}/event/delete')
    @swagger_reduce_response
    def event_delete(self, **kwargs):
        return self._event('delete')

    @rpcmethod_route(request_method='OPTIONS',
                     route_suffix='/{contentId}/event/close')
    @rpcmethod_view(http_cache=0,
                    permission=security.NO_PERMISSION_REQUIRED)
    def options_contentId_event(self, **kwargs):
        return {}

    @rpcmethod_route(request_method='POST',
                     route_suffix='/{contentId}/event/close')
    @swagger_reduce_response
    def event_close(self, **kwargs):
        return self._event('close')

    @rpcmethod_route(request_method='OPTIONS',
                     route_suffix='/{contentId}/event/approved')
    @rpcmethod_view(http_cache=0,
                    permission=security.NO_PERMISSION_REQUIRED)
    def options_contentId_event(self, **kwargs):
        return {}

    @rpcmethod_route(request_method='POST',
                     route_suffix='/{contentId}/event/approved')
    @swagger_reduce_response
    def event_approved(self, **kwargs):
        return self._event('approved')

    @rpcmethod_route(request_method='OPTIONS',
                     route_suffix='/{contentId}/event/sendLetter')
    @rpcmethod_view(http_cache=0,
                    permission=security.NO_PERMISSION_REQUIRED)
    def options_contentId_event(self, **kwargs):
        return {}

    @rpcmethod_route(request_method='POST',
                     route_suffix='/{contentId}/event/sendLetter')
    @swagger_reduce_response
    def event_sendLetter(self, **kwargs):
        return self._event('sendLetter')

    @rpcmethod_route(request_method='OPTIONS',
                     route_suffix='/{contentId}/event/setFeedback')
    @rpcmethod_view(http_cache=0,
                    permission=security.NO_PERMISSION_REQUIRED)
    def options_contentId_event(self, **kwargs):
        return {}

    @rpcmethod_route(request_method='POST',
                     route_suffix='/{contentId}/event/setFeedback')
    @swagger_reduce_response
    def event_setFeedback(self, **kwargs):
        return self._event('setFeedback')

    @rpcmethod_route(request_method='POST',
                     route_suffix='/{contentId}/event/{transitionName}')
    @swagger_reduce_response
    def event_generic(self, **kwargs):
        switch = self.request.swagger_data.pop('transitionName')
        return self._event(switch)

    def _event(self, switch):
        mapper = self._getMapper(self.MAPPER_NAME)
        try:
            result = mapper.event(transitionName=switch,
                                  **self.request.swagger_data)
        except transitions.MachineError as e:
            raise self.bad_request(Errors.sm_transition_error,
                                   replacements={
                                       'text': e.value
                                   })
        if result is None:
            raise self.not_found(
                Errors.document_not_found,
                {
                    'contentId': self.request.swagger_data.get('contentId',
                                                               'missing'),
                    'mapperName': self.MAPPER_NAME
                }
            )
        return {"data": result, "status": "ok"}
