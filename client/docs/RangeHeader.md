# RangeHeader

HTTP Range header for partial content requests

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------

## Example

```python
from ds_connector_service.models.range_header import RangeHeader

# TODO update the JSON string below
json = "{}"
# create an instance of RangeHeader from a JSON string
range_header_instance = RangeHeader.from_json(json)
# print the JSON string representation of the object
print RangeHeader.to_json()

# convert the object into a dict
range_header_dict = range_header_instance.to_dict()
# create an instance of RangeHeader from a dict
range_header_form_dict = range_header.from_dict(range_header_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


