"""Basic import tests to ensure package is installable."""


def test_can_import_package():
    import hyper_cmd

    assert hyper_cmd.__version__ == "0.1.0"


def test_can_import_main_classes():
    from hyper_cmd import BaseCommand, BaseWidget, SimpleContainer
    from hyper_cmd.plugins import plugin_registry

    assert BaseCommand is not None
    assert SimpleContainer is not None
    assert BaseWidget is not None
    assert plugin_registry is not None
