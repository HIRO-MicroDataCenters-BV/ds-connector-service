# ds_connector_service.HealthApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**health_check**](HealthApi.md#health_check) | **GET** /health-check/ | Health Check


# **health_check**
> object health_check()

Health Check

Check if the Connector service is running

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
    api_instance = ds_connector_service.HealthApi(api_client)

    try:
        # Health Check
        api_response = api_instance.health_check()
        print("The response of HealthApi->health_check:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling HealthApi->health_check: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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
**200** | Service is healthy |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

