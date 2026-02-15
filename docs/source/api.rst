API
===

############
UML Diagrams
############

Class diagram (inheritance) and dependence structure. The latter has partial errors, as every gamemode.[...] imports the GameImage class. 

The diagrams are automatically generated using the Sphinx-Pyreverse_ plugin. If they are not readable in the PDF version of this documentation (too small), see the `docs/source/uml_images` directory for the full resolution images.

.. _Sphinx-Pyreverse: https://sphinx-pyreverse.github.io/sphinx-pyreverse


.. uml:: Game
    :classes:
    :packages:

#################
Game Module's API
#################

.. autosummary::
    :toctree: _autosummary
    :template: custom-module-template.rst
    :recursive:

    Game