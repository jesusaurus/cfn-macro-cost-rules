import json

import pytest

from cost_rules import app


def test_inherited_rules():
    '''Test inherited_rules()'''
    one_tag = [ 'One', ]

    expected = [{
        'Type': 'INHERITED_VALUE',
        'InheritedValue': {
            'DimensionName': 'TAG',
            'DimensionKey': 'One',
        }
    },]

    result = app.inherited_rules(one_tag)
    assert expected == result

def test_account_rules_without_tags():
    '''Test account_rule() without specifying tags'''
    label = 'Category Name'
    accounts = [ 'abc123', '456xyz' ]

    expected = {
        'Type': 'REGULAR',
        'Value': 'Category Name',
        'Rule': {
            'Dimensions': {
                'Key': 'LINKED_ACCOUNT',
                'Values': [ 'abc123', '456xyz' ],
                'MatchOptions': [ 'EQUALS', ],
            }
        }
    }

    result = app.account_rule(label, accounts)
    assert expected == result

def test_account_rules_with_tags():
    '''Test account_rule() with specifying tags'''
    label = 'Category Name'
    accounts = [ 'abc123', '456xyz' ]
    tags = [ 'One', 'Two' ]

    expected = {
        'Type': 'REGULAR',
        'Value': 'Category Name',
        'Rule': {
            'And': [
                {
                    'Dimensions': {
                        'Key': 'LINKED_ACCOUNT',
                        'Values': [ 'abc123', '456xyz' ],
                        'MatchOptions': [ 'EQUALS', ],
                    }
                },
                {
                    'Tags': {
                        'Key': 'One',
                        'MatchOptions': [ 'ABSENT', ],
                    }
                },
                {
                    'Tags': {
                        'Key': 'Two',
                        'MatchOptions': [ 'ABSENT', ],
                    }
                },
            ]
        }
    }

    result = app.account_rule(label, accounts, tags)
    assert expected == result

def test_tag_rules():
    '''Test tag_end_rules()'''
    label = 'Category Name'
    tags = [ 'One', 'Two' ]
    search = [ 'Suffix', ]

    for match in [ 'ENDS_WITH', 'STARTS_WITH' ]:
        expected = [
            {
                'Type': 'REGULAR',
                'Value': 'Category Name',
                'Rule': {
                    'Tags': {
                        'Key': 'One',
                        'Values': [ 'Suffix', ],
                        'MatchOptions': [ match, ],
                    }
                }
            },
            {
                'Type': 'REGULAR',
                'Value': 'Category Name',
                'Rule': {
                    'Tags': {
                        'Key': 'Two',
                        'Values': [ 'Suffix', ],
                        'MatchOptions': [ match, ],
                    }
                }
            },
        ]

        result = app.tag_rules(label, tags, search, match)
        assert expected == result

def test_inherit():
    '''Test rule_generator() with only inherited values'''
    fragment = {
        'InheritedValues': {
            'TagOrder': [ 'One', 'Two' ]
        },
    }

    expected = [
        {
            'Type': 'INHERITED_VALUE',
            'InheritedValue': {
                'DimensionName': 'TAG',
                'DimensionKey': 'One',
            }
        },
        {
            'Type': 'INHERITED_VALUE',
            'InheritedValue': {
                'DimensionName': 'TAG',
                'DimensionKey': 'Two',
            }
        },
    ]

    _test_generator_and_handler(fragment, expected)


def test_regular():
    '''Test rule_generator() with only regular values'''
    fragment = {
        'RegularValues': [
            {
                'Value': 'Category Foo',
                'TagNames': [ 'One', 'Two' ],
                'TagEndsWith': [ 'FooSuffix', ],
            },
            {
                'Value': 'Category Foo',
                'Accounts': [ 'abc123', ],
            },
        ],
    }

    expected = [
        {
            'Type': 'REGULAR',
            'Value': 'Category Foo',
            'Rule': {
                'Tags': {
                    'Key': 'One',
                    'Values': [ 'FooSuffix', ],
                    'MatchOptions': [ 'ENDS_WITH', ],
                }
            }
        },
        {
            'Type': 'REGULAR',
            'Value': 'Category Foo',
            'Rule': {
                'Tags': {
                    'Key': 'Two',
                    'Values': [ 'FooSuffix', ],
                    'MatchOptions': [ 'ENDS_WITH', ],
                }
            }
        },
        {
            'Type': 'REGULAR',
            'Value': 'Category Foo',
            'Rule': {
                'Dimensions': {
                    'Key': 'LINKED_ACCOUNT',
                    'Values': [ 'abc123', ],
                    'MatchOptions': [ 'EQUALS', ],
                }
            }
        },
    ]

    _test_generator_and_handler(fragment, expected)


