import {getResourceDatetimeAndValue} from "@/baseModel/searchSets";

const getData = async (patient_id, featureObj) => {
    // featureObj should be an object with model's feature set. E.g. diabetes
    let returnObj = {}
    if(typeof(featureObj) != "object")
        return

    for (const [key, valueObj] of Object.entries(featureObj)) {
        // TODO: 在加入更多判斷之後，這行程式碼可以槓掉。目前只支援observation
        if(valueObj['type_of_data'].toLowerCase() === 'patient')
            continue;

        await getResourceDatetimeAndValue(patient_id, valueObj)
            .then(response => {
                returnObj[key] = {}
                returnObj[key].name = key
                returnObj[key].value = response.resource_value
                returnObj[key].date = response.resource_datetime
                returnObj[key].take = returnObj[key].value[returnObj[key].value.length - 1]
            }).catch( e => console.log(e)
        )
    }
    /* return object types with:
            {key: {'date': [], 'value': []}}

     */

    return returnObj

}




export {getData}