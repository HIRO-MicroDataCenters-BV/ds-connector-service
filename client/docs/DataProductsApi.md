# ds_connector_service.DataProductsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_connector_metadata**](DataProductsApi.md#get_connector_metadata) | **GET** /connector-metadata | Get Connector Metadata
[**get_dataproduct_chunk**](DataProductsApi.md#get_dataproduct_chunk) | **GET** /distribution-content/{interface_id}/{resource_path}/chunk | Get Data Product Chunk
[**get_dataproduct_content**](DataProductsApi.md#get_dataproduct_content) | **GET** /distribution-content/{interface_id}/{resource_path} | Get Data Product Content
[**get_distribution_metadata**](DataProductsApi.md#get_distribution_metadata) | **GET** /distribution-metadata/{interface_id}/{resource_path} | Get Distribution Metadata
[**list_dataproduct_distributions**](DataProductsApi.md#list_dataproduct_distributions) | **GET** /dataproduct-distributions/{interface_id}/{directory_resource_path} | List Data Product Distributions
[**list_dataproducts**](DataProductsApi.md#list_dataproducts) | **GET** /dataproducts/{interface_id} | List Data Products
[**stream_upload_dataproduct**](DataProductsApi.md#stream_upload_dataproduct) | **POST** /distribution-stream-upload/{interface_id}/{resource_path} | Stream Upload Data Product
[**upload_dataproduct**](DataProductsApi.md#upload_dataproduct) | **POST** /distribution-upload/{interface_id}/{resource_path} | Upload Data Product


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
    range_header = ds_connector_service.RangeHeader() # RangeHeader | HTTP Range header for partial content requests (optional)

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
 **range_header** | [**RangeHeader**](.md)| HTTP Range header for partial content requests | [optional] 

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
> List[str] list_dataproducts(interface_id)

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

**List[str]**

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

# **stream_upload_dataproduct**
> UploadResponse stream_upload_dataproduct(interface_id, var_resource_path, file=file, content_type=content_type, tags=tags)

Stream Upload Data Product

Upload a data product using streaming (memory-efficient for large files/data)  Supports two streaming methods: 1. Multipart file streaming: Stream file chunks 2. Direct content streaming: Stream JSON/text data from request body  Args:     request: FastAPI request object     interface_id: Storage interface (file, s3)     resource_path: Path where to store the data     file: File to stream upload (for multipart uploads only)     content_type: Optional content type override (for multipart uploads)     tags: Optional tags     usecases: Write use case dependency  Returns:     Upload result information

### Example


```python
import ds_connector_service
from ds_connector_service.models.content_type import ContentType
from ds_connector_service.models.file import File
from ds_connector_service.models.tags import Tags
from ds_connector_service.models.upload_response import UploadResponse
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
    file = '/path/to/file' # File |  (optional)
    content_type = ds_connector_service.ContentType() # ContentType |  (optional)
    tags = ds_connector_service.Tags() # Tags |  (optional)

    try:
        # Stream Upload Data Product
        api_response = api_instance.stream_upload_dataproduct(interface_id, var_resource_path, file=file, content_type=content_type, tags=tags)
        print("The response of DataProductsApi->stream_upload_dataproduct:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->stream_upload_dataproduct: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **interface_id** | **str**|  | 
 **var_resource_path** | **str**|  | 
 **file** | [**File**](File.md)|  | [optional] 
 **content_type** | [**ContentType**](ContentType.md)|  | [optional] 
 **tags** | [**Tags**](Tags.md)|  | [optional] 

### Return type

[**UploadResponse**](UploadResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **upload_dataproduct**
> UploadResponse upload_dataproduct(interface_id, var_resource_path, file=file, content_type=content_type, tags=tags)

Upload Data Product

Upload a complete data product file or JSON data  Supports two upload methods: 1. Multipart file upload: Use form-data with file field 2. Direct JSON/data upload: Send JSON/text directly in request body  Args:     request: FastAPI request object     interface_id: Storage interface (file, s3)     resource_path: Path where to store the data     file: File to upload (for multipart uploads only)     content_type: Optional content type override (for multipart uploads)     tags: Optional tags in format \"key=value,key2=value2\"     usecases: Write use case dependency  Returns:     Upload result information

### Example


```python
import ds_connector_service
from ds_connector_service.models.content_type import ContentType
from ds_connector_service.models.file1 import File1
from ds_connector_service.models.tags1 import Tags1
from ds_connector_service.models.upload_response import UploadResponse
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
    file = ds_connector_service.File1() # File1 |  (optional)
    content_type = ds_connector_service.ContentType() # ContentType |  (optional)
    tags = ds_connector_service.Tags1() # Tags1 |  (optional)

    try:
        # Upload Data Product
        api_response = api_instance.upload_dataproduct(interface_id, var_resource_path, file=file, content_type=content_type, tags=tags)
        print("The response of DataProductsApi->upload_dataproduct:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->upload_dataproduct: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **interface_id** | **str**|  | 
 **var_resource_path** | **str**|  | 
 **file** | [**File1**](File1.md)|  | [optional] 
 **content_type** | [**ContentType**](ContentType.md)|  | [optional] 
 **tags** | [**Tags1**](Tags1.md)|  | [optional] 

### Return type

[**UploadResponse**](UploadResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

