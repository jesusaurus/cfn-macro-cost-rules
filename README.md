# cfn-macro-cost-rules
A CloudFormation snippet macro for generating the Rules parameter of AWS::CE::CostCategory resources.

## Input Format
This snippet macro expects to process a snippet with one or both of two
top-level keys: `InheritedValues` and `RegularValues`.

### Inherited Values from Tags

When specifying `InheritedValues`, a `TagOrder` sub-key must be provided, and a
`RulePosition` sub-key may also be provided. The `TagOrder` sub-key must
provide a list strings corresponding to a tag name that has been configured as a
cost allocation tag. The `RulePosition` sub-key may be provided to configure
the inherited-value rules to occur either before or after regular-valued rules;
possible values are either `First` or `Last`, defaulting to `Last`.

Minimal example creating a cost category from a single tag:
```yaml
Resources:
  MyCostCategory:
    Type: AWS::CE::CostCategory
    Properties:
      Name: 'My Cost Category'
      RuleVersion: 'CostCategoryExpression.v1'
      Rules:
        Fn::Transform:
          - Name: SageCostRuleGenerator
        InheritedValues:
          TagOrder:
            - MyTagName
```

### Regular Values

When specifying `RegularValues`, a list of objects is expected where each object
has a `Value` sub-key and a combination of `Accounts`, `TagNames`, `TagEndsWith`,
and/or `TagStartsWith` sub-keys. The `Value` sub-key expects a string, and all
other sub-keys expect a list of strings.

If an element of the list only specifies `Value` and `Accounts` sub-keys, then
the resulting rule will assign all resources in the listed accounts to the cost
category value.
```yaml
Resources:
  MyCostCategory:
    Type: AWS::CE::CostCategory
    Properties:
      Name: 'My Cost Category'
      RuleVersion: 'CostCategoryExpression.v1'
      Rules:
        Fn::Transform:
          - Name: SageCostRuleGenerator
        RegularValues:
          - Value: Category A
            Accounts:
              - 12345678
              - 56781234
```

If an element of the list only specifies `Value` and `TagNames` sub-keys, then
the resulting rules will assign all resources tagged with one of the listed tag
names to the cost category value. The tag value is ignored.
```yaml
Resources:
  MyCostCategory:
    Type: AWS::CE::CostCategory
    Properties:
      Name: 'My Cost Category'
      RuleVersion: 'CostCategoryExpression.v1'
      Rules:
        Fn::Transform:
          - Name: SageCostRuleGenerator
        RegularValues:
          - Value: Category B
            TagNames:
              - MyTagOne
              - MyTagTwo
```

To match tags based on a prefix or suffix of the tag value, specify either
`TagStartsWith` or `TagEndsWith` respectively.

This example will generate a first rule to match any resources tagged with
a tag named `MyTagOne` if the tag value starts with `TagOnePrefix`; and a
second rule to match resources with a `MyTagTwo` tag with a value ending
in `:tag two suffix`; with both rules assigning matching resources to the
same cost category.
```yaml
Resources:
  MyCostCategory:
    Type: AWS::CE::CostCategory
    Properties:
      Name: 'My Cost Category'
      RuleVersion: 'CostCategoryExpression.v1'
      Rules:
        Fn::Transform:
          - Name: SageCostRuleGenerator
        RegularValues:
          - Value: Category C
            TagNames:
              - MyTagOne
           TagStartsWith:
             - TagOnePrefix
          - Value: Category C
            TagNames:
              - MyTagTwo
            TagEndsWith:
              - ':tag two suffix'
```

When combining `Accounts` and `TagNames` sub-keys, in addition to creating cost
category rules for the tag names as expected, fallback rules based on the given
accounts will be created for resources that LACK the given tags.

This example will create a rule to categorize resources if `MyTagOne` exists
and starts with `TagOnePrefix`, and another rule to categorize resources in
account `56781234` without a `MyTagOne` tag into the same category:
```yaml
Resources:
  MyCostCategory:
    Type: AWS::CE::CostCategory
    Properties:
      Name: 'My Cost Category'
      RuleVersion: 'CostCategoryExpression.v1'
      Rules:
        Fn::Transform:
          - Name: SageCostRuleGenerator
        RegularValues:
          - Value: Category D
            TagNames:
              - MyTagOne
            TagStartsWith:
              - TagOnePrefix
            Accounts:
              - 56781234
```


### Combining Regular and Inherited Values

