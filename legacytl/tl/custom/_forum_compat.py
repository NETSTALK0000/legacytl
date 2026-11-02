"""
Layer 232 moved the forum topic methods from the `channels` namespace to `messages`
and replaced `channel` (InputChannel) with `peer` (InputPeer).

This registers the old names on `functions.channels`: calling one builds the
matching `functions.messages` request, so existing code keeps working. The
names are not TL constructors; nothing is read or written with them.
"""
from .. import functions, types

_OLD_ARGS = {
    'CreateForumTopicRequest': ('channel', 'title', 'icon_color', 'icon_emoji_id',
                                'random_id', 'send_as'),
    'DeleteTopicHistoryRequest': ('channel', 'top_msg_id'),
    'EditForumTopicRequest': ('channel', 'topic_id', 'title', 'icon_emoji_id',
                              'closed', 'hidden'),
    'GetForumTopicsByIDRequest': ('channel', 'topics'),
    'GetForumTopicsRequest': ('channel', 'offset_date', 'offset_id',
                              'offset_topic', 'limit', 'q'),
    'ReorderPinnedForumTopicsRequest': ('channel', 'order', 'force'),
    'UpdatePinnedForumTopicRequest': ('channel', 'topic_id', 'pinned'),
}


class _Meta(type):
    def __call__(cls, *args, **kwargs):
        return cls._build(*args, **kwargs)

    def __instancecheck__(cls, obj):
        return isinstance(obj, cls._target())

    def __subclasscheck__(cls, sub):
        return sub is cls or (isinstance(sub, type) and issubclass(sub, cls._target()))


def _to_peer(value):
    if isinstance(value, types.InputChannel):
        return types.InputPeerChannel(value.channel_id, value.access_hash)
    if isinstance(value, types.InputChannelFromMessage):
        return types.InputPeerChannelFromMessage(
            value.peer, value.msg_id, value.channel_id)
    if isinstance(value, types.InputChannelEmpty):
        return types.InputPeerEmpty()
    return value  # a username, id or entity: the request resolves it itself


def _install():
    for name, order in _OLD_ARGS.items():
        def build(*args, _name=name, _order=order, **kwargs):
            if len(args) > len(_order):
                raise TypeError('%s takes at most %d arguments (%d given)'
                                % (_name, len(_order), len(args)))
            for key, value in zip(_order, args):
                if key in kwargs:
                    raise TypeError('%s got multiple values for %r' % (_name, key))
                kwargs[key] = value
            if 'channel' in kwargs:
                kwargs['peer'] = _to_peer(kwargs.pop('channel'))
            return getattr(functions.messages, _name)(**kwargs)

        cls = _Meta(name, (), {
            '_build': staticmethod(build),
            '_target': staticmethod(lambda _n=name: getattr(functions.messages, _n)),
            '__doc__': 'Legacy channels.%s: builds messages.%s (layer 232).' % (name, name),
        })
        setattr(functions.channels, name, cls)


_install()
