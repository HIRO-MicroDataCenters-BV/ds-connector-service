# template_web_client.DataProductsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_data_product**](DataProductsApi.md#create_data_product) | **POST** /data-products/ | Create Data Product
[**delete_data_product**](DataProductsApi.md#delete_data_product) | **DELETE** /data-products/{connector_id}/{data_product_id}/ | Delete Data Product
[**get_data_product**](DataProductsApi.md#get_data_product) | **GET** /data-products/{connector_id}/{data_product_id}/ | Get Data Product
[**get_data_product_content**](DataProductsApi.md#get_data_product_content) | **GET** /data-products/{connector_id}/{data_product_id}/content | Get Data Product Content
[**list_data_products**](DataProductsApi.md#list_data_products) | **GET** /data-products/ | List Data Products


# **create_data_product**
> object create_data_product(body)

Create Data Product

Register a new data product (metadata only)

### Example


```python
import template_web_client
from template_web_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = template_web_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with template_web_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = template_web_client.DataProductsApi(api_client)
    body = None # object | 

    try:
        # Create Data Product
        api_response = api_instance.create_data_product(body)
        print("The response of DataProductsApi->create_data_product:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->create_data_product: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | **object**|  | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**201** | Data product created successfully |  -  |
**400** | Invalid input |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_data_product**
> object delete_data_product(connector_id, data_product_id)

Delete Data Product

Delete a data product (delegated to the underlying Interface)

### Example


```python
import template_web_client
from template_web_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = template_web_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with template_web_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = template_web_client.DataProductsApi(api_client)
    connector_id = 'connector_id_example' # str | 
    data_product_id = 'data_product_id_example' # str | 

    try:
        # Delete Data Product
        api_response = api_instance.delete_data_product(connector_id, data_product_id)
        print("The response of DataProductsApi->delete_data_product:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->delete_data_product: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **connector_id** | **str**|  | 
 **data_product_id** | **str**|  | 

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
**200** | Data product deleted successfully |  -  |
**404** | Data product not found |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_data_product**
> object get_data_product(connector_id, data_product_id)

Get Data Product

Return metadata for a specific data product

### Example


```python
import template_web_client
from template_web_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = template_web_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with template_web_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = template_web_client.DataProductsApi(api_client)
    connector_id = 'connector_id_example' # str | 
    data_product_id = 'data_product_id_example' # str | 

    try:
        # Get Data Product
        api_response = api_instance.get_data_product(connector_id, data_product_id)
        print("The response of DataProductsApi->get_data_product:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->get_data_product: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **connector_id** | **str**|  | 
 **data_product_id** | **str**|  | 

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
**200** | Data product metadata |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_data_product_content**
> object get_data_product_content(connector_id, data_product_id)

Get Data Product Content

Retrieve data product content wrapped in MMIO

### Example


```python
import template_web_client
from template_web_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = template_web_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with template_web_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = template_web_client.DataProductsApi(api_client)
    connector_id = 'connector_id_example' # str | 
    data_product_id = 'data_product_id_example' # str | 

    try:
        # Get Data Product Content
        api_response = api_instance.get_data_product_content(connector_id, data_product_id)
        print("The response of DataProductsApi->get_data_product_content:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->get_data_product_content: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **connector_id** | **str**|  | 
 **data_product_id** | **str**|  | 

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
**200** | MMIO object with data product content |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_data_products**
> object list_data_products(page=page, page_size=page_size)

List Data Products

Return paginated list of available data products

### Example


```python
import template_web_client
from template_web_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = template_web_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with template_web_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = template_web_client.DataProductsApi(api_client)
    page = 1 # int |  (optional) (default to 1)
    page_size = 100 # int |  (optional) (default to 100)

    try:
        # List Data Products
        api_response = api_instance.list_data_products(page=page, page_size=page_size)
        print("The response of DataProductsApi->list_data_products:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DataProductsApi->list_data_products: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**|  | [optional] [default to 1]
 **page_size** | **int**|  | [optional] [default to 100]

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
**200** | List of data products |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

