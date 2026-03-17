# UploadResponse

Response model for upload operations

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Upload status message | 
**result** | [**Result**](Result.md) |  | [optional] 

## Example

```python
from ds_connector_service.models.upload_response import UploadResponse

# TODO update the JSON string below
json = "{}"
# create an instance of UploadResponse from a JSON string
upload_response_instance = UploadResponse.from_json(json)
# print the JSON string representation of the object
print UploadResponse.to_json()

# convert the object into a dict
upload_response_dict = upload_response_instance.to_dict()
# create an instance of UploadResponse from a dict
upload_response_form_dict = upload_response.from_dict(upload_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


