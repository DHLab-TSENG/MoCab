<template>
  <div v-if="!getChangeStatus">
    <div class="lineChartClass">
      <Line
          :chart-data="chartData"
          :chart-options="chartOptions"
      />
    </div>
    <div class="chartLabelClass">
      <label>{{ title + ": " }}</label>
      <input type="number" v-model.lazy="take">
    </div>
  </div>
</template>

<script>
import {Line} from 'vue-chartjs'
import 'chartjs-adapter-moment'
import {Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, LinearScale, TimeScale} from 'chart.js'

ChartJS.defaults.font.size = 13;
ChartJS.register(Title, Tooltip, Legend, LineElement, LinearScale, PointElement, TimeScale)
export default {
  name: "LineChart",
  components: {Line},
  props: {
    title: String,
    chartLabel: Array,
    chartPoint: Array,
  },
  data() {
    return {
      minDataSlice: 2,
      chartData: {
        labels: this.chartLabel.slice(this.minDataSlice),
        datasets: [
          {
            label: this.title,
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
                size: 14
              }
            }
          },
          filler: {
            propagate: false
          },
          bodyAlign: 'center'
        },
        onClick: (e) => {
          this.take = e.chart.tooltip.dataPoints[0].raw
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
    console.log(this.minDataSlice)
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
.lineChartClass {
  width: 40vw;
  position: relative;
  margin: 15px
}

.chartLabelClass {
  margin-bottom: 10px;
}

</style>