import FHIR from 'fhirclient'

let server_url = 'http://ming-desktop.ddns.net:8192/fhir'

const getServerUrl = () => {
    return server_url;
}

const changeServerUrl = (serverUrl) => {
    server_url = serverUrl
}

const client = FHIR.client(
    {
        serverUrl: getServerUrl()
    }
)



/**
 * Abstract Class ResourceInterface
 *
 * @class ResourcesInterface
 */
class ResourcesInterface{
    constructor() {
        if(this.constructor === ResourcesInterface){
            throw new Error("ResourceInterface is an abstract class, concrete before used.")
        }
    }

    // eslint-disable-next-line no-unused-vars
    async search(patient_id, code) {
        throw new Error("Method 'search()' must be implemented.")
    }

    // eslint-disable-next-line no-unused-vars
    getDateTime(resourceList) {
        throw new Error("Method 'getDateTime() must be implemented.")
    }

    // eslint-disable-next-line no-unused-vars
    getValue(resourceObject) {
        throw new Error("Method 'getValue()' must be implemented.")
    }
}

/**
 * Observation
 *
 * @class Observation
 * @extends {ResourcesInterface}
 */
// eslint-disable-next-line no-unused-vars
class Observation extends ResourcesInterface {
    /////////////// Using promise
    async search(patient_id, code) {
        let url = encodeURI(`Observation?subject=${patient_id}&code=${code}&_sort=date`)
        let result = {}
        result = await client
            .request(url)
            .then(async response => {
                let resource = []
                if (response.total === 0) {
                    url = encodeURI(`Observation?subject=${patient_id}&component-code=${code}&_sort=date`)
                    await client
                        .request(url)
                        .then(response => {
                            if (response.total === 0)
                                return
                            response['entry'].forEach(value => {
                                resource.push(value['resource'])
                            })
                            result.response = resource
                            result.component = code
                        }).catch(() => console.log(url))
                } else{
                    response['entry'].forEach(value => {
                        resource.push(value['resource'])
                    })
                }
                if (result.resource === undefined)
                    result.resource = resource
                if (result.component === undefined)
                    result.component = null
                return result
            }).catch(error => console.log(error))

        return result

    }

    getValue(resourceObject) {
        let array = []
        if(resourceObject.component == null){
            resourceObject.resource.forEach(resource => {
                array.push(resource['valueQuantity']['value'])
            })
        } else {
            resourceObject.resource.forEach(resource => {
                let value
                resource['component'].forEach(component => {
                    component.code.coding.forEach(coding => {
                        if(coding.code === resourceObject['component'])
                            value = component['valueQuantity']['value']
                    })
                })
                array.push(value)
            })
        }
        return array
    }

    getDateTime(resourceList) {
        let array = []
        resourceList.forEach(resource => {
            // eslint-disable-next-line no-prototype-builtins
            array.push(resource.hasOwnProperty('effectiveDateTime') ? resource['effectiveDateTime'] : resource['effectivePeriod']['start'])
        })
        return array
    }

}

/**
 * Condition
 *
 * @class Condition
 * @extends ResourcesInterface
 */
// eslint-disable-next-line no-unused-vars
class Condition extends ResourcesInterface{
    // eslint-disable-next-line no-unused-vars
    async search(patient_id, code){
        return true
    }

    // eslint-disable-next-line no-unused-vars
    getValue(resourceObject) {
        let array = []
        array.push(true)
        return array
    }

    //eslint-disable-next-line no-unused-vars
    getDateTime(resourceList) {
        return ["2021-12-12"]
    }
}


class ResourceMgmt {

    constructor(resourceObject) {
        this._strategy = resourceObject
    }

    strategy(resourceObject){
        this._strategy = resourceObject
    }

    async getDataWithResources(patientId, featureObject) {
        if(this._strategy === undefined)
            return

        return await this._strategy.search(patientId, featureObject['code'])
    }

    getDateWithResources(resourceList) {
        if(this._strategy === undefined)
            return

        return this._strategy.getDateTime(resourceList)
    }

    getValueWithResources(resourceList) {
        if(this._strategy === undefined)
            return

        return this._strategy.getValue(resourceList)
    }
}

const getResourceDatetimeAndValue = async function (patient_id, featureObject) {
    const patient_resource_mgmt = new ResourceMgmt(eval(`new ${capitalize(featureObject['type_of_data'])}()`))

    return await patient_resource_mgmt.getDataWithResources(patient_id, featureObject)
        .then(response => {
            const resourceObject = response
            const resource_datetime = patient_resource_mgmt.getDateWithResources(resourceObject['resource'])
            const resource_value = patient_resource_mgmt.getValueWithResources(resourceObject)

            return {resource_value: resource_value, resource_datetime: resource_datetime}
        }).catch(e => console.log(e))
}

const capitalize = ((str) => {
    const lower = str.toLowerCase()
    return str.charAt(0).toUpperCase() + lower.slice(1)
});

export {getResourceDatetimeAndValue, changeServerUrl}