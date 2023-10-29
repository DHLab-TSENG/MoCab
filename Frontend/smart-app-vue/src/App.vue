<template>
  <img alt="Vue logo" src="./assets/mocab_icon.png">
  <!--  <HelloWorld msg="Welcome to Your Vue.js App"/>-->
  <div id="mainDiv">
    <div id="divChart">
      <div>
        <label for="since-time" style="font-size: 25px">Since Datetime: </label>
        <input
            style="font-size: 25px"
            id="setMinDateTime"
            v-model="minDate"
            name="since-time"
            type="datetime-local"
            @change="minDateChange"
        >
      </div>
      <div
          style="display: flex;justify-content: center"
          v-for="x in getFeatureArray"
          :key="x.name"
      >
        <div>
          <ModelChart
              v-if="x.name === type"
              :chartUsed="x.name"
              :title="x.name"
          >
          </ModelChart>
        </div>
      </div>
    </div>
    <div
        id="divModelSelect"
    >
      <h2
          v-if="!gettingModelScoreStatus"
      >
        Model Score: {{getCurrentModelObject.score}}
      </h2>
      <h2
        v-else-if="gettingModelScoreStatus"
      >
        Getting new model score...
      </h2>
      <select
          id="model-select"
          v-model="type"
          name="model"
      >
        <option
            v-for="x in getFeatureArray"
            :key="x.name"
            :value="x.name"
        >
          {{ x.name }}
        </option>
      </select>
    </div>
  </div>
</template>

<script>
import ModelChart from "@/components/ModelChart";
import {getData} from "@/baseModel/patientDataSearch";
import axios from "axios";

export default {
  name: 'App',
  components: {
    ModelChart
  },
  data() {
    return {
      minDate: new Date(),
      type: 'qcsi'
    }
  },
  methods: {
    // data is on ObjectType send by LineChartView.$emit
    minDateChange() {
      this.$store.commit('changeMinDate', this.minDate)
      this.$store.commit('changeModelChartUI')
    },
  },
  watch: {},
  computed: {
    getFeatureArray() {
      return this.$store.state.modelFeatureArray
    },
    getCurrentModelObject() {
      let obj = {}
      obj.score = 0
      for(const arr of this.$store.state.modelFeatureArray){
        if(arr.name === this.type)
          obj = arr
      }
      return obj
    },
    gettingModelScoreStatus() {
      return this.$store.state.modelScoreGettingStatus
    }
  }
  ,
  async created() {
    /**
     * modelFeatureArray: Array
     * Element of modelFeatureArray: featureCollectObject
     *
     * featureCollectObject: key: name, resources, score
     * name: string, model's name
     * resources: object, patient resources from FHIR Server
     * score: float, model's score
     */
    let modelFeatureArray = [] // Stores all feature
    let featureCollectObject

    let model_list = await axios({
      method: 'get',
      baseURL: this.$store.state.base,
      url: `/exist_model`,
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    })
        .then((result) => {
          return result.data['model']
        })
        .catch(error => console.log(error))

    let uri = window.location.search.substring(1);
    let params = new URLSearchParams(uri);
    if (params.has('id')) {
      this.$store.commit('changePatientId', params.get('id'))
    } else {
      console.log("patient_id is not in the parameter, using default patient 'test-03121002' instead. ")
    }


    for (const available_model of model_list) {
      featureCollectObject = {}
      featureCollectObject.name = available_model
      featureCollectObject.resources = await getData(this.$store.state.patient_id, available_model)
      featureCollectObject.score = 0
      modelFeatureArray.push(featureCollectObject)
    }
    console.log(modelFeatureArray)
    this.$store.commit('updateFeatureArray', modelFeatureArray)
  },
}
</script>

<style>
body{
  overflow: hidden;
}
img {
  height: 7vh;
  margin-right: 10px
}

h2 {
  font-size: 25px;
  text-align: left;
}

#app {
  height: 98vh;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  /*margin-top: 60px;*/
}

#mainDiv{
  height: 90vh;
  display: flex;
  justify-content: space-between;
}

#divChart {
  height: 85vh;
  width: 70vw;
  margin: 10px;
  /*overflow: overlay;*/
}

#divModelSelect{
  display: flex;
  flex-direction: column;
  width: 30vw;
}

#model-select {
  height: 4vmin;
  width: 50%;
  float: left;
  margin-bottom: 20px;
  font-size: 16px;
  font-weight:bold;
}
</style>
