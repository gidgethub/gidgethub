:mod:`gidgethub.sansio` --- sans-I/O support
============================================

.. module:: gidgethub.sansio


Exceptions
----------

.. autoexception:: GitHubException

.. autoexception:: ValidationFailure


Functions
---------

.. function:: validate(payload: bytes, *, signature: str, secret: str) -> None

   Validate that the webhook event body came from an approved repository.

   :exc:`ValidationFailure` is raised if the provided *signature* does
   not match the calculated signature.
