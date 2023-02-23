from ansible.plugins.loader import PluginLoader
from ansible.template import Templar


def get_plugin():
    loader = PluginLoader(
        'LookupModule',
        'ansible.plugins.lookup',
        "./plugins/",
        "lookup",
        required_base_class='LookupBase'
    )

    lookup = loader.get("tabular")
    lookup._templar = Templar(loader=None)

    return lookup


def test_basic():
    # Arrange
    variables = {
        "hello": "world",
        "foo": "bar"
    }
    config = {
        "columns": {
            "key1": "hello",
            "key2": "foo",
            "item": "item"
        },
        "loop": [
            "a",
            "b"
        ]
    }

    # Nested list bc lookup plugins
    # have a "pipline": returns a list
    # of resutls (also receives a list of input)
    EXPECTED = [
        [
            {
                "key1": "world",
                "key2": "bar",
                "item": "a"
            },
            {
                "key1": "world",
                "key2": "bar",
                "item": "b"
            }
        ]
    ]

    lookup = get_plugin()

    # Act
    actual = lookup.run([config], variables=variables)

    # Assert
    assert actual == EXPECTED


def test_loop_var():
    # Arrange
    variables = {
        "hello": "world",
        "foo": "bar"
    }
    config = {
        "columns": {
            "key1": "hello",
            "key2": "foo",
            "item": "myvar"
        },
        "loop": [
            "a",
            "b"
        ],
        "template_control": {
            "loop_var": "myvar"
        }
    }

    # Nested list bc lookup plugins
    # have a "pipline": returns a list
    # of resutls (also receives a list of input)
    EXPECTED = [
        [
            {
                "key1": "world",
                "key2": "bar",
                "item": "a"
            },
            {
                "key1": "world",
                "key2": "bar",
                "item": "b"
            }
        ]
    ]

    lookup = get_plugin()

    # Act
    actual = lookup.run([config], variables=variables)

    # Assert
    assert actual == EXPECTED


def test_row_templating():
    # Arrange
    variables = {
        "hello": "world",
        "foo": "bar"
    }
    config = {
        "columns": {
            "key1": "hello",
            "key2": "foo",
            "item": "item.var",
            "combined": "item.key1 + item.key2"
        },
        "loop": [
            {
                "var": "a"
            },
            {
                "var": "b"
            }
        ],
        "template_control": {
            "allow_row_templating": True,
        }
    }

    # Nested list bc lookup plugins
    # have a "pipline": returns a list
    # of resutls (also receives a list of input)
    EXPECTED = [
        [
            {
                "key1": "world",
                "key2": "bar",
                "item": "a",
                "combined": "worldbar"
            },
            {
                "key1": "world",
                "key2": "bar",
                "item": "b",
                "combined": "worldbar"
            }
        ]
    ]

    lookup = get_plugin()

    # Act
    actual = lookup.run([config], variables=variables)

    # Assert
    assert actual == EXPECTED


def test_merge_with_item():
    # Arrange
    variables = {
        "hello": "world",
        "foo": "bar"
    }
    config = {
        "columns": {
            "key1": "hello",
            "key2": "foo",
        },
        "loop": [
            {
                "var": "a"
            },
            {
                "var": "b"
            }
        ],
        "template_control": {
            "merge_with_item": True,
        }
    }

    # Nested list bc lookup plugins
    # have a "pipline": returns a list
    # of resutls (also receives a list of input)
    EXPECTED = [
        [
            {
                "key1": "world",
                "key2": "bar",
                "var": "a",
            },
            {
                "key1": "world",
                "key2": "bar",
                "var": "b",
            }
        ]
    ]

    lookup = get_plugin()

    # Act
    actual = lookup.run([config], variables=variables)

    # Assert
    assert actual == EXPECTED


def test_convert_bare_false():
    # Arrange
    variables = {
        "hello": "world",
        "foo": "bar"
    }
    config = {
        "columns": {
            "key1": "hello",
            "key2": "foo",
            "item": "[[ item ]]"
        },
        "loop": [
            "a",
            "b"
        ],
        "template_control": {
            "convert_bare": False,
            "variable_start_string": "[[",
            "variable_end_string": "]]"
        }
    }

    # Nested list bc lookup plugins
    # have a "pipline": returns a list
    # of resutls (also receives a list of input)
    EXPECTED = [
        [
            {
                "key1": "hello",
                "key2": "foo",
                "item": "a"
            },
            {
                "key1": "hello",
                "key2": "foo",
                "item": "b"
            }
        ]
    ]

    lookup = get_plugin()

    # Act
    actual = lookup.run([config], variables=variables)

    # Assert
    assert actual == EXPECTED
