import {getResourceDatetimeAndValue} from "@/baseModel/searchSets";
// import FHIR from "fhirclient"

const getData = async (patient_id, model_name) => {
    // featureObj should be an object with model's feature set. E.g. diabetes
    let returnObj = {}

    await getResourceDatetimeAndValue(patient_id, model_name)
        .then(response => {
            for(const [key, valueObj] of Object.entries(response.data)){
                returnObj[key] = {}
                returnObj[key]["name"] = key
                returnObj[key]["take"] = valueObj['value'][0]
                returnObj[key]["date"] = valueObj['date'].reverse()
                returnObj[key]['value'] = valueObj['value'].reverse()
            }
        }).catch( e => console.log(e)
    )
    /* return object types with:
            {key: {'date': [], 'value': []}}

     */

    return returnObj

}




export {getData}