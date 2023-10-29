<template>
  <div style="width: 32.92%;" v-if="!getChangeStatus">
    <div class="lineChartClass">
      <Line
          :chart-data="chartData"
          :chart-options="chartOptions"
      />
    </div>
    <div class="chartLabelClass">
      <label style="font-size: 22px">{{ title.replaceAll("_", " ") }}</label>
      <div
          class="divInputClass"
          v-if="featureObj[title]['type_of_data'] === 'observation' || featureObj[title]['type_of_data'] === 'patient'"
      >
        <input
            type="number"
            v-model.lazy="take"
        >
        <span style="margin-left:3px;font-size: 12px">{{ featureObj[title]['unit'] }}</span>
      </div>
      <div
          class="divInputClass"
          v-if="featureObj[title]['type_of_data'] === 'condition'"
      >
        <!--   Keep spaces for condition resources in search_type == "count"     -->
        <label style="padding-top: 3px"><input type="radio" v-model="take" :value="true">True</label>
        <label style="padding-top: 3px"><input type="radio" v-model="take" :value="false">False</label>
      </div>
    </div>
  </div>
</template>

<script>
import {Line} from 'vue-chartjs';
import {featureTable} from "@/baseModel/feature";
import 'chartjs-adapter-moment';
import {Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, LinearScale, TimeScale} from 'chart.js'

ChartJS.defaults.font.size = 10;
ChartJS.register(Title, Tooltip, Legend, LineElement, LinearScale, PointElement, TimeScale)
export default {
  name: "LineChart",
  components: {Line},
  props: {
    modelName: String,
    title: String,
    chartLabel: Array,
    chartPoint: Array,
  },
  data() {
    return {
      featureObj: featureTable[this.modelName],
      minDataSlice: 2,
      chartData: {
        labels: this.chartLabel.slice(this.minDataSlice),
        datasets: [
          {
            label: this.title.replaceAll("_", " "),
            fill: false,
            tension: 0.2,
            borderWidth: 3,
            borderColor: [
              'rgb(255, 159, 64)',
            ],
            pointBorderWidth: 5,
            data: this.chartPoint.slice(this.minDataSlice),
          }
        ]
      },
      chartOptions: {
        spanGaps: true,
        aspectRatio: 1.25,
        responsive: true,
        animation: false,
        plugins: {
          decimation: {
            threshold: 5
          },
          legend: {
            labels: {
              font: {
                size: 25
              }
            }
          },
          filler: {
            propagate: false
          },
          bodyAlign: 'center'
        },
        onClick: (e) => {
          try{
            this.take = e.chart.tooltip.dataPoints[0].raw
          }
          catch (e){
            this.take += 0
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'month' // TODO: May have to change unit if the time between maximum and minimum is under a month
            },
            max: this.$store.state.maxDate,
            min: this.$store.state.minDate,
            alignToPixels: true
          },
          y: {
            type: 'linear',
            max: Math.max(...this.chartPoint) + Math.max(...this.chartPoint)*0.1,
            min: Math.min(...this.chartPoint) - Math.min(...this.chartPoint)*0.1,
          }
        }
      },
      take: null,
    }
  },
  beforeCreate(){
    let count = 0

    this.chartLabel.forEach(dateElement => {
      let minDate = new Date(this.$store.state.minDate)
      let currentDate = new Date(dateElement)
      if(minDate.getTime() > currentDate.getTime()) {
        count++
      }
    })

    this.minDataSlice = count
  },
  mounted() {
    // eslint-disable-next-line vue/no-mutating-props
    this.take = this.$props.chartPoint[this.chartPoint.length - 1]
  },
  watch: {
    take(newValue) {
      this.$emit("takeChange", {
        "featureName": this.title,
        "featureValue": newValue
      })
    },
    getChangeStatus() {
      let count = 0

      this.chartLabel.forEach(dateElement => {
        let minDate = new Date(this.$store.state.minDate)
        let currentDate = new Date(dateElement)
        if(minDate.getTime() > currentDate.getTime()) {
          count++
        }
      })
      console.log(count)
      this.minDataSlice = 1
      this.chartOptions.scales.x.min = this.$store.state.minDate
    }
  },
  computed: {
    getChangeStatus() {
      return this.$store.state.dateChanged
    },
  }
}
</script>

<style scoped>
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
   display: none;
  -webkit-appearance: none;
}
input {
  margin-top: 5px;
  height: 15px;
}
input[type=number] {
  /*text-align: center;*/
  width: 4vw;
}

.lineChartClass {
  position: relative;
  margin: 15px
}

.chartLabelClass {
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: 100%;
  padding-bottom: 10px;
  border-bottom-style: dashed;
}

.divInputClass {
  height: 3.5vh
}

</style>