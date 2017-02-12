:mod:`gidgethub`
===========================

.. automodule:: gidgethub


Classes
-------

.. exception:: GitHubException

   Base exception for this library.


.. exception:: ValidationFailure

   An exception representing `failed validation of a webhook event`_.
   Inherits from :exc:`GitHubException`.


.. exception:: HTTPException(status_code: http.HTTPStatus, *args: Any)

   A general exception to represent HTTP responses. Inherits from
   :exc:`GitHubException`.


.. exception:: RedirectionException(status_code: http.HTTPStatus, *args: Any)

   Exception for 3XX HTTP responses. Inherits from :exc:`HTTPException`.


.. exception:: BadRequest(status_code: http.HTTPStatus, *args: Any)

   Exception for 4XX HTTP responses. Inherits from :exc:`HTTPException`.


.. autoclass:: InvalidField

.. autoclass:: GitHubBroken


.. _failed validation of a webhook event: https://developer.github.com/webhooks/securing/#validating-payloads-from-github
