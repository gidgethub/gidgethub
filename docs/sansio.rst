:mod:`gidgethub.sansio` --- sans-I/O support
============================================

.. module:: gidgethub.sansio


Functions
---------

.. function:: validate(payload: bytes, *, signature: str, secret: str) -> None

   `Validate <https://developer.github.com/webhooks/securing/#validating-payloads-from-github>`_
   that the webhook event body came from an approved repository.

   :exc:`gidgethub.exceptions.ValidationFailure` is raised if the provided
   *signature* does not match the calculated signature.


Classes
-------

.. class:: Event(data: JSONDict, *, event: str, delivery_id: str)

   A representation of a
   `webhook event <https://developer.github.com/webhooks/#events>`_.
