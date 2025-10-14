# DataProductDistribution

Standardized metadata for resources across different sources

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**access_service** | **str** |  | [optional] 
**access_url** | **str** |  | [optional] 
**byte_size** | **int** |  | [optional] 
**compress_format** | **str** |  | [optional] 
**download_url** | **str** |  | [optional] 
**media_type** | **str** |  | [optional] 
**package_format** | **str** |  | [optional] 
**access_rights** | **str** |  | [optional] 
**conforms_to** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**format** | **str** |  | [optional] 
**issued** | **str** |  | [optional] 
**license** | **str** |  | [optional] 
**modified** | **str** |  | [optional] 
**rights** | **str** |  | [optional] 
**title** | **str** |  | [optional] 
**has_policy** | **str** |  | [optional] 
**checksum** | **str** |  | [optional] 

## Example

```python
from ds_connector_service.models.data_product_distribution import DataProductDistribution

# TODO update the JSON string below
json = "{}"
# create an instance of DataProductDistribution from a JSON string
data_product_distribution_instance = DataProductDistribution.from_json(json)
# print the JSON string representation of the object
print(DataProductDistribution.to_json())

# convert the object into a dict
data_product_distribution_dict = data_product_distribution_instance.to_dict()
# create an instance of DataProductDistribution from a dict
data_product_distribution_from_dict = DataProductDistribution.from_dict(data_product_distribution_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


