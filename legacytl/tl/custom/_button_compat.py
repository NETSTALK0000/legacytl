"""
Compatibility layer for the keyboard button redesign introduced in layer 232.

Before layer 232 there was one TL constructor per button kind
(``KeyboardButtonCallback``, ``KeyboardButtonUrl``, ...). Since then there are
only two constructors, ``KeyboardInlineButton`` and ``KeyboardButton``, and the
kind of the button is stored in their ``type`` field
(``InlineButtonTypeCallback``, ``ButtonTypeRequestPhone``, ...).

To keep existing code (library internals and third party modules) working,
this module registers the old names in the ``types`` namespace:

* calling ``types.KeyboardButtonCallback(text, data)`` builds the new object;
* ``isinstance(button, types.KeyboardButtonCallback)`` checks the new object
  and its ``type``;
* attributes of the type (``button.data``, ``button.url``, ...) can be read
  directly from the button.

These names are *not* registered as TL constructors: nothing is ever read
from or written to the wire with them.
"""
from .. import types


class _Meta(type):
    def __call__(cls, *args, **kwargs):
        return cls._build(*args, **kwargs)

    def __instancecheck__(cls, obj):
        return cls._check(obj)

    def __subclasscheck__(cls, sub):
        return sub is cls


def _define(name, holder, type_cls, build):
    """Defines the legacy ``name``; ``holder`` is the real button class."""
    def check(obj, _h=holder, _t=type_cls):
        return (isinstance(obj, getattr(types, _h))
                and isinstance(getattr(obj, 'type', None), getattr(types, _t)))

    cls = _Meta(name, (), {
        '_build': staticmethod(build),
        '_check': staticmethod(check),
        '__doc__': 'Legacy name for %s with type %s (layer 232).' % (holder, type_cls),
    })
    setattr(types, name, cls)
    return cls


def _inline(text, type_):
    return types.KeyboardInlineButton(text, type_)


def _reply(text, type_):
    return types.KeyboardButton(text, type_)


def _install():
    I, R = 'KeyboardInlineButton', 'KeyboardButton'

    _define('KeyboardButtonCallback', I, 'InlineButtonTypeCallback',
            lambda text, data, requires_password=None: _inline(
                text, types.InlineButtonTypeCallback(data, requires_password)))
    _define('KeyboardButtonUrl', I, 'InlineButtonTypeUrl',
            lambda text, url: _inline(text, types.InlineButtonTypeUrl(url)))
    _define('KeyboardButtonSwitchInline', I, 'InlineButtonTypeSwitchInline',
            lambda text, query, same_peer=None, peer_types=None: _inline(
                text, types.InlineButtonTypeSwitchInline(query, same_peer, peer_types)))
    _define('KeyboardButtonBuy', I, 'InlineButtonTypeBuy',
            lambda text: _inline(text, types.InlineButtonTypeBuy()))
    _define('KeyboardButtonGame', I, 'InlineButtonTypeGame',
            lambda text: _inline(text, types.InlineButtonTypeGame()))
    _define('KeyboardButtonCopy', I, 'InlineButtonTypeCopy',
            lambda text, copy_text: _inline(text, types.InlineButtonTypeCopy(copy_text)))
    _define('KeyboardButtonWebView', I, 'InlineButtonTypeWebView',
            lambda text, url: _inline(text, types.InlineButtonTypeWebView(url)))
    _define('KeyboardButtonUserProfile', I, 'InlineButtonTypeUserProfile',
            lambda text, user_id: _inline(text, types.InlineButtonTypeUserProfile(user_id)))
    _define('KeyboardButtonUrlAuth', I, 'InlineButtonTypeUrlAuth',
            lambda text, url, button_id, fwd_text=None: _inline(
                text, types.InlineButtonTypeUrlAuth(url, button_id, fwd_text)))
    _define('InputKeyboardButtonUrlAuth', I, 'InputInlineButtonTypeUrlAuth',
            lambda text, url, bot=None, request_write_access=None, fwd_text=None: _inline(
                text, types.InputInlineButtonTypeUrlAuth(
                    url, request_write_access, fwd_text, bot)))
    _define('InputKeyboardButtonUserProfile', I, 'InputInlineButtonTypeUserProfile',
            lambda text, user_id: _inline(
                text, types.InputInlineButtonTypeUserProfile(user_id)))

    _define('KeyboardButtonRequestPhone', R, 'ButtonTypeRequestPhone',
            lambda text: _reply(text, types.ButtonTypeRequestPhone()))
    _define('KeyboardButtonRequestGeoLocation', R, 'ButtonTypeRequestGeoLocation',
            lambda text: _reply(text, types.ButtonTypeRequestGeoLocation()))
    _define('KeyboardButtonRequestPoll', R, 'ButtonTypeRequestPoll',
            lambda text, quiz=None: _reply(text, types.ButtonTypeRequestPoll(quiz)))
    _define('KeyboardButtonSimpleWebView', R, 'ButtonTypeSimpleWebView',
            lambda text, url: _reply(text, types.ButtonTypeSimpleWebView(url)))
    _define('KeyboardButtonRequestPeer', R, 'ButtonTypeRequestPeer',
            lambda text, button_id, peer_type, max_quantity: _reply(
                text, types.ButtonTypeRequestPeer(button_id, peer_type, max_quantity)))
    _define('InputKeyboardButtonRequestPeer', R, 'InputButtonTypeRequestPeer',
            lambda text, button_id, peer_type, max_quantity, name_requested=None,
            username_requested=None, photo_requested=None: _reply(
                text, types.InputButtonTypeRequestPeer(
                    button_id, peer_type, max_quantity, name_requested,
                    username_requested, photo_requested)))

    def _getattr(self, name):
        # Only reached when normal lookup fails: forward to the button type,
        # so ``button.data`` / ``button.url`` / ... keep working.
        if name == 'type' or name.startswith('_'):
            raise AttributeError(name)
        try:
            inner = object.__getattribute__(self, 'type')
        except AttributeError:
            raise AttributeError(name) from None
        try:
            return getattr(inner, name)
        except AttributeError:
            raise AttributeError(
                '%r object has no attribute %r' % (type(self).__name__, name)
            ) from None

    types.KeyboardInlineButton.__getattr__ = _getattr
    types.KeyboardButton.__getattr__ = _getattr


_install()
