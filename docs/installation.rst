Installation
============

You can install the package using ``uv``, which is the recommended modern approach for fast, reliable dependency management. Alternatively, you can use ``pip`` for legacy support.

Using UV (Recommended)
--------------------------

To install the package into your current environment using ``uv``, run:

.. code-block:: bash

   uv pip install package-name

If you want to create a new project and add the package as a dependency, use:

.. code-block:: bash

   uv add package-name

Legacy Installation (pip)
-------------------------

If you prefer or require the traditional approach, you can install the package using ``pip``.

.. warning::
   Using ``uv`` is recommended for significantly faster resolution and installation. If you use ``pip``, ensure your environment is properly activated.

To install using ``pip``:

.. code-block:: bash

   pip install package-name

For development environments, you may also use:

.. code-block:: bash

   pip install -e .