If both `RegularValues` and `InheritedValues` keys are provided, then both sets
of rules will be generated and concatenated together. Since key order for YAML
maps is implementation dependent (i.e. no guarantee that order is preserved),
the inherited-value rules will either be prepended or appended to the
regular-value rules based on the `RulePosition` sub-key under `InheritedValues`.

```yaml
Resources:
  MyCostCategory:
    Type: AWS::CE::CostCategory
    Properties:
      Name: 'My Cost Category'
      RuleVersion: 'CostCategoryExpression.v1'
      Rules:
        Fn::Transform:
          - Name: SageCostRuleGenerator
        InheritedValues:
          TagOrder:
            - ImportantGroupTag
          RulePosition: First
        RegularValues:
          - Value: Fallback Group
            Accounts:
              - 12345678
              - 56781234
```


## Development

### Contributions
Contributions are welcome.

### Install Requirements
Run `pipenv install --dev` to install both production and development
requirements, and `pipenv shell` to activate the virtual environment. For more
information see the [pipenv docs](https://pipenv.pypa.io/en/latest/).

After activating the virtual environment, run `pre-commit install` to install
the [pre-commit](https://pre-commit.com/) git hook.

### Update Requirements
First, make any needed updates to the base requirements in `Pipfile`,
then use `pipenv` to regenerate both `Pipfile.lock` and
`requirements.txt`. We use `pipenv` to control versions in testing,
but `sam` relies on `requirements.txt` directly for building the
container used by the lambda.

```shell script
$ pipenv update
$ pipenv requirements > requirements.txt
```

Additionally, `pre-commit` manages its own requirements.
```shell script
$ pre-commit autoupdate
```

### Create a local build

```shell script
$ sam build
```

### Run unit tests
Tests are defined in the `tests` folder in this project. Use PIP to install the
[pytest](https://docs.pytest.org/en/latest/) and run unit tests.

```shell script
$ python -m pytest tests/ -vv
```

### Run integration tests
Running integration tests
[requires docker](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html)

```shell script
$ sam local invoke Function --event events/event.json
```

## Deployment

### Deploy Lambda to S3
Deployments are sent to the
[Sage cloudformation repository](https://bootstrap-awss3cloudformationbucket-19qromfd235z9.s3.amazonaws.com/index.html)
which requires permissions to upload to Sage
`bootstrap-awss3cloudformationbucket-19qromfd235z9` and
`essentials-awss3lambdaartifactsbucket-x29ftznj6pqw` buckets.

```shell script
sam package --template-file .aws-sam/build/template.yaml \
  --s3-bucket essentials-awss3lambdaartifactsbucket-x29ftznj6pqw \
  --output-template-file .aws-sam/build/lambda-template.yaml

aws s3 cp .aws-sam/build/lambda-template.yaml s3://bootstrap-awss3cloudformationbucket-19qromfd235z9/lambda-template/master/
```

## Publish Lambda

### Private access
Publishing the lambda makes it available in your AWS account.  It will be accessible in
the [serverless application repository](https://console.aws.amazon.com/serverlessrepo).

```shell script
sam publish --template .aws-sam/build/lambda-template.yaml
```

### Public access
Making the lambda publicly accessible makes it available in the
[global AWS serverless application repository](https://serverlessrepo.aws.amazon.com/applications)

```shell script
aws serverlessrepo put-application-policy \
  --application-id <lambda ARN> \
  --statements Principals=*,Actions=Deploy
```

## Install Lambda into AWS

### Sceptre
Create the following [sceptre](https://github.com/Sceptre/sceptre) file
config/prod/lambda-template.yaml

```yaml
template:
  type: http
  url: "https://PUBLISH_BUCKET.s3.amazonaws.com/lambda-template/VERSION/lambda-template.yaml"
stack_name: "lambda-template"
stack_tags:
  Department: "Platform"
  Project: "Infrastructure"
  OwnerEmail: "it@sagebase.org"
```

Install the lambda using sceptre:
```shell script
sceptre --var "profile=my-profile" --var "region=us-east-1" launch prod/lambda-template.yaml
```

### AWS Console
Steps to deploy from AWS console.

1. Login to AWS
2. Access the
[serverless application repository](https://console.aws.amazon.com/serverlessrepo)
-> Available Applications
3. Select application to install
4. Enter Application settings
5. Click Deploy

## Releasing

We have setup our CI to automate a releases.  To kick off the process just create
a tag (i.e 0.0.1) and push to the repo.  The tag must be the same number as the current
version in [template.yaml](template.yaml).  Our CI will do the work of deploying and publishing
the lambda.
