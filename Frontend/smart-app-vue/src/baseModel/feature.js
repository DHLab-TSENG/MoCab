import features from "../assets/features.csv"

export const featureTable = {}

const special_field_sets = ['model', "feature", "code", "code_system"]

function FeatureTableSyntaxExceptions(message) {
    this.message = message
    this.name = "FeatureTableSyntaxExceptions"
}

function testCodeEmpty(code, featureName) {
    if(code == null){
        let message = featureName + "'s code is Empty"
        throw new FeatureTableSyntaxExceptions(message)
    }
}

features.forEach((obj) => {
    try{
        testCodeEmpty(obj['code'], obj['feature'])
    }catch (e) {
        console.log(e.name, e.message)
    }
    // eslint-disable-next-line no-prototype-builtins
    if(!featureTable.hasOwnProperty(obj['model']))
        featureTable[obj['model']] = {}

    // eslint-disable-next-line no-prototype-builtins
    if(!featureTable[obj['model']].hasOwnProperty(obj['feature']))
        featureTable[obj['model']][obj['feature']] = {}

    let code = obj['code']
    if(obj['code_system'] != null)
        code = `${obj['code_system']}|${obj['code']}`

    // check if 'code' key already exists in the feature
    // eslint-disable-next-line no-prototype-builtins
    if(!featureTable[obj['model']][obj['feature']].hasOwnProperty('code'))
        featureTable[obj['model']][obj['feature']]['code'] = code
    else
        featureTable[obj['model']][obj['feature']]['code'] =
            `${featureTable[obj['model']][obj['feature']]['code']},${code}`

    for(const [key, value] of Object.entries(obj)) {
        if(!special_field_sets.includes(key)){
            featureTable[obj['model']][obj['feature']][key] = value
        }
    }
})