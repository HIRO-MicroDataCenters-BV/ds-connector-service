# DataProductDistribution

Standardized metadata for resources across different sources

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**access_service** | [**AccessService**](AccessService.md) |  | [optional] 
**access_url** | [**AccessUrl**](AccessUrl.md) |  | [optional] 
**byte_size** | [**ByteSize**](ByteSize.md) |  | [optional] 
**compress_format** | [**CompressFormat**](CompressFormat.md) |  | [optional] 
**download_url** | [**DownloadUrl**](DownloadUrl.md) |  | [optional] 
**media_type** | [**MediaType**](MediaType.md) |  | [optional] 
**package_format** | [**PackageFormat**](PackageFormat.md) |  | [optional] 
**access_rights** | [**AccessRights**](AccessRights.md) |  | [optional] 
**conforms_to** | [**ConformsTo**](ConformsTo.md) |  | [optional] 
**description** | [**Description**](Description.md) |  | [optional] 
**format** | [**Format**](Format.md) |  | [optional] 
**issued** | [**Issued**](Issued.md) |  | [optional] 
**license** | [**License**](License.md) |  | [optional] 
**modified** | [**Modified**](Modified.md) |  | [optional] 
**rights** | [**Rights**](Rights.md) |  | [optional] 
**title** | [**Title**](Title.md) |  | [optional] 
**has_policy** | [**HasPolicy**](HasPolicy.md) |  | [optional] 
**checksum** | [**Checksum**](Checksum.md) |  | [optional] 

## Example

```python
from ds_connector_service.models.data_product_distribution import DataProductDistribution

# TODO update the JSON string below
json = "{}"
# create an instance of DataProductDistribution from a JSON string
data_product_distribution_instance = DataProductDistribution.from_json(json)
# print the JSON string representation of the object
print DataProductDistribution.to_json()

# convert the object into a dict
data_product_distribution_dict = data_product_distribution_instance.to_dict()
# create an instance of DataProductDistribution from a dict
data_product_distribution_form_dict = data_product_distribution.from_dict(data_product_distribution_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


