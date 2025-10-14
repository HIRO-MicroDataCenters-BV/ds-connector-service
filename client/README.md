# Python client
API version: 0.1.0

## Requirements

- Python 3.10+
- Docker engine. [Documentation](https://docs.docker.com/engine/install/)

## Installation & Usage

1. If you don't have `Poetry` installed run:

```bash
pip install poetry
```

2. Install dependencies:

```bash
poetry config virtualenvs.in-project true
poetry install --no-root
```

3. Running tests:

```bash
poetry run pytest
```

You can test the application for multiple versions of Python. To do this, you need to install the required Python versions on your operating system, specify these versions in the tox.ini file, and then run the tests:
```bash
poetry run tox
```
Add the tox.ini file to `client/.openapi-generator-ignore` so that it doesn't get overwritten during client generation.

4. Building package:

```bash
poetry build
```

5. Publishing
```bash
poetry config pypi-token.pypi <pypi token>
poetry publish
```

## Client generator
To generate the client, execute the following script from the project root folder
```bash
poetry --directory server run python ./tools/client_generator/generate.py ./api/openapi.yaml
```

### Command
```bash
generate.py <file> [--asyncio]
```

#### Arguments
**file**
Specifies the input OpenAPI specification file path or URL. This argument is required for generating the Python client. The input file can be either a local file path or a URL pointing to the OpenAPI schema.

**--asyncio**
Flag to indicate whether to generate asynchronous code. If this flag is provided, the generated Python client will include asynchronous features. By default, synchronous code is generated.

#### Configuration
You can change the name of the client package in the file `/tools/client_generator/config.json`.

Add file's paths to `client/.openapi-generator-ignore` so that it doesn't get overwritten during client generation.

#### Examples

```bash
python generate.py https://<domain>/openapi.json
python generate.py https://<domain>/openapi.json --asyncio
python generate.py /<path>/openapi.yaml
python generate.py /<path>/openapi.yaml --asyncio
```

## Getting Started

Please follow the [installation procedure](#installation--usage) and then run the following:

```python

import ds_connector_service
from ds_connector_service.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = ds_connector_service.Configuration(
    host = "http://localhost"
)



# Enter a context with an instance of the API client
with ds_connector_service.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ds_connector_service.DataProductsApi(api_client)

    try:
        # Get Connector Metadata
        api_response = api_instance.get_connector_metadata()
        print("The response of DataProductsApi->get_connector_metadata:\n")
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling DataProductsApi->get_connector_metadata: %s\n" % e)

```

## Documentation for API Endpoints

All URIs are relative to *http://localhost*

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*DataProductsApi* | [**get_connector_metadata**](docs/DataProductsApi.md#get_connector_metadata) | **GET** /connector-metadata | Get Connector Metadata
*DataProductsApi* | [**get_dataproduct_chunk**](docs/DataProductsApi.md#get_dataproduct_chunk) | **GET** /distribution-content/{interface_id}/{resource_path}/chunk | Get Data Product Chunk
*DataProductsApi* | [**get_dataproduct_content**](docs/DataProductsApi.md#get_dataproduct_content) | **GET** /distribution-content/{interface_id}/{resource_path} | Get Data Product Content
*DataProductsApi* | [**get_distribution_metadata**](docs/DataProductsApi.md#get_distribution_metadata) | **GET** /distribution-metadata/{interface_id}/{resource_path} | Get Distribution Metadata
*DataProductsApi* | [**health_check**](docs/DataProductsApi.md#health_check) | **GET** /interface-health/{interface_id} | Health Check
*DataProductsApi* | [**list_dataproduct_distributions**](docs/DataProductsApi.md#list_dataproduct_distributions) | **GET** /dataproduct-distributions/{interface_id}/{directory_resource_path} | List Data Product Distributions
*DataProductsApi* | [**list_dataproducts**](docs/DataProductsApi.md#list_dataproducts) | **GET** /dataproducts/{interface_id} | List Data Products
*HealthApi* | [**service_health_check**](docs/HealthApi.md#service_health_check) | **GET** /health-check | Health check
*DefaultApi* | [**metrics_metrics_get**](docs/DefaultApi.md#metrics_metrics_get) | **GET** /metrics | Metrics


## Documentation For Models

 - [AccessRights](docs/AccessRights.md)
 - [AccessService](docs/AccessService.md)
 - [AccessUrl](docs/AccessUrl.md)
 - [ByteSize](docs/ByteSize.md)
 - [Checksum](docs/Checksum.md)
 - [CompressFormat](docs/CompressFormat.md)
 - [ConformsTo](docs/ConformsTo.md)
 - [ConnectorMetadata](docs/ConnectorMetadata.md)
 - [DataProductDistribution](docs/DataProductDistribution.md)
 - [DataProductItem](docs/DataProductItem.md)
 - [Description](docs/Description.md)
 - [DownloadUrl](docs/DownloadUrl.md)
 - [Format](docs/Format.md)
 - [HTTPValidationError](docs/HTTPValidationError.md)
 - [HasPolicy](docs/HasPolicy.md)
 - [HealthCheck](docs/HealthCheck.md)
 - [Issued](docs/Issued.md)
 - [License](docs/License.md)
 - [MediaType](docs/MediaType.md)
 - [Modified](docs/Modified.md)
 - [PackageFormat](docs/PackageFormat.md)
 - [RangeHeader](docs/RangeHeader.md)
 - [Rights](docs/Rights.md)
 - [Title](docs/Title.md)
 - [ValidationError](docs/ValidationError.md)
 - [ValidationErrorLocInner](docs/ValidationErrorLocInner.md)


<a id="documentation-for-authorization"></a>
## Documentation For Authorization

Endpoints do not require authorization.


## Author

all-hiro@hiro-microdatacenters.nl


