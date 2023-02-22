# Ansible Collection - ehharvey.data
This colletion contains plugins (currently 1 plugin) that assists in data manipulation.

# Contribution and Collaboration
I welcome contribution and collaboration. If you can, please file an Issue before submitting a PR.

Note that I use ansible-test features (unit, integration and "sanity"/smoke tests).

# Plugins and Modules
## Lookup Plugins
### tabular
`tabular` is a plugin that creates table-like data using a dictionary configuration and templating. This dictionary contains:
* `columns`: a dictionary containing the columns to create (keys) and their values. The values are templated every "row"
* `loop`: An iterable (e.g., list or dict) that is used to generate the table. By default, the iterable can be accessible
          via the `item` variable, which you can provide inside `columns`
* `template_control`: Optional configuration parameters

Here is an example:
```
- name: Basic test
  ansible.builtin.debug:
    msg: "{{ test_passed | ternary('Passed', 'Failed') }}"
  vars:
    hello: world
    foo: bar
    table:
      columns:
        var1: hello
        var2: foo
        item: item
      loop:
        - a
        - b
    actual: "{{ lookup('ehharvey.data.tabular', table) }}"
    expected:
      - var1: world
        var2: bar
        item: a
      - var1: world
        var2: bar
        item: b
    test_passed: "{{ actual == expected }}"
  failed_when: actual != expected
```


Since Ansible is eager to template data before passing them to the lookup plugin, by default you should not provide the braces
"{{" or "}}". However, the templating tokens are configurable if you prefer:
```
- name: Basic test with [[ and ]] tokens
  ansible.builtin.debug:
    msg: "{{ test_passed | ternary('Passed', 'Failed') }}"
  vars:
    hello: world
    foo: bar
    table:
      columns:
        var1: "[[ hello ]]"
        var2: "[[ foo ]]"
        item: "[[ item ]]"
      loop:
        - a
        - b
      template_control:
        convert_bare: no
        variable_start_string: "[["
        variable_end_string: "]]"
    actual: "{{ lookup('ehharvey.data.tabular', table) }}"
    expected:
      - var1: world
        var2: bar
        item: a
      - var1: world
        var2: bar
        item: b
    test_passed: "{{ actual == expected }}"
  failed_when: actual != expected
```


`tabular` is modelled after approaches that I've (Emil) seen online that use `set_fact` and `loop` (or `with_items`) to generate
table-like data. These approaches typically follow this pattern:
1. Use `set_fact` to store the final result
2. Use a combination method (`combine` filter or `+`) that takes the old fact and combines it with a new data item
3. Use a `loop` that provides new data items


I believe this approach to be an anti-pattern for the following reasons:
* It is slow: looping causes Ansible to perform many serializations and deserializations of your data
* If you have more than 1 host in the play, then you introduce race conditions unless you `throttle`
* You often have to delegate the task
* You must store the resulting data on some host, usually localhost


This plugin addresses these issues by creating the table inside a single lookup plugin. Furthermore:
* The configuration to build the table can exist anywhere (in your playbook, in your inventory, etc.)
* You can create a table per host
* You still retain the ability to use other plugins