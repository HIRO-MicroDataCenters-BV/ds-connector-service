# ds_connector_service.ContractsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**validate_contract**](ContractsApi.md#validate_contract) | **POST** /contracts/validate | Validate Contract


# **validate_contract**
> object validate_contract(body)

Validate Contract

Validate a contract before allowing access to data

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
    api_instance = ds_connector_service.ContractsApi(api_client)
    body = None # object | 

    try:
        # Validate Contract
        api_response = api_instance.validate_contract(body)
        print("The response of ContractsApi->validate_contract:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ContractsApi->validate_contract: %s\n" % e)
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
**200** | Contract is valid |  -  |
**403** | Invalid contract |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

