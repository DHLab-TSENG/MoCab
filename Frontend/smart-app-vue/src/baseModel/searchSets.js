import axios from "axios";
import {store} from '@/dataStore'

const getResourceDatetimeAndValue = async function (patient_id, model_name) {
    return axios({
        method: 'get',
        baseURL: store.state.base,
        url: `/${store.state.base_prefix}/${model_name}?id=${patient_id}`,
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }).then(response => {
        return response
    })
}

export {getResourceDatetimeAndValue}