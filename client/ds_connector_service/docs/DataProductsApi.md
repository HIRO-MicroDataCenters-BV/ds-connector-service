# ds_connector_service.DataProductsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_connector_metadata**](DataProductsApi.md#get_connector_metadata) | **GET** /connector-metadata | Get Connector Metadata
[**get_dataproduct_chunk**](DataProductsApi.md#get_dataproduct_chunk) | **GET** /distribution-content/{interface_id}/{resource_path}/chunk | Get Data Product Chunk
[**get_dataproduct_content**](DataProductsApi.md#get_dataproduct_content) | **GET** /distribution-content/{interface_id}/{resource_path} | Get Data Product Content
[**get_distribution_metadata**](DataProductsApi.md#get_distribution_metadata) | **GET** /distribution-metadata/{interface_id}/{resource_path} | Get Distribution Metadata
[**health_check**](DataProductsApi.md#health_check) | **GET** /interface-health/{interface_id} | Health Check
[**list_dataproduct_distributions**](DataProductsApi.md#list_dataproduct_distributions) | **GET** /dataproduct-distributions/{interface_id}/{directory_resource_path} | List Data Product Distributions
[**list_dataproducts**](DataProductsApi.md#list_dataproducts) | **GET** /dataproducts/{interface_id} | List Data Products


# **get_connector_metadata**
> ConnectorMetadata get_connector_metadata()

Get Connector Metadata

partial(func, *args, **keywords) - new function with partial application of the given arguments and keywords.

### Example


```python
import ds_connector_service
from ds_connector_service.models.connector_metadata import ConnectorMetadata
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
    except Exception as e:
        print("Exception when calling DataProductsApi->get_connector_metadata: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**ConnectorMetadata**](ConnectorMetadata.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_dataproduct_chunk**
> object get_dataproduct_chunk(interface_id, var_resource_path, range_header=range_header)

Get Data Product Chunk

Return a dataset chunk (partial CSV content).

### Example


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
    interface_id = 'interface_id_example' # str | 
    var_resource_path = 'var_resource_path_example' # str | 
    range_header = 'bytes=0-1023' # str | HTTP Range header for partial content requests (optional)

    try:
        # Get Data Product Chunk
        api_response = api_instance.get_dataproduct_chunk(interface_id, var_resource_path, range_header=range_header)
        print("The response of DataProductsApi->get_dataproduct_chunk:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->get_dataproduct_chunk: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **interface_id** | **str**|  | 
 **var_resource_path** | **str**|  | 
 **range_header** | **str**| HTTP Range header for partial content requests | [optional] 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json, text/csv

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Full chunk when no range specified |  -  |
**206** | Partial content chunk |  * Content-Range - Range of bytes returned <br>  |
**404** | Data product not found |  -  |
**416** | Range not satisfiable |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_dataproduct_content**
> object get_dataproduct_content(interface_id, var_resource_path)

Get Data Product Content

Return the full dataset content.

### Example


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
    interface_id = 'interface_id_example' # str | 
    var_resource_path = 'var_resource_path_example' # str | 

    try:
        # Get Data Product Content
        api_response = api_instance.get_dataproduct_content(interface_id, var_resource_path)
        print("The response of DataProductsApi->get_dataproduct_content:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->get_dataproduct_content: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **interface_id** | **str**|  | 
 **var_resource_path** | **str**|  | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_distribution_metadata**
> object get_distribution_metadata(interface_id, var_resource_path)

Get Distribution Metadata

Return Metadata for a distribution along with region.

### Example


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
    interface_id = 'interface_id_example' # str | 
    var_resource_path = 'var_resource_path_example' # str | 

    try:
        # Get Distribution Metadata
        api_response = api_instance.get_distribution_metadata(interface_id, var_resource_path)
        print("The response of DataProductsApi->get_distribution_metadata:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->get_distribution_metadata: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **interface_id** | **str**|  | 
 **var_resource_path** | **str**|  | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **health_check**
> object health_check(interface_id)

Health Check

Perform health check on the specified interface.

### Example


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
    interface_id = 'interface_id_example' # str | 

    try:
        # Health Check
        api_response = api_instance.health_check(interface_id)
        print("The response of DataProductsApi->health_check:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->health_check: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **interface_id** | **str**|  | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_dataproduct_distributions**
> List[DataProductItem] list_dataproduct_distributions(interface_id, directory_resource_path)

List Data Product Distributions

Return a paginated list of data product distributions with region.

### Example


```python
import ds_connector_service
from ds_connector_service.models.data_product_item import DataProductItem
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
    interface_id = 'interface_id_example' # str | 
    directory_resource_path = 'directory_resource_path_example' # str | 

    try:
        # List Data Product Distributions
        api_response = api_instance.list_dataproduct_distributions(interface_id, directory_resource_path)
        print("The response of DataProductsApi->list_dataproduct_distributions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->list_dataproduct_distributions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **interface_id** | **str**|  | 
 **directory_resource_path** | **str**|  | 

### Return type

[**List[DataProductItem]**](DataProductItem.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_dataproducts**
> List[Optional[str]] list_dataproducts(interface_id)

List Data Products

List available data products from the base path.

### Example


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
    interface_id = 'interface_id_example' # str | 

    try:
        # List Data Products
        api_response = api_instance.list_dataproducts(interface_id)
        print("The response of DataProductsApi->list_dataproducts:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->list_dataproducts: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **interface_id** | **str**|  | 

### Return type

**List[Optional[str]]**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

