import json
import logging

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

def tag_rules(label, tags, search, match):
    '''
        Example JSON for two tags:

      [{
        "Type": "REGULAR",
        "Value": "BMGF Ki",
        "Rule": {
          "Tags": {
            "Key": "CostCenter",
            "Values": [
              "30144"
            ],
            "MatchOptions": [
              "ENDS_WITH"
            ]
          }
        }
      },
      {
        "Type": "REGULAR",
        "Value": "BMGF Ki",
        "Rule": {
          "Tags": {
            "Key": "CostCenterOther",
            "Values": [
              "30144"
            ],
            "MatchOptions": [
              "ENDS_WITH"
            ]
          }
        }
      }]
    '''

    valid = [ 'ENDS_WITH', 'STARTS_WITH' ]
    if match not in valid:
        raise ValueError(f'Valid tag match values: {valid} ; found: {match}')


    def _build_tag(key, values):
        tag = {}
        tag['Key'] = key
        tag['Values'] = values
        tag['MatchOptions'] = [ match, ]
        return tag

    rules = []

    for t in tags:
        rule = {}
        rule['Type'] = 'REGULAR'
        rule['Value'] = label
        rule['Rule'] = {
            'Tags': _build_tag(t, search)
        }
        rules.append(rule)

    return rules

def account_rule(label, accounts, tags=None):
    '''
        Example JSON with tags:

      {
        "Type": "REGULAR",
        "Value": "Platform Infrastructure",
        "Rule": {
          "And": [
            {
              "Dimensions": {
                "Key": "LINKED_ACCOUNT",
                "Values": [
                  "420786776710",
                  "745159704268",
                  "325565585839"
                ],
                "MatchOptions": [
                  "EQUALS"
                ]
              }
            },
            {
              "Tags": {
                "Key": "CostCenter",
                "MatchOptions": [
                  "ABSENT"
                ]
              }
            },
            {
              "Tags": {
                "Key": "CostCenterOther",
                "MatchOptions": [
                  "ABSENT"
                ]
              }
            }
          ]
        }
      }

        Example JSON without tags:

      {
        "Type": "REGULAR",
        "Value": "BMGF Ki",
        "Rule": {
          "Dimensions": {
            "Key": "LINKED_ACCOUNT",
            "Values": [
              "464102568320"
            ],
            "MatchOptions": [
              "EQUALS"
            ]
          }
        }
      }

    '''
    rule = {
        'Type': 'REGULAR',
        'Value': label,
    }

    _accounts = {
        'Dimensions': {
            'Key': 'LINKED_ACCOUNT',
            'Values': accounts,
            'MatchOptions': [ 'EQUALS', ],
        }
    }

    def _build_tag_absent(key):
        tag = {}
        tag['Key'] = key
        tag['MatchOptions'] = [ 'ABSENT', ]
        return {'Tags': tag}

    _rule = {}
    if tags:
        _tags = [ _build_tag_absent(t) for t in tags ]
        rule['Rule'] = { 'And': [ _accounts, ] + _tags }

    else:
        rule['Rule'] = _accounts

    return rule


def inherited_rules(tags):
    '''
    Fall back on directly using tag values
    Example JSON


  [{
    "Type": "INHERITED_VALUE",
    "InheritedValue": {
      "DimensionName": "TAG",
      "DimensionKey": "CostCenterOther"
    }
  },
  {
    "Type": "INHERITED_VALUE",
    "InheritedValue": {
      "DimensionName": "TAG",
      "DimensionKey": "CostCenter"
    }
  }]
    '''
    rules = []

    for t in tags:
        rule = {
            'Type': 'INHERITED_VALUE',
            'InheritedValue': {
                'DimensionName': 'TAG',
                'DimensionKey': t,
            }
        }
        rules.append(rule)

    return rules

def rule_generator(params):
    '''
        Input:

        InheritedValues:
          TagOrder:
            - CostCenterOther
            - CostCenter
          RulePosition: Last
        RegularValues:
          - Value: Category One
            Accounts:
              - 123abc
              - 456xyz
            TagNames:
              - CostCenter
              - CostCenterOther
            TagEndsWith:
              - 123400
          - Value: Category Two
            ...
    '''
    # Rule order matters, first match wins and rules should
    # generally be ordered most-common to least-common
    rules = []

    # Ensure one of `InheritedValues` or `RegularValues` is set
    if not ( ('InheritedValues' in params) or ('RegularValues' in params) ):
        raise KeyError("Either a 'InheritedValues' or 'RegularValues' key must be present")

    # First get the inherited tag info
    it_position = 'Last'  # either 'First' or 'Last'
    it_rules = []
    if 'InheritedValues' in params:
        info = params['InheritedValues']

        if 'RulePosition' in info:
            it_position = info['RulePosition']

        if 'TagOrder' in info:
            order = info['TagOrder']
            it_rules = inherited_rules(order)
        else:
            raise KeyError("'InheritedValues' key must have a 'TagOrder' sub-key")

    # add our inherited tag rules if their position is First
    if it_rules and it_position == 'First':
        rules.extend(it_rules)

    # iterate over our labels, building the rules for each
    if 'RegularValues' in params:
        for info in params['RegularValues']:

            # Ensure that a categorp value is given
            if 'Value' not in info:
                raise KeyError("'RegularValues' element must have a 'Value' key")

            # First add tag suffix rules
            tags = None
            if 'TagNames' in info:
                tags = info['TagNames']
                if 'TagEndsWith' in info:
                    rules.extend(tag_rules(info['Value'], tags, info['TagEndsWith'], 'ENDS_WITH'))
                if 'TagStartsWith' in info:
                    rules.extend(tag_rules(info['Value'], tags, info['TagStartsWith'], 'STARTS_WITH'))

            # Then add an account rule
            if 'Accounts' in info:
                rules.append(account_rule(info['Value'], info['Accounts'], tags))

    # add our inherited tag rules if their position is Last
    if it_rules and it_position == 'Last':
        rules.extend(it_rules)

    return rules

def handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        Macro Input Format
        https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-macros.html

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
        Macro Output Format
        https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-macros.html
    """

    out = {
        'requestId': None,
        'status': None,
        'fragment': None
    }

    try:
        fragment = event['fragment']
        out['requestId'] = event['requestId']
        rules = rule_generator(fragment)
        out['fragment'] = json.dumps(rules)
        out['status'] = 'success'
        LOG.info(f"Output size: {len(out['fragment'])}")
        LOG.info(out['fragment'])

    except Exception as e:
        out['status'] = 'failed'
        out['errorMessage'] = str(e)

    return out