def test_complex():
    '''Test rule_generator() with a more complex configuration'''
    fragment = {
        'InheritedValues': {
            'TagOrder': [ 'One', 'Two' ],
            'RulePosition': 'First',
        },
        'RegularValues': [
            {
                'Value': 'Category Foo',
                'TagNames': [ 'Foo', ],
                'TagEndsWith': [ 'FooSuffix', ],
                'Accounts': [ 'abc123', ],
            },
            {
                'Value': 'Category Bar',
                'Accounts': [ '456xyz', 'xyz456' ],
                'TagNames': [ 'Foo' ],
            },
        ],
    }

    expected = [
        {
            'Type': 'INHERITED_VALUE',
            'InheritedValue': {
                'DimensionName': 'TAG',
                'DimensionKey': 'One',
            }
        },
        {
            'Type': 'INHERITED_VALUE',
            'InheritedValue': {
                'DimensionName': 'TAG',
                'DimensionKey': 'Two',
            }
        },
        {
            'Type': 'REGULAR',
            'Value': 'Category Foo',
            'Rule': {
                'Tags': {
                    'Key': 'Foo',
                    'Values': [ 'FooSuffix', ],
                    'MatchOptions': [ 'ENDS_WITH', ],
                }
            }
        },
        {
            'Type': 'REGULAR',
            'Value': 'Category Foo',
            'Rule': {
                'And': [
                    {
                        'Dimensions': {
                            'Key': 'LINKED_ACCOUNT',
                            'Values': [ 'abc123', ],
                            'MatchOptions': [ 'EQUALS', ],
                        }
                    },
                    {
                        'Tags': {
                            'Key': 'Foo',
                            'MatchOptions': [ 'ABSENT', ],
                        }
                    },
                ]
            }
        },
        {
            'Type': 'REGULAR',
            'Value': 'Category Bar',
            'Rule': {
                'And': [
                    {
                        'Dimensions': {
                            'Key': 'LINKED_ACCOUNT',
                            'Values': [ '456xyz', 'xyz456' ],
                            'MatchOptions': [ 'EQUALS', ],
                        }
                    },
                    {
                        'Tags': {
                            'Key': 'Foo',
                            'MatchOptions': [ 'ABSENT', ],
                        }
                    },
                ]
            }
        },
    ]

    _test_generator_and_handler(fragment, expected)

def test_no_keys():
    fragment = {}
    exc = KeyError

    _test_generator_and_handler_exc(fragment, exc)

def test_no_tag_order():
    fragment = {
        'InheritedValues': {
            'Invalid': 'invalid'
        },
    }
    exc = KeyError

    _test_generator_and_handler_exc(fragment, exc)

def test_no_tag_value():
    fragment = {
        'RegularValues': [
            {
                'Accounts': [ 'abc123', ],
            },
        ],
    }
    exc = KeyError

    _test_generator_and_handler_exc(fragment, exc)

def _test_generator_and_handler(fragment, expected):
    result = app.rule_generator(fragment)
    assert expected == result

    event = {
        'fragment': fragment,
        'requestId': 'test',
    }
    result = app.handler(event, None)
    assert result['status'] == 'success'
    assert json.dumps(expected) == result['fragment']

def _test_generator_and_handler_exc(fragment, exc):
    with pytest.raises(exc):
        result = app.rule_generator(fragment)

    event = {
        'fragment': fragment,
        'requestId': 'test',
    }
    result = app.handler(event, None)
    assert result['status'] == 'failed'
