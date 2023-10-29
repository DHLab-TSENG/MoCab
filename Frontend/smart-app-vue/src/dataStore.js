import {createStore} from "vuex";
import axios from "axios";

const nowDate = new Date()

export const store = createStore({
    state () {
        return {
            modelFeatureArray: [],
            modelScoreGettingStatus: false, // while data changes, parameter will turn to true
            dateChanged: false,
            minDate: nowDate.setFullYear(nowDate.getFullYear() - 7),
            maxDate: new Date(),
            base: 'http://127.0.0.1:5050',
            base_prefix: 'smart',
            patient_id: "test-03121002",
        }
    },
    mutations: {
        changePatientId(state, id){
          state.patient_id = id
        },
        updateFeatureArray(state, modelArray) {
            state.modelFeatureArray = modelArray
        },
        changeMinDate(state, date) {
            state.minDate = Date.parse(date)
        },
        changeModelChartUI(state) {
            state.dateChanged = true
            setTimeout(function() {
                state.dateChanged = false
            }, 100)
        },
        changeModelScore(state, object){
            /**
             * object.key: index: array's index, score: result of model
             */
            state.modelFeatureArray[object.index].score = object.score
        },
        changeFeatureTake(state, valueObj){
            /**
             * valueObj.key: index: index of modelFeatureArray, featureName: this.title, featureValue: {changedValue}
             */
            const arrayIndex = valueObj.index
            const featureName = valueObj.featureName
            state.modelFeatureArray[arrayIndex].resources[featureName].take = valueObj.featureValue == 'true' ? true : valueObj.featureValue == 'false' ? false : valueObj.featureValue
        },
        gettingModelScore(state, statusBool){
            state.modelScoreGettingStatus = statusBool
        }
    },
    actions: {
        async getModelScore({commit}, arrayIndex){
            const modelFeatureObj = this.state.modelFeatureArray[arrayIndex]
            let featureObj = {}
            Object.entries(modelFeatureObj.resources).forEach(([key, valueObj]) => {
                featureObj[key] = {}
                featureObj[key].value = valueObj.take
            })
            axios({
                method: 'post',
                baseURL: this.state.base,
                url: `/${modelFeatureObj.name}/change`,
                data: featureObj,
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            })
                .then((result) => {
                    let obj = {}
                    obj.index = arrayIndex
                    let score = Number(result.data['predict_value']).toFixed(3)
                    // if the decimal are all in 0, parse it into integer
                    if (score % 1 === 0) {
                        score = parseInt(score)
                    }
                    obj.score = score
                    commit('changeModelScore', obj)
                })
                .catch(error => console.log(error))
        },
        async featureTakeChanged({dispatch, commit}, valueObj ){
            /**
             * valueObj.key: index: index of modelFeatureArray, featureName: this.title, featureValue: {changedValue}
             */

            commit('changeFeatureTake', valueObj) // 換掉數值
            commit('gettingModelScore', true)
            await dispatch('getModelScore', valueObj.index)

            setTimeout(() => {
                commit('gettingModelScore', false)
                }, 1000
            )
        }
    }
})
