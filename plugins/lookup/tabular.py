# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = """
    name: tabular
    author: Emil Harvey (@ehharvey) <emil.h.harvey@outlook.com>
    version_added: "0.0.1"
    short_description: Generates tabular data using templating.
    description: >-
      Generates tabular data based on iterable input. Receives a dict config
      that contains columns (tabular), an iterable (loop), and optional
      configuration options (template_control).

      This plugin requires pydantic to be installed
    options:
      _terms:
        description: list of Options to template
"""

EXAMPLES = """
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

- name: All options set
  ansible.builtin.debug:
    msg: "{{ test_passed | ternary('Passed', 'Failed') }}"
  vars:
    hello: world
    foo: bar
    table:
      columns:
        var1: "[[ hello ]]"
        var2: "[[ foo ]]"
        combined: "[[ itemvar.var1 + itemvar.var2 ]]"
      loop:
        - myvar: abc
        - myvar: def
      template_control:
        loop_var: itemvar
        merge_with_item: yes
        allow_row_templating: yes
        convert_bare: no
        variable_start_string: "[["
        variable_end_string: "]]"
    actual: "{{ lookup('ehharvey.data.tabular', table) }}"
    expected:
      - var2: bar
        var1: world
        combined: worldbar
        myvar: abc
      - var2: bar
        var1: world
        combined: worldbar
        myvar: def
    test_passed: "{{ actual == expected }}"
  failed_when: actual != expected

- name: Test interop with builtin filter plugins
  ansible.builtin.debug:
    msg: "{{ test_passed | ternary('Passed', 'Failed') }}"
  vars:
    hello: world
    foo: BAR
    table:
      columns:
        var1: hello | upper
        var2: foo | lower
        item: item | reject("equalto", "bad") | join(" ")
      loop:
        - ["good", "bad", "good"]
        - ["the", "quick", "brown", "fox"]
    actual: "{{ lookup('ehharvey.data.tabular', table) }}"
    expected:
      - var1: WORLD
        var2: bar
        item: "good good"
      - var1: WORLD
        var2: bar
        item: "the quick brown fox"
    test_passed: "{{ actual == expected }}"
  failed_when: actual != expected
"""


from typing import Any, Dict, List, Mapping
from copy import deepcopy
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from ansible.template import Templar
from ansible.errors import AnsibleAssertionError, AnsibleError


RETURN = """
_raw:
   description: tabular data (list of dictionaries per table)
   type: list
   elements: list
"""

try:
    from pydantic import BaseModel
    HAS_PYDANTIC = True

    class TemplateControl(BaseModel):
        loop_var: str = "item"

        # If any are true
        # items in Option.loop MUST BE A DICTIONARY
        # (Option.loop is a List[Dict[str, Any]])
        merge_with_item: bool = False
        allow_row_templating = False

        convert_bare = True

        # If convert_bare is false, set these to sensible (non {{ }} values)
        variable_start_string = "{{"
        variable_end_string = "}}"

    class Option(BaseModel):
        columns: Dict[str, Any]
        loop: List[Any]
        template_control: TemplateControl = TemplateControl()

    def create_row(
        columns: Dict[str, Any],
        item: Any,
        variables: dict,
        template_control: TemplateControl,
            templar: Templar):

        row = {}

        vars = deepcopy(variables)

        for key, value in columns.items():
            vars.update({template_control.loop_var: item})

            with templar.set_temporary_context(
                variable_start_string=template_control.variable_start_string,
                variable_end_string=template_control.variable_end_string,
                available_variables=vars
            ):
                row[key] = templar.template(
                    value,
                    convert_bare=template_control.convert_bare
                )

            if template_control.merge_with_item:
                if not (isinstance(item, Mapping)):
                    raise AnsibleAssertionError(
                        "Items in loop must be dict if merge_with_item is true"
                    )

                row.update(item)

            if template_control.allow_row_templating:
                if not (isinstance(item, dict)):
                    raise AnsibleAssertionError(
                        ("Items in loop must be dicts if allow_row_templating "
                            "is true")
                    )

                item.update(row)

        return row

    def create_table(term: Option, variables: dict, templar: Templar):
        term = Option(**term)

        return [
            create_row(
                term.columns,
                item,
                variables,
                term.template_control,
                templar
            )

            for item in term.loop
        ]
except ModuleNotFoundError as e:
    HAS_PYDANTIC = False


display = Display()


class LookupModule(LookupBase):

    def run(self, terms: List[dict], variables: dict, **kwargs) -> List[dict]:
        if not HAS_PYDANTIC:
            raise AnsibleAssertionError("pydantic module is required")

        ret: List[dict] = []

        # self.set_options(var_options=variables, direct=kwargs)

        if self._templar is None:
            raise AnsibleAssertionError("templar could not be accessed")

        templar: Templar = self._templar

        return [
            create_table(term, variables, templar)

            for term in terms
        ]
