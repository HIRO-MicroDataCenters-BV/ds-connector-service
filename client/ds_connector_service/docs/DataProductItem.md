# DataProductItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**distribution** | [**List[DataProductDistribution]**](DataProductDistribution.md) |  | 
**region** | **str** |  | [optional] [default to '']

## Example

```python
from ds_connector_service.models.data_product_item import DataProductItem

# TODO update the JSON string below
json = "{}"
# create an instance of DataProductItem from a JSON string
data_product_item_instance = DataProductItem.from_json(json)
# print the JSON string representation of the object
print(DataProductItem.to_json())

# convert the object into a dict
data_product_item_dict = data_product_item_instance.to_dict()
# create an instance of DataProductItem from a dict
data_product_item_from_dict = DataProductItem.from_dict(data_product_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


