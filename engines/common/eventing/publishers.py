from engines.common.eventing.bus import publish
from engines.common.eventing.event import EventType, RoleProgressEvent,RoleResultEvent,RoleErrorEvent


def pub_role_progress(data: RoleProgressEvent):
    publish(event_type=EventType.ROLE_PROGRESS, data=data.model_dump())


def pub_role_result(data:RoleResultEvent):
    publish(event_type=EventType.ROLE_RESULT, data=data.model_dump())



def pub_role_error(data:RoleErrorEvent):
    publish(event_type=EventType.ROLE_ERROR, data=data.model_dump())
